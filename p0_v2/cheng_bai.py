# -*- coding: utf-8 -*-
"""L4 格局成败判定字段（核A · 裁141甲 / 裁142否丙）

消费类型: COMPUTED —— 挂 ge_cheng.cheng_bai，下游一次读。
值域: CHENG / PO / CHENG_ZHONG_YOU_PO（三态，初版）
      PO_ZHONG_YOU_CHENG 依赖 C 块（救应），不落，标「依赖 C 块」。

依据:
  cheng_bai_criteria（§4.26.4，纯结构出口）
  ge_cheng.po_ge  24 处赋值语义全为 A「此盘此格已破」（§4.26.1 核验）
  ge_cheng.xi_wx_status  区分「破格后喜神被清空」vs「成中有败」

判定逻辑（纯结构，零新判据）:
  CHENG             po_n == 0
  CHENG_ZHONG_YOU_PO po_n > 0 且 xi_wx_status == "DEFINED"
                      （破格条件写入，但喜神仍定义 = 成中有败）
  PO                po_n > 0 且 xi_wx_status != "DEFINED"

★ 不读 ge 字符串（"(破格)" 后缀只有 43/1408 盘有，非可靠判据）。
★ 只读 po_n + xi_wx_status，两个字段同源 ge_cheng。
"""
from typing import Any, Dict, Optional


def compute_cheng_bai(ge_cheng: Optional[Dict[str, Any]]) -> Optional[str]:
    """从 ge_cheng 推 cheng_bai 判定。

    Args:
        ge_cheng: build_ge_cheng 产出的 dict，含 po_ge / xi_wx_status 键。

    Returns:
        "CHENG" / "CHENG_ZHONG_YOU_PO" / "PO" / None（无格）
    """
    if not ge_cheng or ge_cheng.get("ge") in (None, "无格", ""):
        return None

    po_ge = ge_cheng.get("po_ge") or []
    po_n = len(po_ge)
    xi_status = ge_cheng.get("xi_wx_status")

    if po_n == 0:
        return "CHENG"
    elif xi_status == "DEFINED":
        return "CHENG_ZHONG_YOU_PO"
    else:
        return "PO"


def build_cheng_bai(ge_cheng: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """落进 ge_cheng 的 dict 形态（含 basis 供人工核）。"""
    result = compute_cheng_bai(ge_cheng)
    po_n = len((ge_cheng or {}).get("po_ge") or [])
    xi_status = (ge_cheng or {}).get("xi_wx_status")
    return {
        "value": result,
        "status": "DEFINED" if result else "NO_GE",
        "basis": {
            "po_n": po_n,
            "xi_wx_status": xi_status,
            "slice_ids": "STRUCTURE.GE_JU.CHENG_BAI.001..012",
        },
        "po_zhong_you_cheng": "依赖 C 块（救应），不落",
    }


if __name__ == "__main__":
    # 探针（独立进程，不 import 引擎生产路径）
    print("=== cheng_bai 判定探针 ===")
    # 构造 4 个已知盘
    tests = [
        ("CHENG",               {"ge":"食神格","po_ge":[],"xi_wx_status":"DEFINED"}),
        ("PO",                  {"ge":"财格","po_ge":[{"type":"组合","match":"ANY","required":["七杀"]}] ,"xi_wx_status":None}),
        ("PO",                  {"ge":"从财格(破格)","po_ge":[{"type":"组合","match":"ANY","required":["比肩"]}],"xi_wx_status":"UNVERIFIED"}),
        ("CHENG_ZHONG_YOU_PO",  {"ge":"从财格","po_ge":[{"type":"组合","match":"ANY","required":["比肩"]}],"xi_wx_status":"DEFINED"}),
    ]
    all_pass = True
    for expect, gc in tests:
        r = build_cheng_bai(gc)
        ok = r["value"] == expect
        all_pass &= ok
        print("  预期=%-20s 实测=%-20s %s  basis=%s" % (
            expect, r["value"], "PASS" if ok else "FAIL", r["basis"]))
    r_none = build_cheng_bai(None)
    print("  ge=None -> value=None status=%s  %s" % (
        r_none["status"], "PASS" if r_none["status"]=="NO_GE" else "FAIL"))
    print("★ 探针:", "PASS" if all_pass else "FAIL")
    print("★ po_zhong_you_cheng:", build_cheng_bai(tests[0][1])["po_zhong_you_cheng"])
