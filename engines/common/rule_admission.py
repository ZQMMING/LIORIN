# -*- coding: utf-8 -*-
"""PATCH-028 Rule Admission Layer（规则准入层）
- 规则状态机：DRAFT→CANDIDATE→ADMITTED/REJECTED（门槛）
- 绑定 schema 七字段：rule_id/classic_source/namespace/producer/input_contract/output_state/evidence_chain
- 禁止原文直链状态；必须 原文→规则解析→namespace→producer→state
- 12 条 ADMITTED 绑定完整性校验（不重新裁决）
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 019 registry 12 条 ADMITTED 的 028 绑定登记（基于已裁决 governance 文件推导，非新规则）
ADMITTED_BINDINGS = [
    {"rule_id": "CAND-WANG-001", "classic_source": "YHZP-138-001（得时俱为旺论，A）", "namespace": "YHZP.wang_expression", "producer": "024", "input_contract": "order_state==GET_ORDER", "output_state": "wang_state", "evidence_chain": ["YHZP-138-001"]},
    {"rule_id": "CAND-WANG-002", "classic_source": "DTS-016-002（旺中有衰者存，B1 原注）", "namespace": "DTS.wang_relation", "producer": "024", "input_contract": "SUPPORTING（辅助，不单独触发）", "output_state": "wang_state(辅助)", "evidence_chain": ["DTS-016-002"]},
    {"rule_id": "CAND-SHUAI-001", "classic_source": "YHZP-138-001（失令便作衰看，A）", "namespace": "YHZP.wang_expression", "producer": "024", "input_contract": "order_state==NOT_GET_ORDER", "output_state": "shuai_state", "evidence_chain": ["YHZP-138-001"]},
    {"rule_id": "CAND-QIANG-001", "classic_source": "YHZP-138-001（日干无气遇劫为强，A）", "namespace": "YHZP.wang_expression", "producer": "024", "input_contract": "日干无气 AND 天干比劫透", "output_state": "qiang_state", "evidence_chain": ["YHZP-138-001"]},
    {"rule_id": "RULE-022C-01", "classic_source": "YHZP-078-024（财多生官须身健/盗气自柔）", "namespace": "YHZP.support_relation", "producer": "022D", "input_contract": "wealth_relation_state 对象化（财多结构+日主关系）", "output_state": "wealth_relation_state（非 strength）", "evidence_chain": ["YHZP-078-024"]},
    {"rule_id": "RULE-022C-02", "classic_source": "YHZP-079-022（身强杀浅假杀为权）", "namespace": "YHZP.support_relation", "producer": "022D", "input_contract": "condition（身强系综合判断，非单因子）", "output_state": "authority_relation_state", "evidence_chain": ["YHZP-079-022"]},
    {"rule_id": "RULE-022C-03", "classic_source": "YHZP-076-104+109（杀旺运纯身旺→贵 vs 七杀全彰→贫）", "namespace": "YHZP.support_relation", "producer": "022D", "input_contract": "BY_CONDITION（双分支禁合并）", "output_state": "authority_relation_state", "evidence_chain": ["YHZP-076-104", "YHZP-076-109"]},
    {"rule_id": "RULE-022C-04", "classic_source": "YHZP-082-001（七杀格喜忌）", "namespace": "YHZP.support_relation", "producer": "022D", "input_contract": "pattern 域七杀格语境", "output_state": "authority_relation_state", "evidence_chain": ["YHZP-082-001"]},
    {"rule_id": "RULE-022C-05", "classic_source": "DTS-017-001/002（中和原则 A+B1）", "namespace": "DTS.strength_relation", "producer": "022D", "input_contract": "CONTEXT_PRINCIPLE（不得直接→NEUTRAL）", "output_state": "context_marker", "evidence_chain": ["DTS-017-001", "DTS-017-002"]},
    {"rule_id": "RULE-022C-06", "classic_source": "PZZQ-007-030（伤官财格双向）", "namespace": "PZZQ.strength_condition", "producer": "022D", "input_contract": "pattern 域双向条件", "output_state": "pattern_condition", "evidence_chain": ["PZZQ-007-030"]},
    {"rule_id": "RULE-022C-07", "classic_source": "PZZQ-007-028（煞食均根轻助身）", "namespace": "PZZQ.strength_condition", "producer": "022D", "input_contract": "root 对象化（煞/食/身分别判根）", "output_state": "root_relation_state", "evidence_chain": ["PZZQ-007-028"]},
    {"rule_id": "RULE-022C-08", "classic_source": "YHZP-063-001（月令入口语境锚）", "namespace": "PZZQ.pattern", "producer": "022D", "input_contract": "月令入口（不得自动判强弱）", "output_state": "month_order_entry", "evidence_chain": ["YHZP-063-001"]},
]

REQUIRED = ["rule_id", "classic_source", "namespace", "producer", "input_contract", "output_state", "evidence_chain"]

S = {"order_state": "NOT_GET_ORDER", "bj_tou": [], "wealth_relation_state": "UNDETERMINED", "strength_state": "UNDETERMINED"}


def check_bindings():
    ok, missing = [], []
    for r in ADMITTED_BINDINGS:
        miss = [f for f in REQUIRED if not r.get(f)]
        if miss:
            missing.append((r["rule_id"], miss))
        else:
            ok.append(r["rule_id"])
    return ok, missing


def chart_1983_match():
    """1983-1103 规则匹配演示（绑定后行为不变）"""
    hits = []
    if S["order_state"] == "GET_ORDER":
        hits.append("CAND-WANG-001→wang_state")
    if S["order_state"] == "NOT_GET_ORDER":
        hits.append("CAND-SHUAI-001→shuai_state=SHUAI")
    if S["order_state"] == "NOT_GET_ORDER" and not S["bj_tou"]:
        hits.append("CAND-QIANG-001 未触发（无天干比劫透）")
    return hits, "strength_state=UNDETERMINED（无授权综合，FAIL_CLOSED）"


if __name__ == "__main__":
    print("==== PATCH-028 Rule Admission Layer ====")
    print("\n==== 状态机 ====")
    print("  DRAFT → CANDIDATE → ADMITTED / REJECTED（门槛：证据绑定→11门槛→Golden）")
    print("  ADMITTED=资格层≠自动执行；golden_pass 未过不得进引擎")
    print("\n==== 12 条 ADMITTED 绑定完整性 ====")
    ok, missing = check_bindings()
    print(f"  完整绑定: {len(ok)} 条")
    print(f"  缺口: {missing if missing else '无'}")
    print("\n==== 禁止链 ====")
    print("  经典原文→状态：FORBIDDEN（原文命中只是 Evidence）")
    print("  必须：原文→规则解析→namespace→producer→state")
    print("\n==== QTBJ-018-001 政策 ====")
    print("  保持 CANDIDATE_RULE，不先升格（先框架后准入，防规则先通过架构后补）")
    print("\n==== 1983-1103 匹配演示 ====")
    hits, note = chart_1983_match()
    for h in hits:
        print(f"  {h}")
    print(f"  {note}")
