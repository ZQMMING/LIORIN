# -*- coding: utf-8 -*-
"""PATCH-027 Climate Production Contract（调候生产契约）
- climate_state 生产者：QTBJ.climate DIRECT + DTS.climate SUPPORTING
- 输入仅季节/月令/日主/寒暖/燥湿；禁 climate→strength/pattern、climate_use→use_god/qu_yong
- 输出带 climate_type/season_source/temperature_source/evidence_chain
- QTBJ-018-001 未升格前 FAIL_CLOSED
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

S = {
    "month_order": "戌", "daymaster": "乙木", "seasonal_state": "QTBJ_REQUIRED",
    "temperature_condition": "UNDETERMINED", "dryness_wetness": "UNDETERMINED",
    "strength_state": "UNDETERMINED", "pattern_state": "UNDETERMINED",
    "climate_use_state": "UNDETERMINED", "use_god_state": "UNDETERMINED", "qu_yong_state": "UNDETERMINED",
    # 事实层证据（禁自动转调候结论）
    "fact_water_visible": 3,
}

FORBIDDEN_PATHS = [
    ("climate_state", "strength_state", "寒暖≠旺衰"),
    ("climate_state", "pattern_state", "调候≠格局判定"),
    ("climate_use_state", "use_god_state", "调候用≠格局用"),
    ("climate_use_state", "qu_yong_state", "调候用≠病药取用"),
    ("climate_state", "climate_use_state", "调候状态不自动产生调候用神"),
]


def produce_climate():
    qtbj_rule_ready = False  # QTBJ-018-001 仍 CANDIDATE_RULE
    if not qtbj_rule_ready:
        value = "UNDETERMINED（QTBJ 调候规则未准入：QTBJ-018-001 仍 CANDIDATE_RULE，须升格核验或换 QTBJ-060-001/109-001）"
    return {
        "state": "climate_state",
        "value": value,
        "producer": "QTBJ.climate",
        "sources": ["QTBJ.climate(month_order/daymaster/seasonal_state/temperature_condition/dryness_wetness)"],
        "evidence_chain": ["QTBJ 十干逐月调候体系（规则未准入，FAIL_CLOSED）"],
        "namespace_source": {"QTBJ": "climate"},
        "climate_type": "UNKNOWN",
        "season_source": "戌月（寒露后霜降前）",
        "temperature_source": "UNDETERMINED（无量化依据，禁编数字阈值）",
        "fact_layer_note": f"水透三({S['fact_water_visible']})为寒湿事实证据，但禁自动转调候结论",
    }


if __name__ == "__main__":
    print("==== PATCH-027 Climate Production Contract ====")
    print("\n==== 禁止路径 ====")
    for frm, to, reason in FORBIDDEN_PATHS:
        print(f"  禁止: {frm} → {to}（{reason}）")
    print("\n==== 概念边界 ====")
    print("  寒暖≠旺衰；燥湿≠强弱；调候用≠格局用")
    print("\n==== 1983-1103 Climate Producer 输出 ====")
    print(json.dumps(produce_climate(), ensure_ascii=False, indent=1))
    print("\n==== 规则准入检查 ====")
    print("  QTBJ-018-001 CANDIDATE_RULE → 未升格 → climate_state FAIL_CLOSED ✓")
