# -*- coding: utf-8 -*-
"""L0 条件三元组规范 condition_spec.py —— 全部底层的共同语言

方法论铁律(用户锁定):
  禁浮点/乘除加权; 只布尔 + 序数 + 离散枚举 + 规则优先级; 原著优先, 无原文标 UNVERIFIED。

一条可机读条件 = 三元组 + 可选取反:
    Condition = {
        "fact":   "点路径, 引用 facts 深层字段 (如 wuxing_power.土.combo / ge_cheng.ti_wx)",
        "op":     "eq | ne | in | not_in | gte | lte | exists | not_exists",
        "value":  枚举值/序数/五行/字符串/列表 (禁 float),
        "negate": false   # 整体取反标志 (NOT 条件)
    }

op 语义(全部离散):
    eq        事实 == value                     (布尔相等)
    ne        事实 != value
    in        事实 ∈ value(list)                (集合枚举)
    not_in    事实 ∉ value(list)
    gte       事实 >= value                     (序数比较, 双方必须 int)
    lte       事实 <= value
    exists    fact 路径存在且值非 None/空        (存在性)
    not_exists fact 路径缺失或值为 None/空

条件组合(见 condition_evaluator.py):
    AND 组: 全部 MATCHED -> MATCHED; 任一 NOT_MATCHED -> NOT_MATCHED; 否则 ABSTAIN
    OR  组: 任一 MATCHED -> MATCHED; 全部 NOT_MATCHED -> NOT_MATCHED; 否则 ABSTAIN

本模块只做定义 + 校验, 不做求值(求值在 condition_evaluator.py)。
"""
from typing import Any, Dict, List, Optional

# 合法 op 枚举(布尔 + 序数 + 存在性 + 集合)
OPS = ("eq", "ne", "in", "not_in", "gte", "lte", "exists", "not_exists")

# 序数比较 op(要求 value 与事实均为 int)
ORDER_OPS = ("gte", "lte")

# 集合 op(要求 value 为非空 list)
SET_OPS = ("in", "not_in")

# 存在性 op(不要求 value)
EXIST_OPS = ("exists", "not_exists")

# 被禁止的字段/值类型: 浮点、权重、置信度、评分 —— 方法论红线
FORBIDDEN_VALUE_TYPES = (float,)

FORBIDDEN_VALUE_KEYWORDS = ("weight", "score", "confid", "prob", "ratio", "percent")


class ConditionError(ValueError):
    """条件非法。"""


def validate_condition(c: Dict[str, Any]) -> None:
    """校验一条条件。非法即抛 ConditionError。

    校验点:
      1. fact 非空字符串
      2. op ∈ OPS
      3. 序数 op: value 必须 int
      4. 集合 op: value 必须非空 list
      5. 存在性 op: 不带 value 或 value 忽略
      6. value 禁 float; 若为 list, 逐元素禁 float
      7. fact 禁含权重/置信度类关键词
    """
    if not isinstance(c, dict):
        raise ConditionError("条件必须是 dict, 收到 %r" % type(c).__name__)
    fact = c.get("fact")
    if not isinstance(fact, str) or not fact.strip():
        raise ConditionError("fact 必须是非空字符串")
    op = c.get("op")
    if op not in OPS:
        raise ConditionError("op=%r 非法, 合法=%s" % (op, OPS))
    value = c.get("value")

    # 关键词红线(浮点/权重/置信度)
    for kw in FORBIDDEN_VALUE_KEYWORDS:
        if kw in fact.lower():
            raise ConditionError("fact 含禁用关键词 %r: %r" % (kw, fact))

    if op in ORDER_OPS:
        if not isinstance(value, int):
            raise ConditionError("op=%s 要求 value 为 int, 收到 %r" % (op, value))
    elif op in SET_OPS:
        if not isinstance(value, list) or not value:
            raise ConditionError("op=%s 要求 value 为非空 list, 收到 %r" % (op, value))
        for v in value:
            if isinstance(v, FORBIDDEN_VALUE_TYPES):
                raise ConditionError("op=%s value 元素禁浮点: %r" % (op, v))
    elif op in EXIST_OPS:
        pass  # 存在性条件不要求 value
    else:  # eq / ne
        if isinstance(value, FORBIDDEN_VALUE_TYPES):
            raise ConditionError("op=%s value 禁浮点: %r" % (op, value))

    # negate 可选, 必须 bool
    if "negate" in c and not isinstance(c.get("negate"), bool):
        raise ConditionError("negate 必须 bool")


def norm_condition(c: Dict[str, Any]) -> Dict[str, Any]:
    """归一化: 补默认值, 过校验。返回规范形态。"""
    out = dict(c)
    out.setdefault("negate", False)
    validate_condition(out)
    return out


def validate_condition_group(group: List[Dict[str, Any]], logic: str = "AND") -> None:
    """校验一组条件(AND/OR 组)。"""
    if logic not in ("AND", "OR"):
        raise ConditionError("组逻辑必须 AND/OR, 收到 %r" % logic)
    if not isinstance(group, list) or not group:
        raise ConditionError("条件组必须非空 list")
    for c in group:
        validate_condition(c)


def resolve_dotted(facts: Dict[str, Any], path: str) -> "tuple[bool, Any]":
    """点路径取值: facts['wuxing_power']['土']['combo']。

    路径段支持:
      - dict 键:           a.b.c
      - list 索引:         a.0.b
      - list 属性投影:     a.#.key  (取列表每元素的 key, 返回 list; 用于「成党/透干任一属某五行」)
    返回 (found, value); 路径断在空/缺键 -> (False, None)。
    """
    cur: Any = facts
    for seg in path.split("."):
        if seg == "":
            return False, None
        if isinstance(cur, dict):
            if seg not in cur:
                return False, None
            cur = cur[seg]
        elif isinstance(cur, list):
            if seg == "#":
                # 投影: 列表每元素取下一段
                nxt = path.split(".", 1)[1] if "." in path else ""
                if not nxt:
                    return False, None
                vals = []
                for it in cur:
                    if isinstance(it, dict):
                        ok, v = resolve_dotted(it, nxt)
                        if ok:
                            vals.append(v)
                return (True, vals) if vals else (False, None)
            try:
                cur = cur[int(seg)]
            except (ValueError, IndexError):
                return False, None
        else:
            return False, None
    return True, cur


def is_empty_value(v: Any) -> bool:
    """空值判定(用于 exists/not_exists)。"""
    if v is None:
        return True
    if isinstance(v, (str, list, dict)):
        return len(v) == 0
    return False
