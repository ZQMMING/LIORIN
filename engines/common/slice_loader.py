# -*- coding: utf-8 -*-
"""L1 切片加载器 slice_loader.py —— 生产侧 canonical 切片源

canonical 源: p0_v2/六部经典MD文库/  (942 条 MD 切片, 带 frontmatter + 原文 + 语义解析)
只读加载, 不做任何裁决。供 Matcher / 病药层 / 格局层消费切片条件时使用。

记录形态:
    {
      "slice_id":   "STRUCTURE.GE_JU.CHENG_BAI.001",
      "source":     "DTS 十二、八格",
      "version":    "京图撰刘基原注本",
      "line":       "行201",
      "category":   "STRUCTURE.GE_JU",
      "slice_type": "原则型",
      "authority":  "准" | "旁参" | "被DTS否决",
      "scope":      "全局" | ...,
      "verified":   "已校验" | ...,
      "original":   "原文(含原注)",
      "semantic":   {"对象":..,"关系":..,"条件":..,"结果":..},   # 自然语言, 待翻译器转三元组
      "path":       "相对路径",
    }
"""
import io
import os
import re
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLICE_LIB = os.path.join(ROOT, "p0_v2", "六部经典MD文库")

_CACHE: Dict[str, Dict[str, Any]] = {}
_INDEX: Optional[List[Dict[str, Any]]] = None


def _parse_slice(path: str) -> Dict[str, Any]:
    """解析单个 MD 切片文件 -> 记录。"""
    txt = io.open(path, encoding="utf-8", errors="replace").read()
    head = {}
    # frontmatter 行形态: > **切片ID**：xxx
    for m in re.finditer(r"^>\s*\*\*([^*]+)\*\*[：:]\s*(.+?)\s*$", txt, re.M):
        head[m.group(1).strip()] = m.group(2).strip()

    def _seg(tag: str) -> str:
        if tag not in txt:
            return ""
        parts = txt.split("## " + tag, 1)
        if len(parts) < 2:
            return ""
        nxt = parts[1].split("\n## ", 1)
        return nxt[0].strip()

    semantic = {}
    seg = _seg("语义解析")
    if seg:
        # 语义解析 段内行形态: **对象**：xxx / **关系**：xxx / **条件**：xxx / **结果**：xxx
        for m in re.finditer(r"\*\*([^*]+)\*\*[：:]\s*(.+)", seg, re.M):
            semantic[m.group(1).strip()] = m.group(2).strip()

    rec = {
        "slice_id": head.get("切片ID", ""),
        "source": head.get("来源", ""),
        "version": head.get("版本", ""),
        "line": head.get("页码/行号", ""),
        "category": head.get("G1-A Category", ""),
        "slice_type": head.get("切片类型", ""),
        "authority": head.get("准神归属", ""),
        "scope": head.get("适用范围", ""),
        "verified": head.get("校验状态", ""),
        "original": _seg("原文"),
        "semantic": semantic,
        "path": os.path.relpath(path, SLICE_LIB).replace("\\", "/"),
    }
    return rec


def load_slices(subdir: str = "") -> List[Dict[str, Any]]:
    """加载全部切片(或某子目录)。带缓存。"""
    global _INDEX
    base = os.path.join(SLICE_LIB, subdir) if subdir else SLICE_LIB
    if not os.path.isdir(base):
        raise FileNotFoundError("切片文库不存在: %s" % base)
    out = []
    for root, _dirs, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn.startswith("_") or ".bak." in fn:
                continue
            p = os.path.join(root, fn)
            key = os.path.abspath(p)
            if key not in _CACHE:
                _CACHE[key] = _parse_slice(p)
            out.append(_CACHE[key])
    if subdir:
        return out
    _INDEX = out
    return out


def count() -> int:
    return len(load_slices())


def get_slice(slice_id: str) -> Optional[Dict[str, Any]]:
    """按切片ID精确取。"""
    for s in load_slices():
        if s["slice_id"] == slice_id:
            return s
    return None


def find_slices(kw: str) -> List[Dict[str, Any]]:
    """按关键词搜: 切片ID / 来源 / 原文 / 语义解析文本。"""
    kw = str(kw).strip()
    if not kw:
        return []
    hit = []
    for s in load_slices():
        hay = " ".join([
            s["slice_id"], s["source"], s["original"], s["scope"],
            " ".join(s["semantic"].values()),
        ])
        if kw in hay:
            hit.append(s)
    return hit


def by_authority(authority: str) -> List[Dict[str, Any]]:
    """按准神归属过滤: 准 / 旁参 / 被DTS否决。"""
    return [s for s in load_slices() if s["authority"] == authority]


if __name__ == "__main__":
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    n = count()
    print("切片总数 = %d" % n)
    print("准神归属分布:")
    from collections import Counter
    c = Counter(s["authority"] for s in load_slices())
    for k, v in c.most_common():
        print("  %-10s %d" % (k or "(空)", v))
    s = get_slice("STRUCTURE.GE_JU.CHENG_BAI.001")
    if s:
        print("抽查:", s["slice_id"], "|", s["source"], "| 条件=", str(s["semantic"].get("条件"))[:80])
