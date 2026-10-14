"""
MultiMethodSignal — 紫微两派 RuleGraph 集成器（Z17 收敛）

架构收敛（2026-09-14 用户定稿）：
  整个紫微系统 = 南派（倪海厦/三合） + 北派（钦天），两派平行输出。
  - 共用层：排盘（FrozenZiweiChart）两派共用一张盘，不复制计算。
  - 平行输出：南派（SanheRuleGraph + 倪师断言）| 北派（QintianRuleGraph），
    MethodBundle 各自命名空间隔离，不做"投票"合并。
  - 已删除：中州派（zhongzhou/ 子包）、飞星派（feixing/ 子包）及其骨架类。

严格工程边界 (P0-8-A 继承):
  ❌ 不改 BaseZiweiRuleGraph
  ❌ 不改 FrozenZiweiChart / ZiweiChart
  ❌ 不改各派 RuleGraph 子类 (Sanhe / Qintian)
  ❌ 不写"判断/解释/强旺衰" - 那是"解"层的事
  ✅ 仅做"派别独立 compute + 适配器翻译 + 合并 + 命名空间隔离"

架构:
  chart (FrozenZiweiChart) → MultiMethodSignal.compute(chart)
                            ├→ SanheRuleGraph.match_all(chart)  → MethodBundle (南派)
                            └→ QintianRuleGraph.match_all(chart) → MethodBundle (北派)
                          ↓
                          MultiMethodSignal (2 MethodBundles + 跨派共识)

派别 API 差异适配:
  - SanheRuleGraph:
      * match_all(chart) - 无 resolver
      * RuleMatchResult.matched_rules = RuleMatch(rule_spec + facts + qualified + qualifier)
      * rule_spec.rule_id 如 "SANHE-PATTERN-杀破狼" / "SANHE-SIHUA-癸" / "SANHE-PALACE-命宫"
  - QintianRuleGraph:
      * match_all(chart) - 无 resolver
      * 有 graph_id() method
      * QintianRuleMatch = rule_id + evidence_grade + semantic_summary + judgment_strength
      * QintianRuleGraphResult 有 unmatched_production_rules + draft_detected
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .method_graphs import SanheRuleGraph
from .qintian import make_qintian_rule_graph
from .rule_graph import PATTERN_DEFS as _PATTERN_DEFS_SRC


@dataclass
class MethodMatch:
    """单条派别内规则匹配 (派别无关通用结构)"""
    rule_id: str
    evidence_grade: int
    semantic_summary: str
    facts: Dict[str, Any] = field(default_factory=dict)
    judgment_strength: str = "neutral"  # "strong" / "moderate" / "weak" / "neutral"
    judgment_text: str = ""  # 辨层判定的古典字面描述（解层消费用）


@dataclass
class MethodBundle:
    """单派别 RuleGraph 计算结果 (命名空间隔离)"""
    method_id: str                 # "SANHE" / "QINTIAN"
    graph_id: str                  # "SANHE-Z12" 等
    profile: str                   # PROFILE 字串
    implementation_status: str     # "PRODUCTION" / "PARTIAL" / "DRAFT" / "SCAFFOLD" / "FAIL"
    matched_rules: List[MethodMatch] = field(default_factory=list)
    unmatched_production_rules: List[str] = field(default_factory=list)
    draft_detected: List[str] = field(default_factory=list)
    rule_count: int = 0
    evidence_bindings: Dict[str, Dict] = field(default_factory=dict)
    compute_error: Optional[str] = None


@dataclass
class MultiMethodSignal:
    """多派别聚合信号 - 上游"辨"层的输入"""
    chart_id: str
    bundles: Dict[str, MethodBundle] = field(default_factory=dict)
    cross_method_consensus: List[str] = field(default_factory=list)
    total_matched_rules: int = 0
    total_unmatched_production: int = 0
    compute_status: str = "OK"


# ----- 派别适配器 -----

def _wrap_sanhe(graph: SanheRuleGraph, chart) -> MethodBundle:
    """三合派（南派/倪海厦）RuleGraph → MethodBundle (Z17 接线)

    Z17 修复：此前 _wrap_sanhe(None, chart) 硬编码返回空 SCAFFOLD，
    导致南派 63 条规则从未进入多派输出。现实例化 SanheRuleGraph 并
    真实匹配，命中结果进入 MethodBundle。
    """
    graph_id = "SANHE-Z12"
    profile = "SANHE-NIHAI"
    try:
        result = graph.match_all(chart)

        matches: List[MethodMatch] = []
        for rm in result.matched_rules:
            spec = rm.rule_spec
            conf = getattr(spec.confidence, "value", "medium")
            matches.append(MethodMatch(
                rule_id=spec.rule_id,
                evidence_grade=(
                    2 if conf == "high" else
                    1 if conf == "medium" else 0
                ),
                semantic_summary=(
                    rm.facts.get("pattern_name", "")
                    or f"{spec.condition.get('palace', '')}宫"
                ),
                facts=dict(rm.facts),
                judgment_strength="moderate" if rm.qualified else "weak",
                judgment_text=spec.operation.get("description", "")
                if isinstance(spec.operation, dict) else "",
            ))

        # 推导 unmatched：SANHE 总规则数 - 命中数
        all_rule_ids = {f"SANHE-{rid}" for rid in (
            [f"PATTERN-{p[0]}" for p in _PATTERN_IDS]
        )}
        matched_ids = {m.rule_id for m in matches}
        unmatched = sorted(all_rule_ids - matched_ids)

        return MethodBundle(
            method_id="SANHE",
            graph_id=graph_id,
            profile=profile,
            implementation_status="FULL",
            matched_rules=matches,
            unmatched_production_rules=unmatched,
            draft_detected=[],
            rule_count=graph.rule_count,
            evidence_bindings={},
        )
    except Exception as e:
        return MethodBundle(
            method_id="SANHE",
            graph_id=graph_id,
            profile=profile,
            implementation_status="FAIL",
            compute_error=f"{type(e).__name__}: {e}",
        )


# 格局名索引（用于推导 unmatched 的 SANHE-PATTERN-* 全集）
#
# Z80-F（2026-10-14）：**由 rule_graph.PATTERN_DEFS 直接派生**，不再硬编码。
#   此前硬编码 41 条（自述「与 PATTERN_DEFS 同名同步」），而 PATTERN_DEFS
#   实为 40 条，多出幻影「杀狼同宫」（DEFS 中只有「破狼同宫」）→
#   使 SANHE-PATTERN-杀狼同宫 恒被判为 unmatched，污染未匹配统计。
#   派生写法从根上杜绝此类失配。
_PATTERN_IDS = [(d[0],) for d in _PATTERN_DEFS_SRC]


def _wrap_qintian(graph, chart) -> MethodBundle:
    """钦天派（北派）RuleGraph → MethodBundle (钦天 API 完整, 几乎无需适配)"""
    try:
        result = graph.match_all(chart)

        matches: List[MethodMatch] = []
        for qm in result.matched_rules:
            matches.append(MethodMatch(
                rule_id=qm.rule_id,
                evidence_grade=qm.evidence_grade,
                semantic_summary=qm.semantic_summary,
                facts=dict(qm.facts),
                judgment_strength=qm.judgment_strength,
            ))

        # Qintian evidence bindings
        from .qintian.evidence import EVIDENCE_BINDINGS as QTN_BINDINGS
        ev_bindings = {
            rid: {"name": getattr(ev, "title", getattr(ev, "name", rid)), "grade": ev.grade}
            for rid, ev in QTN_BINDINGS.items()
        }

        return MethodBundle(
            method_id="QINTIAN",
            graph_id=graph.graph_id(),
            profile=getattr(graph, "PROFILE", "QINTIAN-QINTIAN_SIHA-PRODUCTION-A"),
            implementation_status=result.implementation_status,
            matched_rules=matches,
            unmatched_production_rules=list(result.unmatched_production_rules),
            draft_detected=list(result.draft_detected),
            rule_count=graph.rule_count(),
            evidence_bindings=ev_bindings,
        )
    except Exception as e:
        return MethodBundle(
            method_id="QINTIAN",
            graph_id=getattr(graph, "graph_id", lambda: "QINTIAN-UNKNOWN")(),
            profile=getattr(graph, "PROFILE", "UNKNOWN"),
            implementation_status="FAIL",
            compute_error=f"{type(e).__name__}: {e}",
        )


# ----- 主入口 -----

def compute_multi_method_signals(
    chart,
    *,
    include_sanhe: bool = True,
) -> MultiMethodSignal:
    """两派并行 compute + 适配 + 聚合（南派=三合 | 北派=钦天）

    Args:
        chart: FrozenZiweiChart / ZiweiChart / 任意 duck-typed chart
            需有 .palaces (dict, 钦天要), .palace_stems (钦天要), .flying_transforms (钦天要), .birth_year
        include_sanhe: 是否包含三合（南派）匹配

    Returns:
        MultiMethodSignal with 2 MethodBundles（SANHE / QINTIAN）
    """
    chart_id = f"chart-{getattr(chart, 'birth_year', 'unknown')}-{id(chart) & 0xFFFF:04x}"

    bundles: Dict[str, MethodBundle] = {}

    # 南派（三合/倪海厦）
    if include_sanhe:
        bundles["SANHE"] = _wrap_sanhe(SanheRuleGraph(), chart)

    # 北派（钦天）
    bundles["QINTIAN"] = _wrap_qintian(make_qintian_rule_graph(), chart)

    # 跨派别共识检测
    consensus = _detect_cross_method_consensus(bundles)

    # 聚合
    total_matched = sum(len(b.matched_rules) for b in bundles.values())
    total_unmatched = sum(len(b.unmatched_production_rules) for b in bundles.values())

    fail_count = sum(1 for b in bundles.values() if b.implementation_status == "FAIL")
    if fail_count == 0:
        compute_status = "OK"
    elif fail_count == len(bundles):
        compute_status = "FAIL"
    else:
        compute_status = "PARTIAL"

    return MultiMethodSignal(
        chart_id=chart_id,
        bundles=bundles,
        cross_method_consensus=consensus,
        total_matched_rules=total_matched,
        total_unmatched_production=total_unmatched,
        compute_status=compute_status,
    )


def _detect_cross_method_consensus(bundles: Dict[str, MethodBundle]) -> List[str]:
    """检测跨派别共识: 同一 fact 字段在 ≥2 派命中且值一致"""
    consensus = []
    fact_key_values_by_method: Dict[str, Dict[str, set]] = {}
    for mid, b in bundles.items():
        fact_key_values_by_method[mid] = {}
        for m in b.matched_rules:
            for k, v in m.facts.items():
                if isinstance(v, (str, int, float, bool)):
                    fact_key_values_by_method[mid].setdefault(k, set()).add(v)
    if len(fact_key_values_by_method) < 2:
        return consensus
    method_ids = list(fact_key_values_by_method.keys())
    first, second = method_ids[0], method_ids[1]
    for key in fact_key_values_by_method[first]:
        if key in fact_key_values_by_method[second]:
            common = fact_key_values_by_method[first][key] & fact_key_values_by_method[second][key]
            if common:
                consensus.append(f"{key}={sorted(common)[0]}")
    return consensus
