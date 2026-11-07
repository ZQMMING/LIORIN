# -*- coding: utf-8 -*-
"""L4 格局成败判定（六态）

消费类型: COMPUTED —— 由 ge_cheng（含 po_ge_hits）一次推。
值域:
  None(NO_GE)        ge 无 / 无格
  SPECIAL_PASS       特殊格（从/专旺/化）真成立, H=0
  SPECIAL_FAIL       特殊格假/破（H>0 或 ge 带破格）
  CHENG              普通格 H=0
  CHENG_ZHONG_YOU_PO 普通格 H>0 且 xi_wx 非空（成中有败, 喜神在）
  PO                 普通格 H>0 且 xi_wx 空（破, 喜神清空）

★ H = len(po_ge_hits)（求值器实际命中），不是 po_ge 模板条数。旧 len(po_ge) 逻辑作废。
★ H>0 权威判据读 xi_wx 列表空否（status 键缺失 ≠ 喜神空）。
设计: p0_v2/po_ge求值器三层设计.md。
"""
from typing import Any, Dict, Optional

_SPECIAL_KW = ("从", "化", "曲直", "炎上", "稼穑", "从革", "润下")


def compute_cheng_bai(ge_cheng: Optional[Dict[str, Any]]) -> Optional[str]:
    if not ge_cheng or ge_cheng.get("ge") in (None, "无格", ""):
        return None
    ge = ge_cheng.get("ge") or ""
    hits = ge_cheng.get("po_ge_hits")
    H = len(hits) if hits is not None else 0
    xi = ge_cheng.get("xi_wx") or []
    is_special = any(k in ge for k in _SPECIAL_KW)
    po_mark = "(破格)" in ge
    if is_special:
        return "SPECIAL_FAIL" if (H > 0 or po_mark) else "SPECIAL_PASS"
    if H == 0:
        return "CHENG"
    return "CHENG_ZHONG_YOU_PO" if xi else "PO"


def build_cheng_bai(ge_cheng: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    result = compute_cheng_bai(ge_cheng)
    hits = (ge_cheng or {}).get("po_ge_hits")
    return {
        "value": result,
        "status": "DEFINED" if result else "NO_GE",
        "basis": {
            "H": len(hits) if hits is not None else 0,
            "xi_wx_empty": len((ge_cheng or {}).get("xi_wx") or []) == 0,
            "slice_ids": "STRUCTURE.GE_JU.CHENG_BAI.001..012",
        },
    }


if __name__ == "__main__":
    print("=== cheng_bai 六态探针 ===")
    tests = [
        ("CHENG", {"ge": "食神格", "po_ge_hits": [], "xi_wx": ["火"]}),
        ("PO", {"ge": "财格", "po_ge_hits": [{"hit_type": "组合"}], "xi_wx": []}),
        ("CHENG_ZHONG_YOU_PO", {"ge": "财格", "po_ge_hits": [{"hit_type": "组合"}], "xi_wx": ["水"]}),
        ("SPECIAL_PASS", {"ge": "曲直格", "po_ge_hits": [], "xi_wx": []}),
        ("SPECIAL_FAIL", {"ge": "从财格(破格)", "po_ge_hits": [{"hit_type": "组合"}], "xi_wx": []}),
    ]
    all_pass = True
    for expect, gc in tests:
        r = build_cheng_bai(gc)
        ok = r["value"] == expect
        all_pass &= ok
        print("  预期=%-20s 实测=%-20s %s" % (expect, r["value"], "PASS" if ok else "FAIL"))
    print("  ge=None ->", build_cheng_bai(None)["status"])
    print("★ 探针:", "PASS" if all_pass else "FAIL")
