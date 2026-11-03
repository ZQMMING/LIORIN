# -*- coding: utf-8 -*-
"""PATCH-023C Conflict Namespace Registry（冲突命名空间注册表）
- concept_registry：同词不同义（strength/旺/强/用/病/清/浊）按经典拆分
- Rule Matcher 前置校验：Rule 的 input 必须带经典 namespace 前缀，裸 surface REJECT
- QTBJ 数据流检查：consumer→读取请求→registry→allowed/forbidden（不检查命盘对象是否存在）
- 防止跨领域串规则
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONCEPTS = {
    "strength": {
        "DTS": {"name": "strength_relation", "type": "trend", "allowed_states": ["trend_state", "support_relation", "control_relation", "drain_relation", "root_relation", "order_state"], "forbidden_states": ["strength_state 直判"]},
        "PZZQ": {"name": "strength_condition", "type": "structure", "allowed_states": ["order_state", "month_order", "ten_god_relation", "structure_relation", "root_relation"], "forbidden_states": ["强弱评分"]},
        "QTBJ": {"name": "climate_condition", "type": "climate", "allowed_states": ["seasonal_state", "month_order", "daymaster", "climate_relation"], "forbidden_states": ["strength_state", "wang_state", "qiang_state"]},
    },
    "wang": {
        "DTS": {"name": "wang_relation", "type": "relation_state", "allowed_states": ["trend_state", "support_relation", "control_relation", "drain_relation"]},
        "YHZP": {"name": "wang_expression", "type": "expression_state", "allowed_states": ["ten_god_relation", "element_relation", "root_relation", "season_relation"]},
        "QTBJ": {"forbidden": ["wang_state"]},
    },
    "qiang": {
        "PZZQ": {"name": "strength_condition", "type": "structure", "allowed_states": ["order_state", "month_order", "ten_god_relation", "structure_relation", "root_relation"]},
        "DTS": {"name": "strength_relation", "type": "trend", "allowed_states": ["trend_state", "support_relation", "control_relation", "drain_relation", "root_relation", "order_state"]},
    },
    "用": {
        "PZZQ": {"name": "use_god", "type": "pattern", "allowed_states": ["order_state", "month_order", "ten_god_relation", "structure_relation"]},
        "SFTK": {"name": "qu_yong", "type": "diagnosis", "allowed_states": ["problem_relation", "support_relation", "control_relation", "structure_relation"]},
        "QTBJ": {"name": "climate_use", "type": "climate", "allowed_states": ["seasonal_state", "month_order", "daymaster", "climate_relation"]},
    },
    "病": {
        "SFTK": {"name": "problem", "type": "diagnosis", "allowed_states": ["problem_relation", "support_relation", "control_relation", "structure_relation"]},
        "DTS": {"name": "problem_concept", "type": "concept", "allowed_states": ["trend_state", "support_relation", "control_relation", "drain_relation"]},
    },
    "清": {
        "PZZQ": {"name": "qing_za", "type": "selection", "meaning": "取用神层面纯杂", "allowed_states": ["order_state", "month_order", "ten_god_relation", "structure_relation"]},
        "DTS": {"name": "qing_zhuo", "type": "pattern", "meaning": "气象/格局层面清浊", "allowed_states": ["trend_state", "support_relation", "control_relation", "drain_relation", "root_relation"]},
    },
    "浊": {
        "PZZQ": {"name": "qing_za", "type": "selection"},
        "DTS": {"name": "qing_zhuo", "type": "pattern"},
    },
}

# 1983-11-03 命局状态快照（state_producer 产出）
CHART = {
    "order_state": "NOT_GET_ORDER", "month_order": "戌", "daymaster": "乙木",
    "ten_god_relation": "偏印正印比肩正印", "root_relation": "WEAK_ROOT(亥甲+未乙)",
    "support_relation": "SUPPORT_PRESENT(水透三)", "control_relation": "CONTROL_PRESENT(戌辛)",
    "drain_relation": "DRAIN_PRESENT(午丁泄/戌未土耗)", "trend_state": "PENDING",
    "seasonal_state": "QTBJ_REQUIRED", "climate_relation": "UNDETERMINED",
    "element_relation": "WATER_VISIBLE_SUPPORT+ROOTED_SUPPORT", "season_relation": "戌月",
    "problem_relation": "UNDETERMINED", "structure_relation": "UNDETERMINED",
    "time_object": "1983-11-03 11:30", "luck_cycle": "未启动", "year_cycle": "未启动",
    "strength_state": "UNDETERMINED", "wang_state": "UNKNOWN", "qiang_state": "UNKNOWN",
}

KEYMAP = {"order_state": "order_state", "month_order": "month_order", "daymaster": "daymaster",
          "ten_god_relation": "ten_god_relation", "root_relation": "root_relation",
          "support_relation": "support_relation", "control_relation": "control_relation",
          "drain_relation": "drain_relation", "trend_state": "trend_state",
          "seasonal_state": "seasonal_state", "climate_relation": "climate_relation",
          "element_relation": "element_relation", "season_relation": "season_relation",
          "problem_relation": "problem_relation", "structure_relation": "structure_relation",
          "time_object": "time_object", "luck_cycle": "luck_cycle", "year_cycle": "year_cycle"}


def resolve(scope, surface):
    """按经典解析 surface 概念 → namespaced 定义；无该经典定义则 REJECT"""
    if surface not in CONCEPTS:
        return None, "REJECT: surface 不在 registry"
    entry = CONCEPTS[surface].get(scope)
    if entry is None:
        return None, f"REJECT: {surface} 无 {scope} 定义（该经典未获授权消费此概念）"
    return entry, None


def validate_rule_inputs(rule_id, inputs):
    """Rule Matcher 前置校验：input 必须带 scope 前缀（如 DTS.strength_relation，按 namespaced name 反查）"""
    ok, bad = [], []
    for item in inputs:
        if "." in item:
            scope, name = item.split(".", 1)
            found = None
            for surface, scopes in CONCEPTS.items():
                e = scopes.get(scope)
                if e and e.get("name") == name:
                    found = (surface, e)
                    break
            if found is None:
                bad.append((item, "REJECT: namespace 无此定义"))
            else:
                ok.append(item)
        else:
            bad.append((item, "REJECT: 裸 surface 未带经典 namespace 前缀"))
    return ok, bad


if __name__ == "__main__":
    print("==== PATCH-023C Conflict Namespace Registry ====")
    print("\n==== 概念拆分 ====")
    for surface, scopes in CONCEPTS.items():
        names = ", ".join(f"{s}.{v['name']}" for s, v in scopes.items() if "name" in v)
        forb = ", ".join(f"{s}(forbidden:{','.join(v['forbidden'])})" for s, v in scopes.items() if "forbidden" in v and "name" not in v)
        print(f"  {surface}: {names}{'；' + forb if forb else ''}")

    print("\n==== 1983-1103 namespace 解析 ====")
    for scope, surface in [("DTS", "strength"), ("PZZQ", "strength"), ("QTBJ", "strength")]:
        entry, err = resolve(scope, surface)
        if err:
            print(f"  {scope}.{surface}: {err}")
            continue
        view = {s: CHART.get(KEYMAP.get(s, s), "N/A") for s in entry.get("allowed_states", [])}
        forb = [f for f in entry.get("forbidden_states", []) if f in CHART]
        print(f"  {scope}.{surface} [{entry['type']}]: allowed={json.dumps(view, ensure_ascii=False)}")
        print(f"      forbidden(未消费): {forb if forb else '无'}")

    print("\n==== Rule Matcher 前置校验 ====")
    good_rules = [("R1", ["DTS.strength_relation", "PZZQ.strength_condition"]),
                  ("R2", ["QTBJ.climate_condition"])]
    bad_rules = [("R3", ["strength"]), ("R4", ["water_many"]), ("R5", ["印多"])]
    for rid, ins in good_rules + bad_rules:
        ok, bad = validate_rule_inputs(rid, ins)
        print(f"  {rid}: inputs={ins} → ok={ok} bad={bad}")

    print("\n==== 全局禁令 ====")
    print("  水三透=身强 → REJECT（现象→结论未过 namespace 推理链）")
    print("  乙木戌月=乙木弱 → REJECT（QTBJ 禁读 strength/wang/qiang）")
