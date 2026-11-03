"""通用 EngineResult（§70 统一结构 / §B-3 六组 facts / §B-4 Fact Definitions）。

与 yuhai_ziping/result.py 的 YHZPEngineResult 结构完全一致；
engine 字段由 FactsBuilder(engine=...) 注入对应 ENGINE_ID。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from shared_types.enums import EngineStatus


@dataclass
class FactGroups:
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
class EngineResult:
    """§70 EngineResult 统一结构（引擎族通用）。"""

    engine: str
    status: EngineStatus = EngineStatus.PASS
    canonical_input: Dict[str, str] = field(default_factory=dict)  # {"ref":..., "hash":...}
    facts: FactGroups = field(default_factory=FactGroups)
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
