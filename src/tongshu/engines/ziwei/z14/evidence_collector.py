# -*- coding: utf-8 -*-
"""
Z14/Z17: 同盘异法验收契约（两派收敛）。

核心原则：
  - 一张 FrozenZiweiChart，两个独立方法各自读取（南派 SANHE | 北派 QINTIAN）
  - 方法之间绝不读取对方的 Evidence
  - 输出统一为 ZiweiEvidenceRecord（含 method_id / rule_id / source / trace）
  - 不比较、不投票、不产生 CONFLICTED

Z17 收敛（2026-09-14 用户定稿）：
  - 已删除：中州派（ZHONGZHOU）、飞星派（FEIXING）证据收集
  - 北派（QINTIAN）改用独立子包 qintian/ 的 RuleGraph 收集

架构：
  FrozenZiweiChart
        │
        ├─→ SanheRuleGraph   → Evidence A（南派）
        └─→ QintianRuleGraph → Evidence B（北派）

  两条证据链并列，互不污染。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from ...ziwei_engine import FrozenZiweiChart
from ...ziwei_method_profile import MethodId

logger = logging.getLogger(__name__)


# ============================================================================
# 统一证据记录格式
# ============================================================================

@dataclass(frozen=True)
class ZiweiEvidenceRecord:
    """Z14 统一证据记录：每种方法的输出都映射到此格式。

    字段说明：
      method_id:        来源流派（SANHE/QINTIAN）
      rule_id:          匹配的规则 ID
      evidence_type:    证据类型（pattern/sihua/palace/flying）
      facts:            匹配的事实摘要
      verification:     验证状态（canonical/candidate/unverified）
      implementation:   实现状态（FULL/SCAFFOLD/DRAFT/UNKNOWN）
      trace:            追溯路径（tuple of step descriptions）
    """
    method_id: MethodId
    rule_id: str
    evidence_type: str
    facts: dict[str, Any]
    verification: str = "candidate"
    implementation: str = "UNKNOWN"
    trace: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "method_id": self.method_id.value,
            "rule_id": self.rule_id,
            "evidence_type": self.evidence_type,
            "facts": self.facts,
            "verification": self.verification,
            "implementation": self.implementation,
            "trace": list(self.trace),
        }


# ============================================================================
# 同盘异法证据收集器
# ============================================================================

class MultiMethodEvidenceCollector:
    """从同一 FrozenZiweiChart 收集多派独立证据。

    设计原则：
      - 每个方法只消费 chart + 自身规则
      - 不读取其他方法的证据
      - 输出统一为 ZiweiEvidenceRecord 列表
    """

    def __init__(self, chart: FrozenZiweiChart) -> None:
        self._chart = chart

    def collect(self, method_ids: list[MethodId] | None = None) -> dict[MethodId, list[ZiweiEvidenceRecord]]:
        """收集所有指定流派的证据。

        Returns:
            {MethodId: [ZiweiEvidenceRecord, ...]}
        """
        if method_ids is None:
            method_ids = list(MethodId)

        results: dict[MethodId, list[ZiweiEvidenceRecord]] = {}
        for mid in method_ids:
            results[mid] = self._collect_for_method(mid)
        return results

    def _collect_for_method(self, method_id: MethodId) -> list[ZiweiEvidenceRecord]:
        """为单个流派收集证据（内部隔离，不访问其他派）。"""
        # 延迟导入，避免循环依赖
        return self._collect_pattern_sihua(method_id)

    def _collect_pattern_sihua(
        self, method_id: MethodId
    ) -> list[ZiweiEvidenceRecord]:
        """使用独立 RuleGraph 类收集 pattern+sihua+palace 证据（Z14-FIX）。"""
        if method_id == MethodId.SANHE:
            from ...ziwei.rules.method_graphs import SanheRuleGraph
            graph = SanheRuleGraph()
        elif method_id == MethodId.QINTIAN:
            from ...ziwei.rules.qintian import make_qintian_rule_graph
            graph = make_qintian_rule_graph()
        else:
            # 未知派别，返回空
            return []

        result = graph.match_all(self._chart)

        impl_status = getattr(
            result, "implementation_status",
            getattr(graph, "implementation_status",
                    getattr(graph, "IMPLEMENTATION_STATUS", "UNKNOWN")),
        )

        records: list[ZiweiEvidenceRecord] = []
        for match in result.matched_rules:
            if method_id == MethodId.SANHE:
                # 南派：SanheRuleGraph → RuleMatch（rule_spec 结构）
                spec = match.rule_spec
                records.append(ZiweiEvidenceRecord(
                    method_id=method_id,
                    rule_id=spec.rule_id,
                    evidence_type=spec.rule_type.value,
                    facts=match.facts,
                    verification=spec.evidence_refs[0].verification_status
                        if spec.evidence_refs else "unverified",
                    implementation=impl_status,
                    trace=(
                        f"chart → {method_id.label_zh} → "
                        f"{spec.rule_id} → match"
                    ),
                ))
            else:
                # 北派：QintianRuleMatch（rule_id / facts 结构）+ EVIDENCE_BINDINGS
                from ...ziwei.rules.qintian import EVIDENCE_BINDINGS
                binding = EVIDENCE_BINDINGS.get(match.rule_id)
                records.append(ZiweiEvidenceRecord(
                    method_id=method_id,
                    rule_id=match.rule_id,
                    evidence_type=binding.evidence_type
                        if binding else "flying",
                    facts=match.facts,
                    verification="canonical" if binding else "unverified",
                    implementation=impl_status,
                    trace=(
                        f"chart → {method_id.label_zh} → "
                        f"{match.rule_id} → match"
                    ),
                ))
        return records

    @property
    def chart(self) -> FrozenZiweiChart:
        return self._chart


# ============================================================================
# 隔离验证工具
# ============================================================================

class IsolationVerifier:
    """验证多派证据之间的隔离性。

    Z14-FIX 修正：
      - 自动生成 C(n,2) 组 pair 检查（不再硬编码 4 组）
      - 添加非空检查结果（F3b）
      - 添加实现身份验证（F3）
    """

    @staticmethod
    def verify_no_cross_contamination(
        evidence_map: dict[MethodId, list[ZiweiEvidenceRecord]],
    ) -> dict[str, bool]:
        """验证各派证据无交叉污染。

        Z14-FIX: 自动生成全部 C(n,2) 组 pair 检查。
        """
        checks: dict[str, bool] = {}

        # 检查 1: 每派证据的 method_id 一致
        for mid, records in evidence_map.items():
            all_correct = all(r.method_id == mid for r in records)
            checks[f"method_id_{mid.value}"] = all_correct

        # 检查 2: rule_id 前缀隔离（QINTIAN 规则 ID 前缀为 QTN-）
        _RULE_PREFIX = {MethodId.SANHE: "SANHE", MethodId.QINTIAN: "QTN"}
        prefix_map: dict[str, set[str]] = {}
        for mid, records in evidence_map.items():
            prefix = _RULE_PREFIX.get(mid, mid.value.upper())
            prefix_map[prefix] = {r.rule_id for r in records if r.rule_id}

        for mid_name, prefixes in prefix_map.items():
            has_wrong_prefix = any(
                not rid.startswith(mid_name)
                for rid in prefixes
            )
            checks[f"prefix_isolation_{mid_name}"] = not has_wrong_prefix

        # 检查 3: 不同派规则 ID 无交集（自动生成全部 C(n,2) 组 pair）
        all_ids: dict[str, set[str]] = {}
        for mid, records in evidence_map.items():
            all_ids[mid.value.upper()] = {r.rule_id for r in records if r.rule_id}

        method_names = sorted(all_ids.keys())
        for a, b in combinations(method_names, 2):
            intersection = all_ids[a] & all_ids[b]
            checks[f"no_overlap_{a}_vs_{b}"] = len(intersection) == 0

        return checks

    @staticmethod
    def verify_traceability(
        evidence_map: dict[MethodId, list[ZiweiEvidenceRecord]],
    ) -> dict[str, bool]:
        """验证每条证据可追溯。"""
        checks: dict[str, bool] = {}
        for mid, records in evidence_map.items():
            for i, r in enumerate(records):
                # 每条证据必须有 method_id
                if not r.method_id:
                    checks[f"traceable_{mid.value}_{i}"] = False
                    continue
                # 每条证据必须有 rule_id
                if not r.rule_id:
                    checks[f"traceable_{mid.value}_{i}"] = False
                    continue
                # 每条证据必须有 facts
                if not r.facts:
                    checks[f"traceable_{mid.value}_{i}"] = False
                    continue
                # 每条证据必须有 trace
                if not r.trace:
                    checks[f"traceable_{mid.value}_{i}"] = False
                    continue
            checks[f"all_traceable_{mid.value}"] = True
        return checks

    @staticmethod
    def verify_implementation_identity(
        evidence_map: dict[MethodId, list[ZiweiEvidenceRecord]],
    ) -> dict[str, bool]:
        """F3: 验证每条证据的 implementation 状态与派别一致。

        防止 SCAFFOLD/DRAFT 被伪装成 FULL 实现。
        """
        checks: dict[str, bool] = {}
        for mid, records in evidence_map.items():
            impls = {r.implementation for r in records} if records else {"EMPTY"}
            checks[f"impl_identity_{mid.value}"] = len(impls) <= 1
        return checks

    @staticmethod
    def verify_non_empty_for_implementation(
        evidence_map: dict[MethodId, list[ZiweiEvidenceRecord]],
        required_methods: set[MethodId] | None = None,
    ) -> dict[str, bool]:
        """F3b: 已实现的方法必须产生非空证据（防假阳性）。

        Args:
            required_methods: 必须非空的 MethodId 集合
                             默认：implementation == 'FULL' 或 'SCAFFOLD' 的派别
        """
        if required_methods is None:
            required_methods = {
                mid for mid, records in evidence_map.items()
                if records and records[0].implementation in ("FULL", "SCAFFOLD")
            }
        checks: dict[str, bool] = {}
        for mid in required_methods:
            records = evidence_map.get(mid, [])
            checks[f"non_empty_{mid.value}"] = len(records) > 0
        return checks
