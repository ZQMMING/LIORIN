# -*- coding: utf-8 -*-
"""OCR 疑义**多维取证**工具（2026-10-24）。

为什么有这个工具
----------------
底本是 **OCR 文本**：同一句在不同底本里的异文，是判定「哪一字是 OCR 讹」的最硬证据
—— 若另一底本该处**没有讹**，则此处即 OCR 讹；若各底本**同讹**，则须上影印/互联网。

三条取证通道（按成本从低到高，能用低的就不上高的）：
  ① **多底本异文对照**（本工具，默认）—— K3-448 / K3-447 / K3-449 / 续修四库本 /
     崇祯刻本识典，同一句的异体形态；
  ② **影印原件**（`河洛理数_藏书阁K3-448_1632_OCR/*.png`）—— 逐页目视核定；
  ③ **互联网多源**（公开影印/点校本、人名史实、术语考据）—— 本地定不了时的兜底。

用法
----
    # 列出全部底本里与给定关键词相近的行（异文对照）
    python tools/heluo/verify_ocr_doubt.py --find "康節" --find "堯夫"

    # 按行号取证：给出某底本某行的「疑字」在各底本的对应形态
    python tools/heluo/verify_ocr_doubt.py --line K3-447:266 --ctx 3

    # 对一组疑字，报告每个底本里的命中与异文
    python tools/heluo/verify_ocr_doubt.py --doubt "候野定局" --doubt "世界應月卦"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE = Path(r"D:\顺天系统资料\河洛理数_OCR\修正版")
SOURCES: dict[str, Path] = {
    "K3-448": BASE / "河洛理数_1632笔写本_K3-448_修正版.txt",
    "K3-447": BASE / "河洛理数_1871增补本_K3-447_修正版.txt",
    "K3-449": BASE / "河洛数_缩略本_K3-449_修正版.txt",
    "四库": BASE / "河洛真数_续修四库全书本_文本.txt",
}
#: 崇祯刻本识典（另一书，供通用词取证）
SONGZHEN = Path(r"D:\顺天系统资料\河洛理数_OCR\参评秘诀对照\崇祯五年刻本_卷六_识典整理.txt")

#: 影印 PNG 根（仅 K3-448 有逐页影像）
SHADOW_ROOT = Path(r"D:\顺天系统资料\河洛理数_藏书阁K3-448_1632_OCR")


def _norm(s: str) -> str:
    """归一化：去空白与常见异体标点，便于跨底本比对。"""
    return re.sub(r"[\s　。，、；：？！「」『』（）()《》〈〉·・‧\-—…\.]+", "", s)


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def cmd_find(args) -> int:
    """在全部底本中检索关键词，列出**各底本的异文形态**。"""
    for kw in args.find:
        print(f"\n{'=' * 70}\n检索：{kw!r}\n{'=' * 70}")
        nk = _norm(kw)
        for tag, path in SOURCES.items():
            if not path.exists():
                continue
            hits = []
            for i, line in enumerate(_read(path), 1):
                if _norm(kw) and _norm(kw) in _norm(line):
                    hits.append((i, line.strip()))
            if not hits:
                continue
            print(f"  ── {tag}（{path.name}）：{len(hits)} 处")
            for i, line in hits[:args.limit]:
                print(f"     L{i}: {line[:150]}")
    if SONGZHEN.exists():
        hits = [(i, l.strip()) for i, l in enumerate(_read(SONGZHEN), 1)
                if kw and _norm(kw) in _norm(l)]
        if hits:
            print(f"  ── 崇祯刻本识典：{len(hits)} 处")
            for i, line in hits[:args.limit]:
                print(f"     L{i}: {line[:150]}")
    return 0


def cmd_line(args) -> int:
    """按「底本:行号」取证：打印该行上下文，并在其他底本找**同句异文**。"""
    tag, _, lineno = args.line.partition(":")
    lineno = int(lineno)
    path = SOURCES.get(tag)
    if path is None:
        print(f"✘ 未知底本 {tag}；可选：{list(SOURCES)}")
        return 1
    lines = _read(path)
    lo, hi = max(1, lineno - args.ctx), min(len(lines), lineno + args.ctx)
    print(f"═══ {tag} L{lo}-L{hi}（{path.name}）═══")
    for i in range(lo, hi + 1):
        mark = " ▶" if i == lineno else "  "
        print(f"{mark} L{i}: {lines[i - 1].strip()[:170]}")

    # 同句异文：取该行里较长的片段（去掉标点）去别的底本找
    seg = _norm(lines[lineno - 1])
    if len(seg) < 4:
        seg = _norm(lines[max(1, lineno - 1) - 1])
    key = seg[:8] if len(seg) >= 8 else seg
    print(f"\n── 同句异文对照（片段 {key!r}）──")
    for t2, p2 in SOURCES.items():
        if t2 == tag or not p2.exists():
            continue
        found = [(i, l.strip()) for i, l in enumerate(_read(p2), 1)
                 if key and key in _norm(l)]
        if found:
            print(f"  {t2}:")
            for i, l in found[:args.limit]:
                print(f"     L{i}: {l[:150]}")
    return 0


def cmd_doubt(args) -> int:
    """对一组「疑字串」，报告每个底本的命中与异文（定字的第一手材料）。"""
    for d in args.doubt:
        print(f"\n{'=' * 70}\n疑字串：{d!r}\n{'=' * 70}")
        forms: dict[str, list[str]] = {}
        for tag, path in SOURCES.items():
            if not path.exists():
                continue
            for i, line in enumerate(_read(path), 1):
                s = line.strip()
                if not s:
                    continue
                if d in s or _norm(d) in _norm(s):
                    forms.setdefault(tag, []).append(f"L{i}: {s[:140]}")
        if not forms:
            print("  （各底本均无命中 ⇒ 疑字串本身可能有误）")
            continue
        for tag, rows in forms.items():
            print(f"  ── {tag}：{len(rows)} 处")
            for r in rows[:args.limit]:
                print(f"     {r}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="OCR 疑义多维取证")
    ap.add_argument("--find", action="append", default=[], help="关键词（全底本检索）")
    ap.add_argument("--line", help="底本:行号（取证该行 + 同句异文）")
    ap.add_argument("--doubt", action="append", default=[], help="疑字串（异文对照）")
    ap.add_argument("--ctx", type=int, default=2, help="--line 的上下文行数")
    ap.add_argument("--limit", type=int, default=8, help="每源最多显示多少条")
    args = ap.parse_args()
    if args.line:
        return cmd_line(args)
    if args.doubt:
        return cmd_doubt(args)
    if args.find:
        return cmd_find(args)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
