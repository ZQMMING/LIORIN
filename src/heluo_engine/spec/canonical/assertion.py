"""
P1.2-A — CanonicalAssertion Contract (V13 §三)

设计原则：
  1. direction 在此层才产生，且必须由 Authorized Assertion Rule 授权
  2. 禁止 MappingLayer 自由决定 direction
  3. evidence 字段建立完整追溯链：Assertion → SemanticAtom → EngineEvidence
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class AssertionDirection(str, enum.Enum):
    """V13 冻结的方向枚举（仅 3 值）"""

    SUPPORTIVE = "supportive"  # 支持性
    CAUTION = "caution"  # 警示性
    NEUTRAL = "neutral"  # 中性


@dataclass(frozen=True)
class EvidenceRef:
    """EngineEvidence 的结构化引用，禁止开放 dict。

    最小字段约束：必须包含 evidence_id, engine, value, source_rule_ref, source_field。
    """
    evidence_id: str
    engine: str
    value: Any
    source_rule_ref: str
    source_field: Optional[str] = None
    temporal_scope: Optional[str] = None
    rule_id: Optional[str] = None
    calculation_version: Optional[str] = None
    contract_version: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in {
            "evidence_id": self.evidence_id,
            "engine": self.engine,
            "value": self.value,
            "source_rule_ref": self.source_rule_ref,
            "source_field": self.source_field,
            "temporal_scope": self.temporal_scope,
            "rule_id": self.rule_id,
            "calculation_version": self.calculation_version,
            "contract_version": self.contract_version,
        }.items() if v is not None}


@dataclass(frozen=True)
class CanonicalAssertion:
    """V13 Canonical Assertion 合约。

    direction 在此层才产生，且必须由 Authorized Assertion Rule 授权。
    """

    assertion_id: str
    subject: str  # case_id
    domain: str  # CAREER / FINANCE / RELATIONSHIP / FAMILY / SOCIAL / GROWTH / HEALTH / DECISION
    semantic: str  # 语义原子标签（如 OUTPUT_ACTIVATION）
    direction: AssertionDirection  # supportive / caution / neutral
    temporal_scope: str  # birth / year / month / day / hour
    source_engine: str  # ZI_PING / BLIND_SCHOOL / ...
    source_rule: str  # rule_id
    authorized_rule_id: str  # 授权此 direction 的断言规则 ID
    evidence: EvidenceRef  # 追溯到 EngineEvidence 的结构化引用

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSON 存储/传输）。"""
        return {
            "assertion_id": self.assertion_id,
            "subject": self.subject,
            "domain": self.domain,
            "semantic": self.semantic,
            "direction": self.direction.value,
            "temporal_scope": self.temporal_scope,
            "source_engine": self.source_engine,
            "source_rule": self.source_rule,
            "authorized_rule_id": self.authorized_rule_id,
            "evidence": self.evidence.to_dict(),
        }
