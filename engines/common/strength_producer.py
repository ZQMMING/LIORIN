# -*- coding: utf-8 -*-
"""PATCH-024 Strength State Production Contract（强弱状态生产契约）
- Producer 白名单：wang/shuai/qiang/strength_state 各自生产者
- 输出必须带 producer_trace/evidence_chain/namespace_source（可追溯）
- strength_state 综合生产：DTS.strength_relation + PZZQ.strength_condition + YHZP.support_relation + SMTH.time_modifier
- 无授权组合 → UNDETERMINED（FAIL_CLOSED）
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1983-11-03 状态快照（state_producer 产出）
S = {
    "order_state": "NOT_GET_ORDER", "day_master_element": "WOOD",
    "wang_state": "UNKNOWN", "shuai_state": "SHUAI", "qiang_state": "UNKNOWN",
    "support_relation": "SUPPORT_PRESENT(水透三)", "root_relation": "WEAK_ROOT(亥甲+未乙)",
    "structure_relation": "UNDETERMINED", "trend_state": "PENDING",
    "seasonal_state": "QTBJ_REQUIRED", "time_modifier": "未启动",
    "bj_tou": [],  # 天干比劫透
}

PRODUCER_WHITELIST = {
    "wang_state": [{"scope": "YHZP", "ns": "wang_expression", "rule": "CAND-WANG-001(得时俱为旺论 YHZP-138-001 A)", "mode": "DIRECT"},
                   {"scope": "DTS", "ns": "wang_relation", "rule": "CAND-WANG-002(旺中有衰 B1)", "mode": "SUPPORTING"}],
    "shuai_state": [{"scope": "YHZP", "ns": "wang_expression", "rule": "CAND-SHUAI-001(失令便作衰看 YHZP-138-001 A)", "mode": "DIRECT"}],
    "qiang_state": [{"scope": "YHZP", "ns": "wang_expression", "rule": "CAND-QIANG-001(日干无气遇劫为强 YHZP-138-001 A)", "mode": "DIRECT"}],
    "strength_state": [{"scope": "DTS", "ns": "strength_relation", "mode": "INPUT"},
                       {"scope": "PZZQ", "ns": "strength_condition", "mode": "INPUT"},
                       {"scope": "YHZP", "ns": "support_relation", "mode": "INPUT"},
                       {"scope": "SMTH", "ns": "time_modifier", "mode": "INPUT"}],
}


def produce_strength():
    """024 Producer Layer：1983-1103 命局"""
    # wang_state：CAND-WANG-001 未触发（非 GET_ORDER）
    wang = {"state": "wang_state", "value": "UNKNOWN", "producer": "YHZP.wang_expression(CAND-WANG-001)",
            "sources": ["YHZP.wang_expression"], "evidence_chain": ["YHZP-138-001 得时俱为旺论（条件未满足：order=NOT_GET_ORDER）"],
            "namespace_source": {"YHZP": "wang_expression"}}
    # shuai_state：CAND-SHUAI-001 触发
    shuai = {"state": "shuai_state", "value": "SHUAI", "producer": "YHZP.wang_expression(CAND-SHUAI-001)",
             "sources": ["YHZP.wang_expression"], "evidence_chain": ["YHZP-138-001 失令便作衰看（order=NOT_GET_ORDER 触发）"],
             "namespace_source": {"YHZP": "wang_expression"}}
    # qiang_state：CAND-QIANG-001 双条件未齐（无天干比劫透）
    qiang = {"state": "qiang_state", "value": "UNKNOWN", "producer": "YHZP.wang_expression(CAND-QIANG-001)",
             "sources": ["YHZP.wang_expression"], "evidence_chain": ["YHZP-138-001 日干无气遇劫为强（天干比劫透=0，条件未齐）"],
             "namespace_source": {"YHZP": "wang_expression"}}
    # strength_state：综合生产，当前无授权组合 → UNDETERMINED
    strength = {"state": "strength_state", "value": "UNDETERMINED", "producer": "024",
                "sources": ["DTS.strength_relation(PENDING)", "PZZQ.strength_condition(UNDETERMINED)", "YHZP.support_relation(SUPPORT_PRESENT)", "SMTH.time_modifier(未启动)"],
                "evidence_chain": ["YHZP-138-001", "YHZP-063-001(身旺身弱月令入口)"],
                "namespace_source": {"DTS": "strength_relation", "PZZQ": "strength_condition", "YHZP": "support_relation", "SMTH": "time_modifier"},
                "note": "综合生产条件未授权组合（无单一经典直产 strength_state）→ FAIL_CLOSED 正确"}
    return {"wang_state": wang, "shuai_state": shuai, "qiang_state": qiang, "strength_state": strength}


if __name__ == "__main__":
    print("==== PATCH-024 Strength State Production Contract ====")
    print("\n==== Producer 白名单 ====")
    for state, prods in PRODUCER_WHITELIST.items():
        print(f"  {state}: {json.dumps(prods, ensure_ascii=False)}")
    print("\n==== 1983-1103 Producer Layer 输出（全可追溯） ====")
    out = produce_strength()
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("\n==== 追溯性验证 ====")
    for k, v in out.items():
        ok = all(f in v for f in ("state", "value", "producer", "sources", "evidence_chain", "namespace_source"))
        print(f"  {k}: {'✔ 含完整 trace 字段' if ok else '✘ 缺字段'}")
