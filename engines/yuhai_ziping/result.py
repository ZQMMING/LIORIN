"""YHZP EngineResult（§B-3 Output 结构）。

facts 组：ten_god_facts / six_relative_facts / palace_facts /
basic_structure_facts / geju_candidates / relation_facts。
judgments / evidence / provenance 按 §70 统一结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared_types.enums import EngineStatus


@dataclass
class YHZPFactGroups:
    """§B-4 Fact Definitions（各 Fact 含 source_rule_id 可追溯）。"""

    ten_god_facts: List[Dict[str, Any]] = field(default_factory=list)
    six_relative_facts: List[Dict[str, Any]] = field(default_factory=list)
    palace_facts: List[Dict[str, Any]] = field(default_factory=list)
    basic_structure_facts: List[Dict[str, Any]] = field(default_factory=list)
    geju_candidates: List[Dict[str, Any]] = field(default_factory=list)
    relation_facts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "ten_god_facts": self.ten_god_facts,
            "six_relative_facts": self.six_relative_facts,
            "palace_facts": self.palace_facts,
            "basic_structure_facts": self.basic_structure_facts,
            "geju_candidates": self.geju_candidates,
            "relation_facts": self.relation_facts,
        }


@dataclass
class YHZPEngineResult:
    """§70 EngineResult 统一结构（YHZP 变体）。"""

    engine: str = "YUHAI_ZIPING"
    status: EngineStatus = EngineStatus.PASS
    canonical_input: Dict[str, str] = field(default_factory=dict)  # {"ref":..., "hash":...}
    facts: YHZPFactGroups = field(default_factory=YHZPFactGroups)
    judgments: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    divergences: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "status": self.status.value,
            "canonical_input": self.canonical_input,
            "facts": self.facts.to_dict(),
            "assertions": [],
            "judgments": self.judgments,
            "signals": [],
            "evidence": self.evidence,
            "provenance": self.provenance,
            "divergences": self.divergences,
            "metadata": self.metadata,
        }
