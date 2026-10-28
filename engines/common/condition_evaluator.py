# -*- coding: utf-8 -*-
"""L2 条件求值器 condition_evaluator.py —— 通用三态求值引擎

断言(assertion_matcher)与切片(病药/格局)共用同一求值器:
    条件三元组 {fact, op, value, negate} vs facts 全层 -> MATCHED / NOT_MATCHED / ABSTAIN

三态语义:
    MATCHED      条件成立(含 negate 取反后成立)
    NOT_MATCHED  条件明确不成立
    ABSTAIN      事实缺失(路径断/空值) -> 不裁决, 向上传播

组合:
    AND 组: 全部 MATCHED -> MATCHED; 任一 NOT_MATCHED -> NOT_MATCHED; 否则 ABSTAIN
    OR  组: 任一 MATCHED -> MATCHED; 全部 NOT_MATCHED -> NOT_MATCHED; 否则 ABSTAIN

越权守卫: 求值器不产生 state/strength/use_god/score 等裁决字段。
"""
from typing import Any, Dict, List, Tuple

try:
    from engines.common.condition_spec import (
        EXIST_OPS,
        FORBIDDEN_VALUE_KEYWORDS,
        ORDER_OPS,
        SET_OPS,
        is_empty_value,
        norm_condition,
        resolve_dotted,
        validate_condition_group,
    )
except ImportError:  # 兼容裸路径运行(tests 直接跑 engines/common 下)
    from condition_spec import (
        EXIST_OPS,
        FORBIDDEN_VALUE_KEYWORDS,
        ORDER_OPS,
        SET_OPS,
        is_empty_value,
        norm_condition,
        resolve_dotted,
        validate_condition_group,
    )

# 越权字段集(沿用 assertion_matcher.FORBIDDEN, 求值器自身不产出)
FORBIDDEN = ('climate_state', 'strength_state', 'use_god', 'destiny',
             'fortune_level', 'state', 'fortune', 'winner', 'score')


def evaluate_condition(cond: Dict[str, Any], facts: Dict[str, Any]) -> Tuple[str, str]:
    """单条件求值。返回 (status, reason)。

    求值顺序:
      1. 取事实: resolve_dotted; 找不到 -> ABSTAIN(missing_fact)
      2. 存在性 op: 空值判定
      3. 常规 op: 按 op 比较
      4. negate=True: 结果取反(MATCHED<->NOT_MATCHED; ABSTAIN 保持)
    """
    c = norm_condition(cond)
    fact, op, value, negate = c["fact"], c["op"], c.get("value"), c.get("negate", False)

    found, val = resolve_dotted(facts, fact)
    if not found:
        if op == "not_exists":
            st = "MATCHED"
        elif op == "exists":
            st = "NOT_MATCHED"
        else:
            return "ABSTAIN", "missing_fact:%s" % fact
        return (st, "%s(事实缺失)" % fact) if not negate else (
            ("NOT_MATCHED" if st == "MATCHED" else "MATCHED"),
            "%s(negate 取反)" % fact)

    # 存在性判定
    if op in EXIST_OPS:
        empty = is_empty_value(val)
        st = "MATCHED" if (op == "exists" and not empty) or (op == "not_exists" and empty) else "NOT_MATCHED"
        why = "%s=%r" % (fact, val)
    elif op == "eq":
        st = "MATCHED" if val == value else "NOT_MATCHED"
        why = "%s=%r %s %r" % (fact, val, "==" if st == "MATCHED" else "!=", value)
    elif op == "ne":
        st = "MATCHED" if val != value else "NOT_MATCHED"
        why = "%s=%r %s %r" % (fact, val, "!=" if st == "MATCHED" else "==", value)
    elif op in SET_OPS:
        st = "MATCHED" if (val in value) == (op == "in") else "NOT_MATCHED"
        why = "%s=%r %s %s" % (fact, val, "∈" if st == "MATCHED" else "∉", value)
    elif op in ORDER_OPS:
        # 序数比较: 双方必须 int(布尔/离散红线)
        if not isinstance(val, int) or not isinstance(value, int):
            return "ABSTAIN", "non_ordinal:%s=%r vs %r" % (fact, val, value)
        st = "MATCHED" if (val >= value) == (op == "gte") else "NOT_MATCHED"
        why = "%s=%d %s %d" % (fact, val, ">=" if op == "gte" else "<=", value)
    else:
        return "ABSTAIN", "unsupported_op:%s" % op

    if negate:
        st = "NOT_MATCHED" if st == "MATCHED" else "MATCHED"
        why += " | negate 取反"
    return st, why


