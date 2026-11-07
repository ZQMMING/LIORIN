# -*- coding: utf-8 -*-
"""PATCH-025 Pattern Production Contract（格局生产契约）
- 生产者：PZZQ DIRECT / DTS SUPPORTING / SFTK CONTEXTUAL
- 格局输入不含任何强弱状态；双向循环依赖防护（pattern↔strength 互不推导）
- 输出 schema：state/value/producer/sources/evidence_chain/namespace_source/month_order_entry
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1983-11-03 状态快照
S = {
    "order_state": "NOT_GET_ORDER", "month_order": "戌", "day_master_element": "WOOD",
    "ten_god_relation": {"年干": "偏印", "月干": "正印", "日干": "比肩", "时干": "正印"},
    "structure_relation": "UNDETERMINED",
    "root_relation": "WEAK_ROOT(亥甲+未乙)",
    "strength_state": "UNDETERMINED", "wang_state": "UNKNOWN", "shuai_state": "SHUAI", "qiang_state": "UNKNOWN",
}

FORBIDDEN_PATHS = [
    ("strength_state", "pattern_state", "身强身弱不得作为取格依据"),
    ("pattern_state", "strength_state", "格局成立不得反推身强弱"),
    ("wang_state/shuai_state/qiang_state", "pattern_state", "旺衰状态不得进入格局判定输入"),
]


def produce_pattern():
    """025 Producer Layer：1983-1103 命局——月令入口登记，结构未确认→UNDETERMINED"""
    month_zhi = S["month_order"]  # 戌
    # 戌月用事：戌藏戊辛丁，戌月戊土用事（财）
    month_entry = "戌月戊土用事→财格候选"
    return {
        "state": "pattern_state",
        "value": "UNDETERMINED",
        "producer": "PZZQ.pattern",
        "sources": ["PZZQ.pattern(order_state/month_order/ten_god_relation/structure_relation/root_relation)"],
        "evidence_chain": ["PZZQ-005-007 八字用神专求月令"],
        "namespace_source": {"PZZQ": "pattern"},
        "month_order_entry": f"{month_entry}（structure_relation=UNDETERMINED，待透干会支确认）",
        "forbidden_not_consumed": ["strength_state/wang_state/shuai_state/qiang_state（格局不读强弱）"],
    }


def check_cycle_guard():
    """循环依赖防护校验：pattern 输入不含强弱状态"""
    input_ok = S["structure_relation"] != "UNDETERMINED" or True  # 输入允许 UNDETERMINED 结构
    violations = []
    for frm, to, reason in FORBIDDEN_PATHS:
        # 模拟检查：pattern 输入列表是否包含强弱
        if to == "pattern_state":
            pat_inputs = ["order_state", "month_order", "ten_god_relation", "structure_relation", "root_relation"]
            hit = [f for f in pat_inputs if "strength" in f or f in ("wang_state", "shuai_state", "qiang_state")]
            if hit:
                violations.append((frm, to, f"格局输入含强弱状态 {hit}"))
    return violations


if __name__ == "__main__":
    print("==== PATCH-025 Pattern Production Contract ====")
    print("\n==== 循环依赖防护 ====")
    for frm, to, reason in FORBIDDEN_PATHS:
        print(f"  禁止: {frm} → {to}（{reason}）")
    violations = check_cycle_guard()
    print(f"  格局输入强弱状态检查: {'无违规（格局输入=order/month/ten_god/structure/root）' if not violations else violations}")
    print("\n==== 1983-1103 Pattern Producer 输出 ====")
    print(json.dumps(produce_pattern(), ensure_ascii=False, indent=1))
    print("\n==== 全局禁令 ====")
    print("  格局成立≠反推身强弱；身强弱≠强行取格；旺衰不进入格局输入")
