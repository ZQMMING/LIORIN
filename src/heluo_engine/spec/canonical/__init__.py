"""
P1.2-A Contract Layer — Canonical Data Structures

V13 统一合约层：EngineEvidence → SemanticAtom → CanonicalAssertion → EvidenceCoverage → Judgment

Contract:
  - 所有 dataclass 使用 frozen=True（不可变）
  - 所有枚举继承 str, enum.Enum（方便 JSON 序列化）
  - evidence_id 与 rule_id 分离（V2 修正）
  - direction 仅在 Assertion 层由授权规则产生
  - judgment 需经授权规则，禁止聚合即判断
"""
from __future__ import annotations

from .engine_evidence import EngineEvidence, EngineName, TemporalScope
from .semantic_atom import SemanticAtom
from .assertion import CanonicalAssertion, AssertionDirection, EvidenceRef
from .judgment import EvidenceCoverage, Judgment

__all__ = [
    "EngineEvidence",
    "EngineName",
    "TemporalScope",
    "SemanticAtom",
    "CanonicalAssertion",
    "AssertionDirection",
    "EvidenceRef",
    "EvidenceCoverage",
    "Judgment",
]
