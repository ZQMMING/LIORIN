# -*- coding: utf-8 -*-
"""ZIPING V3.1-FINAL 规则引擎包.

分层 (§51 REV-TYPE 类型隔离):
    constants       确定性参考表 (纯数据, 非计算)
    types           四层分型 + §28 输出契约
    engine          布尔规则引擎核心 (封闭 DSL, FORBIDDEN 拒绝加载)
    rules_loader    YAML 规则 → 条件树 (含 FORBIDDEN 数值等价物拦截)
    facts_adapter   BaziChart → FrozenBaziFact (只搬运, 不重算, ARCH-003~006)
    pipeline        §79 依赖图编排 (并行诊断域 + 显式依赖, 禁止单链线性)
"""
from .types import (
    FrozenBaziFact,
    MethodScope,
    UndeterminedReason,
    ZiPingDerivedFact,
    ZiPingJudgment,
    ZiPingTemporalOverlay,
    synthesize_output,
)
from .engine import EngineContext, Rule, RuleSet, JudgmentBuilder, EngineError
from .rules_loader import load_rule_file, load_rule_set, RuleLoadError
from .facts_adapter import build_frozen_fact, chart_to_context

__all__ = [
    "FrozenBaziFact",
    "MethodScope",
    "UndeterminedReason",
    "ZiPingDerivedFact",
    "ZiPingJudgment",
    "ZiPingTemporalOverlay",
    "synthesize_output",
    "EngineContext",
    "Rule",
    "RuleSet",
    "JudgmentBuilder",
    "EngineError",
    "load_rule_file",
    "load_rule_set",
    "RuleLoadError",
    "build_frozen_fact",
    "chart_to_context",
]
