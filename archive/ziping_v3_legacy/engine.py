# -*- coding: utf-8 -*-
"""ZIPING V3.1 布尔规则引擎核心.

设计约束 (编译级):
  - §2 FORBIDDEN: 引擎层无 score/weight/percentage/投票/计数阈值.
    条件求值只允许: 布尔恒真恒假 / 枚举相等 / 集合成员 / 结构存在性
    (特定结构存在 / 特定根有效 / 特定关系成立 / 特定条件被破坏或救应成立, §50 四形态).
  - §77: 任何 UNDETERMINED 必须携带六因之一.
  - ARCH-009/013: 命中即记录 rule_id + evidence_refs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .constants import (
    BRANCH_ELEMENT,
    BRANCH_HIDDEN,
    CONTROLS,
    GENERATES,
    SEASON_OF_MONTH,
    STEM_ELEMENT,
    STORE_BRANCHES,
)
from .types import (
    FrozenBaziFact,
    MethodScope,
    UndeterminedReason,
    ZiPingDerivedFact,
    ZiPingJudgment,
)

# 条件求值器: (context, derived) -> bool
ConditionFn = Callable[["EngineContext", ZiPingDerivedFact], bool]


class EngineError(Exception):
    """规则求值遇到不可恢复错误 (fail-closed)."""


@dataclass
class Rule:
    """V3.1 单条规则 (§1 标准格式的运行时表示)."""
    rule_id: str
    domain: str
    conditions_all: List[ConditionFn] = field(default_factory=list)
    conditions_any: Optional[List[List[ConditionFn]]] = None  # 任一分支满足
    result_state: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    method_scope: List[MethodScope] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)        # 前置事实/状态名
    invalidated_by: List[str] = field(default_factory=list)
    overrides: List[str] = field(default_factory=list)
    coexists_with: List[str] = field(default_factory=list)
    mutually_exclusive_with: List[str] = field(default_factory=list)

    def evaluate(self, ctx: "EngineContext", derived: ZiPingDerivedFact) -> Optional[bool]:
        """返回 True/False; 前置缺失 → None (由调用方转 UNDETERMINED)."""
        for req in self.requires:
            if req not in ctx.available_facts and req not in derived.states:
                return None
        if self.conditions_all and not all(c(ctx, derived) for c in self.conditions_all):
            return False
        if self.conditions_any:
            if not any(all(c(ctx, derived) for c in branch) for branch in self.conditions_any):
                return False
        return True


@dataclass
class RuleSet:
    """一个域的规则集合 + 裁决."""
    domain: str
    rules: List[Rule] = field(default_factory=list)

    def add(self, rule: Rule) -> None:
        if any(r.rule_id == rule.rule_id for r in self.rules):
            raise EngineError(f"规则重复注册: {rule.rule_id} (domain={self.domain})")
        self.rules.append(rule)

    def hit(self, ctx: EngineContext, derived: ZiPingDerivedFact) -> List[Rule]:
        out = []
        for r in self.rules:
            res = r.evaluate(ctx, derived)
            if res is True:
                out.append(r)
        return out

    def undetermined_reason(self, ctx: EngineContext, derived: ZiPingDerivedFact) -> List[Rule]:
        return [r for r in self.rules if r.evaluate(ctx, derived) is None]


class EngineContext:
    """求值上下文: Bazi 事实 + 符号表 + 可选输入."""

    def __init__(
        self,
        fact: FrozenBaziFact,
        available_facts: Optional[Set[str]] = None,
        temporal_inputs: Optional[Dict[str, Tuple[str, str]]] = None,
    ) -> None:
        self.fact = fact
        self.available_facts = available_facts or set()
        # 时间层输入 (流年/流月/流日 由调用方注入; 缺失 → UNDETERMINED)
        self.temporal = temporal_inputs or {}

    # ---------- 符号表 (确定性枚举, ARCH-003~006 合规: 不重算 Bazi) ----------

    @staticmethod
    def element_of_stem(stem: str) -> Optional[str]:
        return STEM_ELEMENT.get(stem, None)

    @staticmethod
    def element_of_branch(branch: str) -> Optional[str]:
        return BRANCH_ELEMENT.get(branch, None)

    @staticmethod
    def relation(a: str, b: str) -> Optional[str]:
        """a 与 b 五行关系 (a 视角): SAME/SUPPORTIVE/DRAINING/CONSUMING/OPPOSING."""
        if a == b:
            return "SAME"
        if GENERATES.get(a) == b:
            return "DRAINING"     # a 生 b: a 泄
        if GENERATES.get(b) == a:
            return "SUPPORTIVE"   # b 生 a: a 得生
        if CONTROLS.get(a) == b:
            return "CONSUMING"    # a 克 b: a 耗 (我克)
        if CONTROLS.get(b) == a:
            return "OPPOSING"     # b 克 a: a 受克
        return None

    @staticmethod
    def hidden_of(branch: str) -> Dict[str, str]:
        return BRANCH_HIDDEN.get(branch, {"main": "", "middle": "", "residual": "", "all": []})

    def month_season_state(self) -> Optional[str]:
        if "month_branch" not in self.available_facts:
            return None
        return SEASON_OF_MONTH.get(self.fact.month_branch)

    def stem_in_pillars(self, stem: str) -> bool:
        """某干是否透于四柱天干."""
        return any(p[0] == stem for p in self.fact.four_pillars)

    def branch_in_pillars(self, branch: str) -> bool:
        return any(p[1] == branch for p in self.fact.four_pillars)

    def hidden_contains(self, stem: str) -> bool:
        """某干是否藏于四支藏干 (任意气)."""
        for pos in ("YEAR", "MONTH", "DAY", "HOUR"):
            b = self.fact.pillar_branch(pos)
            for role in ("main", "middle", "residual"):
                if self.hidden_of(b).get(role, "") == stem:
                    return True
        return False

    def is_store_branch(self, branch: str) -> bool:
        return branch in STORE_BRANCHES


class JudgmentBuilder:
    """命中规则 → ZiPingJudgment (强制四要素 + UNDETERMINED 分因)."""

    @staticmethod
    def from_hits(
        domain: str,
        state: str,
        hits: "Rule | List[Rule]",
        method_scope: Optional[List[MethodScope]] = None,
        invalidated_by: Optional[List[str]] = None,
    ) -> ZiPingJudgment:
        if isinstance(hits, Rule):
            hits = [hits]
        elif not isinstance(hits, (list, tuple)):
            hits = list(hits)
        scope = method_scope if method_scope is not None else hits[0].method_scope if hits else [MethodScope.DISPUTED]
        evidence: List[str] = []
        for r in hits:
            for e in r.evidence_refs:
                if e not in evidence:
                    evidence.append(e)
        return ZiPingJudgment(
            domain=domain,
            state=state,
            matched_rule_ids=[r.rule_id for r in hits],
            evidence_refs=evidence,
            method_scope=scope,
            invalidated_by=invalidated_by,
        )

    @staticmethod
    def undetermined(
        domain: str,
        reason: UndeterminedReason,
        detail: str = "",
    ) -> ZiPingJudgment:
        return ZiPingJudgment(
            domain=domain,
            state="UNDETERMINED",
            matched_rule_ids=[],
            evidence_refs=[],
            method_scope=[MethodScope.DISPUTED],
            reason=reason,
            reason_detail=detail,
        )
