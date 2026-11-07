"""p0 线证据索引 — p0_v2《六部经典 MD 文库》切片 → V13 evidence id。

背景 (2026-11-07 用户裁决):
    子平引擎最终版本 = `D:\\shuntian-ziping-p0`（engines p0 线）。
    该引擎的证据锚是 `p0_v2/六部经典MD文库` 的切片 ID（如
    `STRUCTURE.GE_JU.CHENG_BAI.001`），与 `data/evidence/E-ZPZ-*` 不是同一命名空间。
    生产 G1 证据闸要求 claim 的 evidence_refs 能在已登记集合中解析，因此这里把
    切片 ID 登记为证据 ID —— 切片文件本身带原典原文与来源，可回溯。

原则:
    - 只登记真实存在的切片（不造 ID）。
    - 只读，不写 p0_v2。
    - 索引缓存（lru_cache），重复调用零开销。
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
SLICE_ROOT = _REPO_ROOT / "p0_v2" / "六部经典MD文库"

_SLICE_ID_RE = re.compile(r"\*\*切片ID\*\*[:：]\s*([^\s]+)")
_BOOK_RE = re.compile(r"\*\*来源\*\*[:：]\s*《([^》]+)》")
_STATUS_RE = re.compile(r"\*\*校验状态\*\*[:：]\s*([^\n]+)")
_ORIGINAL_RE = re.compile(r"##\s*原文\s*\n(.*?)(?:\n---|\Z)", re.S)


def _parse_slice(path: Path) -> Optional[Dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = _SLICE_ID_RE.search(text)
    if not match:
        return None
    book = _BOOK_RE.search(text)
    status = _STATUS_RE.search(text)
    original = _ORIGINAL_RE.search(text)
    return {
        "slice_id": match.group(1).strip(),
        "book": book.group(1).strip() if book else "",
        "status": status.group(1).strip() if status else "",
        "source_text": (original.group(1).strip() if original else ""),
        "path": str(path),
    }


@lru_cache(maxsize=1)
def slice_index() -> Dict[str, Dict[str, str]]:
    """切片 ID → 切片证据元数据。缺目录时返回空索引（不报错）。"""
    index: Dict[str, Dict[str, str]] = {}
    if not SLICE_ROOT.exists():
        return index
    for path in SLICE_ROOT.rglob("*.md"):
        meta = _parse_slice(path)
        if meta:
            index[meta["slice_id"]] = meta
    return index


def slice_ids() -> frozenset:
    """全部可登记为证据的切片 ID。"""
    return frozenset(slice_index().keys())


def lookup(slice_id: str) -> Optional[Dict[str, str]]:
    """取单个切片的证据元数据；不存在返回 None（不造数据）。"""
    return slice_index().get(slice_id)


def normalize(ref: str) -> str:
    """p0 引擎引用的证据码 → 切片 ID。

    引擎侧证据码形如 `DTS PATHOLOGY_QI_HOU.008`（书名 + 篇码），
    切片 ID 形如 `PATHOLOGY.QI_HOU.008`。逐级尝试：
    去书名前缀 → 前缀下划线转点 → 唯一后缀匹配。均失败返回 ""（不造 ID）。
    """
    index = slice_index()
    ref = (ref or "").strip()
    if not ref:
        return ""
    if ref in index:
        return ref
    body = ref.split(" ", 1)[1] if " " in ref else ref
    candidates = {body, body.replace("_", ".")}
    # 逐位置把下划线转点（`PATHOLOGY_QI_HOU.008` → `PATHOLOGY.QI_HOU.008`）
    for i, ch in enumerate(body):
        if ch == "_":
            candidates.add(body[:i].replace("_", ".") + "." + body[i + 1:])
    for cand in candidates:
        if cand in index:
            return cand
    tail = body
    hits = [k for k in index if k.endswith("." + tail) or k == tail]
    if len(hits) == 1:
        return hits[0]
    hits = [k for k in index if k.endswith("." + tail.split(".", 1)[-1])]
    return hits[0] if len(hits) == 1 else ""


def resolve(refs: Optional[list]) -> list:
    """过滤出真实存在的切片引用，保序去重（含证据码归一化）。"""
    index = slice_index()
    seen = set()
    out = []
    for ref in refs or []:
        if not isinstance(ref, str):
            continue
        rid = ref.strip()
        if rid not in index:
            rid = normalize(rid)
        if rid and rid in index and rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out
