"""Rule 数据模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class Rule:
    """盲派规则，支持 requires + invalidates。"""
    rule_id: str
    school: str  # "BLIND_SCHOOL"
    requires: List[str]  # 前置条件：规则ID 或 "stem:JIA" / "branch:WU" / "tg:正财" 等
    invalidates: List[str]  # 反例排除：其他规则的 ID
    relations: List[str] = field(default_factory=list)  # 关联规则ID
    judgment: str = ""  # 判断结论
    classic: str = ""  # 原著出处
    source_verified: bool = False  # 是否已核验原著
    evidence_refs: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.rule_id

    def is_invalidated_by(self, other_rule_ids: Set[str]) -> bool:
        """检查本规则是否被 given rule IDs 中的反例排除。"""
        return bool(set(self.invalidates) & other_rule_ids)


@dataclass
class MatchContext:
    """规则匹配的上下文，包含当前八字状态。"""
    stems: Dict[str, str]  # {pillar: stem} e.g. {"year": "JIA", ...}
    branches: Dict[str, str]  # {pillar: branch}
    hidden_stems: Dict[str, List[str]]  # {pillar: [hidden_stems...]}
    ten_gods: Dict[str, str]  # {stem: ten_god}
    ti_branches: Set[str] = field(default_factory=set)
    yong_branches: Set[str] = field(default_factory=set)
    ti_stems: List[str] = field(default_factory=list)
    yong_stems: List[str] = field(default_factory=list)
    zuo_gong_methods: List[str] = field(default_factory=list)  # 做功方式列表
