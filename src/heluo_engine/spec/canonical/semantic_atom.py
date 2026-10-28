"""
P1.2-A — SemanticAtom Contract (V13 §二)

设计原则：
  1. 查表产物：SemanticAtom 是 EngineEvidence 经过语义知识库查表后的产物
  2. 无方向：SemanticAtom 不产生 direction，仅携带语义键（semantic_keys）
  3. 领域候选：通过 domain_candidates 提供候选人生维度，不预分配 domain
  4. 溯源到 EngineEvidence：每个 SemanticAtom 必须保留 evidence_ref
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .engine_evidence import EngineName


@dataclass(frozen=True)
class SemanticAtom:
    """语义原子层数据合约。从 EngineEvidence 经知识库查表后生成。

    禁止字段：direction, polarity
    """

    # 身份
    atom_id: str  # 如 "TEN_GOD_SHANG_GUAN", "ZW_STAR_ZIWEI"
    engine: EngineName  # 来源引擎
    evidence_ref: str  # 追溯到 EngineEvidence.evidence_id

    # 语义内容（无方向）
    semantic_keys: List[str] = field(default_factory=list)  # 如 ["EXPRESSION", "INNOVATION", ...]
    domain_candidates: List[str] = field(default_factory=list)  # 如 ["CAREER", "GROWTH", "DECISION"]

    # 附加元数据
    label_zh: str = ""  # 中文标签（如 "伤官"）
    category: str = ""  # 类别（如 "TEN_GOD", "FIVE_ELEMENT", "ZIWEI_MAJOR"）
    guidance_keys: List[str] = field(default_factory=list)  # 行为指引键

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSON 存储/传输）。"""
        return {
            "atom_id": self.atom_id,
            "engine": self.engine.value,
            "evidence_ref": self.evidence_ref,
            "semantic_keys": list(self.semantic_keys),
            "domain_candidates": list(self.domain_candidates),
            "label_zh": self.label_zh,
            "category": self.category,
            "guidance_keys": list(self.guidance_keys),
        }
