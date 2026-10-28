# -*- coding: utf-8 -*-
"""PATCH-023B Classical Domain Consumer Contract（经典域消费契约）
- 六经典各自允许读取哪些状态、禁止哪些输入
- consumer_mode：DIRECT / FACT_ONLY / DISPLAY_ONLY / SUPPORTING / FORBIDDEN
- concept_namespace：同一字段不同经典不是同一变量
- 只定义消费边界，不产生任何命理结论
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REGISTRY = [
    {"classical_scope": "PZZQ", "responsible": ["月令", "格局", "用神", "相神", "顺逆"],
     "allowed_input_states": ["order_state", "month_order", "ten_god_relation", "structure_relation", "root_relation"],
     "forbidden_inputs": ["strength_score", "percentage", "temperature_score", "shen_sha"],
     "consumer_mode": "DIRECT", "output_permission": ["pattern_state", "use_god_state"]},
    {"classical_scope": "DTS", "responsible": ["旺衰关系", "中和", "气势", "清浊", "病药概念"],
     "allowed_input_states": ["trend_state", "support_relation", "control_relation", "drain_relation", "root_relation", "order_state"],
     "forbidden_inputs": ["water_many", "element_score", "direct_strength_value"],
     "consumer_mode": "DIRECT", "output_permission": ["wang_state", "shuai_state"]},
    {"classical_scope": "QTBJ", "responsible": ["寒暖", "燥湿", "调候"],
     "allowed_input_states": ["seasonal_state", "month_order", "daymaster", "climate_relation"],
     "forbidden_inputs": ["strength_state", "wang_state", "qiang_state"],
     "consumer_mode": "DIRECT", "output_permission": ["seasonal_state", "climate_relation"],
     "note": "乙木戌月可看燥湿寒暖，不能直接判乙木弱"},
    {"classical_scope": "SFTK", "responsible": ["病药", "救应", "取用条件"],
     "allowed_input_states": ["problem_relation", "support_relation", "control_relation", "structure_relation"],
     "forbidden_inputs": ["PZZQ_useful", "DTS_strength"],
     "consumer_mode": "DIRECT", "output_permission": ["problem_state", "medicine_state"]},
    {"classical_scope": "YHZP", "responsible": ["基础十神", "干支", "五行关系", "部分旺衰表达"],
     "allowed_input_states": ["ten_god_relation", "element_relation", "root_relation", "season_relation"],
     "forbidden_inputs": ["现代评分模型"],
     "consumer_mode": "DIRECT", "output_permission": ["ten_god_state", "element_relation_state"]},
    {"classical_scope": "SMTH/五行精纪", "responsible": ["岁运", "起运", "时间体系"],
     "allowed_input_states": ["time_object", "luck_cycle", "year_cycle"],
     "forbidden_inputs": ["直接参与 strength_state"],
     "consumer_mode": "SUPPORTING", "output_permission": ["luck_cycle", "year_cycle"]},
]

CONSUMER_MODE = ["DIRECT", "FACT_ONLY", "DISPLAY_ONLY", "SUPPORTING", "FORBIDDEN"]

NAMESPACE = {
    "strength": ["DTS.strength_relation", "PZZQ.strength_condition", "QTBJ.climate_condition"],
    "旺": ["DTS.wang_relation", "YHZP.wang_expression"],
    "强": ["PZZQ.strength_condition", "DTS.strength_relation"],
    "用": ["PZZQ.use_god", "SFTK.qu_yong", "QTBJ.climate_use"],
    "病": ["SFTK.problem", "DTS.problem_concept"],
    "清": ["PZZQ.qing_za", "DTS.qing_zhuo"],
    "浊": ["PZZQ.qing_za", "DTS.qing_zhuo"],
}

# 1983-11-03 命局各层状态快照（由 state_producer 产出，此处直接登记消费视图）
CHART_STATE = {
    "order_state": "NOT_GET_ORDER", "month_order": "戌", "daymaster": "乙木",
    "ten_god_relation": {"年干": "偏印", "月干": "正印", "日干": "比肩", "时干": "正印"},
    "root_relation": "WEAK_ROOT(亥藏甲+未藏乙)",
    "support_relation": "SUPPORT_PRESENT(水透三：癸壬壬)",
    "control_relation": "CONTROL_PRESENT(戌藏辛制)",
    "drain_relation": "DRAIN_PRESENT(午丁泄/戌未土耗)",
    "trend_state": "PENDING",
    "seasonal_state": "QTBJ_REQUIRED",
    "climate_relation": "UNDETERMINED",
    "element_relation": "WATER_VISIBLE_SUPPORT+ROOTED_SUPPORT",
    "problem_relation": "UNDETERMINED",
    "structure_relation": "UNDETERMINED",
    "season_relation": "戌月",
    "time_object": "1983-11-03 11:30", "luck_cycle": "未启动", "year_cycle": "未启动",
    "wang_state": "UNKNOWN", "shuai_state": "SHUAI", "strength_state": "UNDETERMINED",
}

KEY_MAP = {
    "order_state": "order_state", "month_order": "month_order", "ten_god_relation": "ten_god_relation",
    "structure_relation": "structure_relation", "root_relation": "root_relation",
    "trend_state": "trend_state", "support_relation": "support_relation", "control_relation": "control_relation",
    "drain_relation": "drain_relation", "seasonal_state": "seasonal_state", "daymaster": "daymaster",
    "climate_relation": "climate_relation", "problem_relation": "problem_relation",
    "element_relation": "element_relation", "season_relation": "season_relation",
    "time_object": "time_object", "luck_cycle": "luck_cycle", "year_cycle": "year_cycle",
}

if __name__ == "__main__":
    print("==== PATCH-023B Classical Domain Consumer Contract ====")
    print("consumer_mode 等级:", CONSUMER_MODE)
    print("\n==== concept_namespace ====")
    for k, v in NAMESPACE.items():
        print(f"  {k}: {v}")
    print("\n==== 1983-11-03 六经典消费视图 ====")
    for entry in REGISTRY:
        scope = entry["classical_scope"]
        allowed = {s: CHART_STATE.get(KEY_MAP[s], "N/A") for s in entry["allowed_input_states"]}
        # 校验：allowed 与 forbidden 无交集（配置一致性）；forbidden 字段在命局中存在但未被本经典消费
        intersect = [f for f in entry["forbidden_inputs"] if f in entry["allowed_input_states"]]
        forbidden_not_consumed = [f for f in entry["forbidden_inputs"] if f in CHART_STATE and f not in entry["allowed_input_states"]]
        print(f"\n  [{scope}] mode={entry['consumer_mode']}")
        print(f"    allowed: {json.dumps(allowed, ensure_ascii=False)}")
        print(f"    配置校验: {'违规交集:' + str(intersect) if intersect else '无（allowed 与 forbidden 无交集）'}")
        print(f"    未消费的全局状态: {'无' if not forbidden_not_consumed else str(forbidden_not_consumed) + '（命局存在但本经典禁止读取）'}")
        print(f"    输出权限: {entry['output_permission']}")
    print("\n==== 全局禁令 ====")
    print("  任何经典不得：水三透=身强；乙木戌月=乙木弱；跨域直判")
