
"""
Qintian Rules Subpackage — 钦天门规则子包 (P0-7-A 入口)

Public API:
    QintianRuleGraph       — 钦天 RuleGraph（独立类）
    QintianRuleMatch       — 单条匹配结果 dataclass
    QintianRuleGraphResult — 整体 match_all 结果
    QintianCombination     — detect 结果
    QintianJudgment        — judgment 结果
    QintianEvidence        — evidence binding
    make_qintian_rule_graph — 工厂函数

证据等级：production 检测器共 60 条（evidence grade=1×58 / grade=3×2）；
DRAFT 检测器 0 条（Z80-G 实测校准，原注释「5 条全部 grade=1」为陈旧值）。
"""

from __future__ import annotations

from .rule_graph import (
    QintianRuleGraph, QintianRuleMatch, QintianRuleGraphResult,
    make_qintian_rule_graph,
)
from .combinations import (
    QintianCombination,
    detect_all_production, detect_all_draft,
    PRODUCTION_DETECTORS, DRAFT_DETECTORS,
)
from .evidence import QintianEvidence, EVIDENCE_BINDINGS, DRAFT_BINDINGS
from .judgments import QintianJudgment, resolve_judgment, JUDGMENT_MAPPING


__all__ = [
    # 主入口
    "QintianRuleGraph",
    "QintianRuleMatch",
    "QintianRuleGraphResult",
    "make_qintian_rule_graph",
    # 数据类
    "QintianCombination",
    "QintianJudgment",
    "QintianEvidence",
    # 证据
    "EVIDENCE_BINDINGS",
    "DRAFT_BINDINGS",
    # 检测器
    "PRODUCTION_DETECTORS",
    "DRAFT_DETECTORS",
    "detect_all_production",
    "detect_all_draft",
    # 判定
    "resolve_judgment",
    "JUDGMENT_MAPPING",
]
