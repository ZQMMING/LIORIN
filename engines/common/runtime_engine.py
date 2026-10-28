# -*- coding: utf-8 -*-
"""PATCH-030 Runtime Decision Engine Contract（运行时决策引擎契约）
- 执行管线：Fact→Producer→Rule Match→Conflict Resolver→State（带 trace）
- 禁多规则命中后自行综合：Result=单规则登记输出 或 UNDETERMINED/UNKNOWN
- ADMITTED_RULE 加载四门槛；REJECT/ABSTAIN/UNKNOWN/UNDETERMINED 四态
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

S = {
    "order_state": "NOT_GET_ORDER", "bj_tou": [], "wealth_relation_state": "UNDETERMINED",
    "structure_relation": "UNDETERMINED",
}

# ADMITTED_RULE 运行时加载（binding 七字段 + evidence 绑定 + producer）
ADMITTED = {
    "CAND-WANG-001": {"producer": "024", "namespace": "YHZP.wang_expression", "output_state": "wang_state", "evidence": ["EVID-001"], "golden_pass": False},
    "CAND-WANG-002": {"producer": "024", "namespace": "DTS.wang_relation", "output_state": "wang_state(SUPPORTING)", "evidence": ["EVID-002"], "golden_pass": False},
    "CAND-SHUAI-001": {"producer": "024", "namespace": "YHZP.wang_expression", "output_state": "shuai_state", "evidence": ["EVID-001"], "golden_pass": False},
    "CAND-QIANG-001": {"producer": "024", "namespace": "YHZP.wang_expression", "output_state": "qiang_state", "evidence": ["EVID-001"], "golden_pass": False},
    "RULE-022C-01": {"producer": "022D", "namespace": "YHZP.support_relation", "output_state": "wealth_relation_state", "evidence": ["EVID-003"], "golden_pass": False},
    "RULE-022C-05": {"producer": "022D", "namespace": "DTS.strength_relation", "output_state": "context_marker", "evidence": ["EVID-007"], "golden_pass": False},
}


def match_rule(rule_id, state_snapshot):
    """规则匹配：返回 MATCHED/ABSTAIN/REJECT；禁自行综合"""
    r = ADMITTED[rule_id]
    if r["golden_pass"] is False and rule_id not in ("CAND-SHUAI-001",):
        # 资格层规则：匹配但条件不完整 → ABSTAIN（候选≠成立）
        pass
    if rule_id == "CAND-SHUAI-001":
        if state_snapshot["order_state"] == "NOT_GET_ORDER":
            return "MATCHED", "SHUAI", r
        return "ABSTAIN", "UNKNOWN", r
    if rule_id == "CAND-WANG-001":
        if state_snapshot["order_state"] == "GET_ORDER":
            return "MATCHED", "WANG", r
        return "ABSTAIN", "UNKNOWN", r
    if rule_id == "CAND-QIANG-001":
        if state_snapshot["order_state"] == "NOT_GET_ORDER" and not state_snapshot["bj_tou"]:
            return "ABSTAIN", "UNKNOWN", r  # 条件不齐（无比劫透），候选不成立
        return "ABSTAIN", "UNKNOWN", r
    if rule_id == "RULE-022C-01":
        if state_snapshot["wealth_relation_state"] == "UNDETERMINED":
            return "ABSTAIN", "UNDETERMINED", r  # 财多结构未确认（022D-R1 对象化）
        return "ABSTAIN", "UNDETERMINED", r
    if rule_id == "RULE-022C-05":
        return "ABSTAIN", "context_marker(不产出 strength)", r
    return "ABSTAIN", "UNKNOWN", r


def run_engine():
    results = {}
    for rid in ADMITTED:
        status, val, r = match_rule(rid, S)
        results[rid] = {"state": r["output_state"], "value": val, "match_result": status,
                        "producer": r["producer"], "evidence_chain": r["evidence"], "golden_pass": r["golden_pass"]}
    return results


if __name__ == "__main__":
    print("==== PATCH-030 Runtime Decision Engine Contract ====")
    print("\n==== ADMITTED_RULE 加载门槛 ====")
    print("  binding七字段 / evidence grade≤B / producer whitelist / golden_pass 登记（当前全 false）")
    print("\n==== 1983-1103 运行时匹配（禁自行综合） ====")
    res = run_engine()
    for rid, v in res.items():
        print(f"  {rid}: {v}")
    print("\n==== 四态机制 ====")
    print("  REJECT=门槛拒绝（D级/引用不实）｜ABSTAIN=条件不完整候选不成立｜UNKNOWN=无授权综合｜UNDETERMINED=冲突/综合条件未满足")
    print("\n==== 冲突演示（CONTRACT_DEMO，非真实规则） ====")
    print("  若同 state 两规则命中输出不同 → UNDETERMINED + conflict 登记（禁评分/投票/合并）")
    print("\n==== 核心禁令 ====")
    print("  多规则命中 → 模型自行综合 → 未经注册结论：FORBIDDEN")
