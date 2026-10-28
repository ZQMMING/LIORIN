# -*- coding: utf-8 -*-
"""ZIPING V3.1 规则加载器 — YAML 声明式规则 → 布尔条件树.

设计: 条件 DSL 是**封闭算子集** (确定性), 结构上拒绝任何数值/数量/百分比算子
(§2 FORBIDDEN + §50 REV-FORBIDDEN + ARCH-007). 未知算子即拒绝加载, 不猜测.

允许的 DSL 算子 (closed set):
    eq        field == value
    ne        field != value
    in        field in [..]
    notin     field not in [..]
    exists    field present (truthy or non-None)
    rel       relation(a,b) == X   (五行关系枚举, §4.1)
    season    month_branch in season S
    hide      hidden_stems 某支含某干 (main/mid/res/all)
    stem_in   某干透于四柱
    br_in     某支见于四柱
    derived   derived.states[k] == value
    true      恒真 / false 恒假 (占位, 仅供组合)

字段路径 (field) 取值:
    fact.<...>     Bazi 事实 (four_pillars / day_master / month_branch / ...)
    derived.<k>    已产出的派生状态
    ctx.<...>      引擎符号表查询 (stem_in / br_in / hide / ...)
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

import yaml

from .engine import EngineContext, MethodScope, Rule
from .types import ZiPingDerivedFact

# FORBIDDEN 算子 — 出现在 YAML 即拒绝 (ARCH-007 + §50 数值等价物)
_FORBIDDEN_OPS = {
    "lt", "gt", "le", "gte", "lt=", "gt=", "<", ">", "<=", ">=",
    "count", "count>=", "count<=", "sum", "score", "weight", "percentage",
    "ratio", "rank", "average", "normalize", "threshold", "vote", "majority",
}
_FORBIDDEN_TOKENS = re.compile(
    r"(?i)\b(score|weight|percentage|ratio|count|threshold|cutoff|"
    r"min_score|max_score|>=\s*\d|<=\s*\d|count_as|support_count|"
    r"dominant_by_presence|has_many|major_support)\b"
)


class RuleLoadError(Exception):
    pass


def _compile_condition(spec: Dict[str, Any], ctx_cls: type) -> Callable:
    """单个条件 dict → ConditionFn (ctx, derived) -> bool. 未知算子即报错."""
    op = spec.get("op")
    if op in _FORBIDDEN_OPS:
        raise RuleLoadError(f"FORBIDDEN 算子被拒绝加载: {op!r} (§2/§50 ARCH-007)")
    if _FORBIDDEN_TOKENS.search(str(spec)):
        raise RuleLoadError(f"FORBIDDEN 数值模型等价物被拒绝加载: {spec}")

    def _field(ctx: EngineContext, key: str) -> Any:
        if key.startswith("derived."):
            return ctx and derived_state(key.split(".", 1)[1])
        if key.startswith("ctx."):
            return getattr(ctx, key.split(".", 1)[1], None)
        if key.startswith("fact."):
            return getattr(ctx.fact, key.split(".", 1)[1], None)
        return getattr(ctx, key, None)

    def derived_state(k: str) -> Any:
        # 闭包引用由调用方注入 — 通过 ctx 传递
        return getattr(ctx, "_cur_derived", None).states.get(k) if hasattr(ctx, "_cur_derived") else None

    if op == "eq":
        key, val = spec["field"], spec["value"]
        return lambda ctx, der: _field(ctx, key) == val

    if op == "ne":
        key, val = spec["field"], spec["value"]
        return lambda ctx, der: _field(ctx, key) != val

    if op == "in":
        key, vals = spec["field"], spec["value"]
        return lambda ctx, der: _field(ctx, key) in vals

    if op == "notin":
        key, vals = spec["field"], spec["value"]
        return lambda ctx, der: _field(ctx, key) not in vals

    if op == "exists":
        key = spec["field"]
        return lambda ctx, der: _field(ctx, key) not in (None, "", [], {})

    if op == "rel":
        a, b, want = spec["a"], spec["b"], spec["value"]
        return lambda ctx, der: ctx.relation(a, b) == want

    if op == "season":
        season = spec["value"]
        return lambda ctx, der: ctx.month_season_state() == season

    if op == "hide":
        branch, stem = spec["branch"], spec["stem"]
        role = spec.get("role", "any")
        def _h(ctx, der):
            bb = ctx.hidden_of(branch)
            if role == "any":
                return any(bb.get(r, "") == stem for r in ("main", "middle", "residual"))
            return bb.get(role, "") == stem
        return _h

    if op == "stem_in":
        stem = spec["value"]
        return lambda ctx, der: ctx.stem_in_pillars(stem)

    if op == "br_in":
        br = spec["value"]
        return lambda ctx, der: ctx.branch_in_pillars(br)

    if op == "derived":
        k, val = spec["state"], spec.get("value", True)
        return lambda ctx, der: der.states.get(k) == val

    if op == "true":
        return lambda ctx, der: True

    if op == "false":
        return lambda ctx, der: False

    raise RuleLoadError(f"未知 DSL 算子 (拒绝猜测, fail-closed): {op!r}")


def load_rule_set(data: Dict[str, Any]) -> "RuleSet":
    """YAML dict (单域) → RuleSet. 全量 FORBIDDEN 校验."""
    from .engine import RuleSet

    if _FORBIDDEN_TOKENS.search(yaml.safe_dump(data, allow_unicode=True)):
        raise RuleLoadError(f"规则域含 FORBIDDEN 数值术语, 拒绝加载: {data.get('domain')}")

    rs = RuleSet(domain=str(data["domain"]))
    for r in data.get("rules", []):
        allfns = [_compile_condition(c, None) for c in r.get("all", [])]
        anyfns = None
        if r.get("any"):
            anyfns = [[_compile_condition(c, None) for c in branch] for branch in r["any"]]
        scope = [MethodScope(s) for s in r.get("method_scope", ["disputed"])]
        rule = Rule(
            rule_id=str(r["rule_id"]),
            domain=rs.domain,
            conditions_all=allfns,
            conditions_any=anyfns,
            result_state=str(r.get("result", {}).get("state", "")),
            evidence_refs=list(r.get("evidence_refs", [])),
            method_scope=scope,
            requires=list(r.get("requires", [])),
            invalidated_by=list(r.get("invalidated_by", [])),
            overrides=list(r.get("overrides", [])),
            coexists_with=list(r.get("coexists_with", [])),
            mutually_exclusive_with=list(r.get("mutually_exclusive_with", [])),
        )
        rs.add(rule)
    return rs


def load_rule_file(path: str) -> "RuleSet":
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return load_rule_set(data)