def evaluate_group(group: List[Dict[str, Any]], facts: Dict[str, Any],
                   logic: str = "AND") -> Tuple[str, str, List[str]]:
    """一组条件求值。返回 (status, reason, 逐条reason)。"""
    validate_condition_group(group, logic)
    details: List[str] = []
    if logic == "AND":
        for c in group:
            st, why = evaluate_condition(c, facts)
            details.append("%s: %s" % (c["fact"], why))
            if st == "NOT_MATCHED":
                return "NOT_MATCHED", "AND: %s" % why, details
        for c in group:
            st, why = evaluate_condition(c, facts)
            if st == "ABSTAIN":
                return "ABSTAIN", "AND: 事实缺失 %s" % c["fact"], details
        return "MATCHED", "AND: 全部成立", details
    # OR
    any_abstain = False
    for c in group:
        st, why = evaluate_condition(c, facts)
        details.append("%s: %s" % (c["fact"], why))
        if st == "MATCHED":
            return "MATCHED", "OR: %s" % why, details
        if st == "ABSTAIN":
            any_abstain = True
    if any_abstain:
        return "ABSTAIN", "OR: 全部未匹配且含事实缺失", details
    return "NOT_MATCHED", "OR: 全部不成立", details


def evaluate(conds: Dict[str, Any], facts: Dict[str, Any]) -> Tuple[str, str, List[str]]:
    """顶层求值入口。conds 形态:
        {"logic": "AND"|"OR", "conditions": [三元组, ...]}
    """
    logic = conds.get("logic", "AND")
    group = conds.get("conditions", [])
    return evaluate_group(group, facts, logic)


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    # 冒烟: 用真实 facts 片段
    facts = {
        "day_stem": "乙",
        "month_branch": "戌",
        "wuxing_power": {"土": {"combo": 6, "ling_state": "旺"}},
        "ge_cheng": {"ti_wx": ["土"], "xi_wx": ["水"]},
        "combination_facts": {"resolved": {"chong_survive": []}},
    }
    cases = [
        ("eq", {"fact": "day_stem", "op": "eq", "value": "乙"}, "MATCHED"),
        ("ne", {"fact": "day_stem", "op": "ne", "value": "甲"}, "MATCHED"),
        ("in", {"fact": "ge_cheng.ti_wx", "op": "in", "value": ["土"]}, "MATCHED"),
        ("not_in", {"fact": "ge_cheng.ti_wx", "op": "not_in", "value": ["水"]}, "MATCHED"),
        ("gte", {"fact": "wuxing_power.土.combo", "op": "gte", "value": 6}, "MATCHED"),
        ("lte", {"fact": "wuxing_power.土.combo", "op": "lte", "value": 5}, "NOT_MATCHED"),
        ("exists", {"fact": "ge_cheng.xi_wx", "op": "exists"}, "MATCHED"),
        ("not_exists", {"fact": "combination_facts.resolved.chong_survive", "op": "not_exists"}, "NOT_MATCHED"),
        ("missing", {"fact": "yongyao.primary", "op": "eq", "value": "木"}, "ABSTAIN"),
        ("negate", {"fact": "month_branch", "op": "eq", "value": "寅", "negate": True}, "MATCHED"),
    ]
    ok = 0
    for name, c, want in cases:
        st, why = evaluate_condition(c, facts)
        mark = "✓" if st == want else "✗"
        if st == want:
            ok += 1
        print("  %s %-10s -> %-12s want=%-12s %s" % (mark, name, st, want, why))
    print("通过 %d/%d" % (ok, len(cases)))
