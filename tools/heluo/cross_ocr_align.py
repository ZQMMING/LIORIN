# -*- coding: utf-8 -*-
"""两套独立 OCR 通道的**逐页异文对照**（内容锚点自动对齐，2026-10-24）。

为什么重要
----------
同一部书的**影印原件**只有一个 OCR 结果 ⇒ 某个字形读错时**无从发现**。
但本项目有**两条彼此独立的 OCR 通道**：

  ① **修正版 OCR**（``修正版/河洛理数_1632笔写本_K3-448_修正版.txt``）
     —— 整本连续文本，带 ``--- pNNN ---`` 页标；
  ② **藏书阁 OCR**（``藏书阁K3-448_1632_OCR/ocr_output/pNNNN.md``）
     —— **另一套 OCR 引擎**（Qianfan-OCR q8_0）的逐页文本，
     影像来源 ``sourcelibrary.org``（互联网同源）⇒ **兼作互联网通道**。

⇒ 同一页两个读数：**一致处**基本可信；**不一致处**才是需要**影印目视核定**的点。
   这把「逐页影印核定」从「全量目视」缩小为「只核不一致处」。

⚠ **页号不是同一套**（实测：修正版 p026 = 卷五卷首页，而藏书阁 p0036 = 成卦法段）
⇒ 故**不用页号对齐，改用内容锚点**：取修正版该页正文字符集，
   在藏书阁全部页里找相似度最高者 ⇒ 自动建立映射。

用法
----
    python tools/heluo/cross_ocr_align.py --lo 2878 --hi 3165 --diff-only
    python tools/heluo/cross_ocr_align.py --lo 2878 --hi 3165 --map-only
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

BASE = Path(r"D:\顺天系统资料\河洛理数_OCR\修正版")
SRC = BASE / "河洛理数_1632笔写本_K3-448_修正版.txt"
SHADOW_OCR = Path(
    r"D:\顺天系统资料\河洛理数_藏书阁K3-448_1632_OCR\ocr_output")

_STRIP = re.compile(r"[\s　。，、；：？！「」『』（）()《》〈〉·・‧\-—…\.#*]+")


def _norm(s: str) -> str:
    return _STRIP.sub("", s)


def _charmul(s: str) -> set[str]:
    return set(_norm(s))


def _sim(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def _split_by_page(lines: list[str]) -> dict[int, list[tuple[int, str]]]:
    pages: dict[int, list[tuple[int, str]]] = {}
    cur = 0
    for i, ln in enumerate(lines, start=1):
        m = re.match(r"^\s*---\s*p(\d+)\s*---\s*$", ln)
        if m:
            cur = int(m.group(1))
            continue
        pages.setdefault(cur, []).append((i, ln))
    return pages


def _shadow_pages() -> dict[int, str]:
    out: dict[int, str] = {}
    for p in sorted(SHADOW_OCR.glob("p*.md")):
        if p.name.endswith(".orig"):
            continue
        m = re.match(r"^p(\d+)\.md$", p.name)
        if not m:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        body = [ln for ln in txt.splitlines() if not ln.strip().startswith("#")]
        out[int(m.group(1))] = "\n".join(body)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="两套独立 OCR 通道逐页异文对照")
    ap.add_argument("--lo", type=int, required=True)
    ap.add_argument("--hi", type=int, required=True)
    ap.add_argument("--diff-only", action="store_true")
    ap.add_argument("--map-only", action="store_true")
    ap.add_argument("--thresh", type=float, default=0.70)
    args = ap.parse_args()

    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    pages = _split_by_page(lines)
    shadow = _shadow_pages()
    if not shadow:
        print("✘ 藏书阁 ocr_output 不可用")
        return 1

    # ── 页号对齐 ──────────────────────────────────────────────────
    # ⚠ 页号**是对齐的**（实测两处）：
    #   · 修正版 p026（K3-448 L2878「海浴鲤数卷之五」）↔ 影印 PNG p0026
    #     = 卷五卷首页（影印逐字为「海洛理數卷之五」）；
    #   · 修正版 p036（K3-448 L488/L491「其餘五交…一卦管六日…」）↔
    #     藏书阁 ocr_output p0036（同段「其餘五交變五卦一卦管六日…」）。
    # ⇒ 不再用「整页字符集相似度」做对齐（排布表页全是爻位串，该法失效）。
    mapping = {p: p for p in pages if p in shadow}

    if args.map_only:
        for page in sorted(mapping):
            print(f"  修正版 p{page:03d}  ↔  藏书阁 p{mapping[page]:04d}")
        print(f"\n共对齐 {len(mapping)} 页")
        return 0

    total = 0
    diff = 0
    for page in sorted(pages):
        rows = [(i, ln) for i, ln in pages[page]
                if args.lo <= i <= args.hi and ln.strip()]
        if not rows:
            continue
        sp = mapping.get(page)
        if sp is None:
            continue
        shtext = shadow[sp]
        sh_lines = [l for l in shtext.splitlines() if l.strip()]
        for i, ln in rows:
            total += 1
            s = _norm(ln)
            if s and s in _norm(shtext):
                continue
            best, score = "", 0.0
            for sl in sh_lines:
                sc = _sim(_charmul(ln), _charmul(sl))
                if sc > score:
                    best, score = sl, sc
            if score < args.thresh:
                diff += 1
                if not args.diff_only:
                    continue
                print(f"\n  ⚠ 修正版 p{page:03d} L{i}  ↔ 藏书阁 p{sp:04d}"
                      f"  相似度 {score:.2f}")
                print(f"     修正版 : {ln.strip()[:140]}")
                print(f"     藏书阁 : {best.strip()[:140]}")
    print(f"\n=== 对照完成：修正版 {args.lo}-{args.hi} 涉及 {len([p for p in pages if any(args.lo<=i<=args.hi for i,_ in pages[p])])} 页，"
          f"参与比对 {total} 行，相似度 < {args.thresh} 的「不一致」{diff} 行 ===")
    print("（不一致处 = 需影印目视核定的重点；一致处基本可信）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
