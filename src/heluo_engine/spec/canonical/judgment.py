"""
P1.2-A — Judgment Contract (V13 §四)

设计原则：
  1. EvidenceCoverage ≠ Judgment：前者是横向组织结构，后者是授权结论
  2. Judgment 需经原典授权规则，禁止"聚合成群即判断"
  3. EvidenceCoverage 只做结构性组织，不做方向比较
  4. 遵循 V13 §二：互补不比较，不投票、不评分、不多数决、不加权
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class EvidenceCoverage:
    """证据覆盖面统计，替代 CrossAnalyzer。

    只做结构性组织：记录哪些 Assertion 存在，来自哪些引擎。
    不做方向比较，不产生 Judgment。
    """

    domain: str
    semantic: str
    evidence_count: int  # 证据数量（非投票）
    source_engines: List[str]  # 哪些引擎提供了证据
    evidence_types: List[str]  # 哪些类型的证据
    assertion_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSON 存储/传输）。"""
        return {
            "domain": self.domain,
            "semantic": self.semantic,
            "evidence_count": self.evidence_count,
            "source_engines": list(self.source_engines),
            "evidence_types": list(self.evidence_types),
            "assertion_ids": list(self.assertion_ids),
        }


@dataclass(frozen=True)
class Judgment:
    """V13 结构化判断结论。

    Judgment 必须由 Authorized Judgment Rule 授权产生。
    不产生新方向，仅引用已有 Assertion 的 direction。
    """

    judgment_id: str
    domain: str
    semantic: str
    evidence_coverage: EvidenceCoverage
    authorized_by: str  # 授权规则 ID
    supporting_assertions: List[str] = field(default_factory=list)  # assertion_id 列表

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSON 存储/传输）。"""
        return {
            "judgment_id": self.judgment_id,
            "domain": self.domain,
            "semantic": self.semantic,
            "evidence_coverage": self.evidence_coverage.to_dict(),
            "authorized_by": self.authorized_by,
            "supporting_assertions": list(self.supporting_assertions),
        }
