# -*- coding: utf-8 -*-
"""ZIPING V3.1 类型隔离层 (§51 REV-TYPE / §28 输出契约).

四层严格分型, 禁止混入同一 dict:
    FrozenBaziFact          排盘层事实 (只读, Bazi 产出)
    ZiPingDerivedFact      子平派生事实 (可验证, 可复算)
    ZiPingJudgment         判断 (必须携带 matched_rule_ids + evidence_refs
                           + method_scope + status, ARCH-008/009/013/014)
    ZiPingTemporalOverlay  时间叠加 (只叠加, 不修改 Natal, ARCH-017)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MethodScope(str, Enum):
    ZIPING_ZHENQUAN = "ziping_zhenquan"
    DI_TIAN_SUI = "di_tian_sui"
    QIONG_TONG_BAO_JIAN = "qiong_tong_bao_jian"
    YUAN_HAI_ZI_PING = "yuan_hai_zi_ping"
    SAN_MING_TONG_HUI = "san_ming_tong_hui"
    DISPUTED = "disputed"


class UndeterminedReason(str, Enum):
    """§77 REV-UNDETERMINED 六因 — 禁止裸 UNDETERMINED (ARCH-014)."""
    FACT_MISSING = "FACT_MISSING"
    RULE_MISSING = "RULE_MISSING"
    RULE_CONFLICT = "RULE_CONFLICT"
    METHOD_UNRESOLVED = "METHOD_UNRESOLVED"
    DEPENDENCY_UNRESOLVED = "DEPENDENCY_UNRESOLVED"
    EVIDENCE_UNVERIFIED = "EVIDENCE_UNVERIFIED"


@dataclass(frozen=True)
class FrozenBaziFact:
    """排盘层事实快照 (REV-TYPE-001). 只读; 子平不得修改或重算."""
    four_pillars: Tuple[Tuple[str, str], ...]   # (stem, branch) x4 年→时
    day_master: str
    month_branch: str
    hidden_stems: Dict[str, Dict[str, str]]     # pos -> {main,middle,residual,all}
    stem_ten_gods: Dict[str, str]               # pos -> 十神
    branch_ten_gods: Dict[str, Dict[str, str]]  # pos -> {main,middle,residual}
    stem_he_pairs: List[Tuple[str, str]]
    branch_relations: Dict[str, List[Any]]      # 合/冲/刑/三合/自刑/破 各 map
    twelve_growth: Dict[str, str]               # pos -> 十二长生 (中文)
    luck_pillars: List[Tuple[str, str]]         # 大运干支
    start_age: float
    gender: str
    # 可选确定性事实 (缺失 → 消费方 UNDETERMINED, 不补算)
    nayin: Optional[Dict[str, str]] = None
    shensha: Optional[Dict[str, Any]] = None
    kong_wang: Optional[Tuple[str, ...]] = None
    solar_term_crossing: Optional[bool] = None  # 节气交界事实 (Bazi 提供)

    @property
    def day_branch(self) -> str:
        return self.four_pillars[2][1]

    def pillar_stem(self, pos: str) -> str:
        idx = {"YEAR": 0, "MONTH": 1, "DAY": 2, "HOUR": 3}[pos]
        return self.four_pillars[idx][0]

    def pillar_branch(self, pos: str) -> str:
        idx = {"YEAR": 0, "MONTH": 1, "DAY": 2, "HOUR": 3}[pos]
        return self.four_pillars[idx][1]


@dataclass
class ZiPingDerivedFact:
    """子平派生事实容器 (REV-TYPE-002). 可验证可复算, 非判断."""
    states: Dict[str, Any] = field(default_factory=dict)


class ZiPingJudgment:
    """判断 (REV-TYPE-003). 构造即强制四要素, 缺一拒绝 (ARCH-008/009/013/014)."""

    def __init__(
        self,
        domain: str,
        state: str,
        matched_rule_ids: List[str],
        evidence_refs: List[str],
        method_scope: List[MethodScope],
        invalidated_by: Optional[List[str]] = None,
        reason: Optional[UndeterminedReason] = None,
        reason_detail: Optional[str] = None,
    ) -> None:
        if not matched_rule_ids:
            # 无规则命中 → 仅允许 UNDETERMINED 出口 (ARCH-012: 无显式规则匹配不得产结论)
            if state != "UNDETERMINED":
                raise ValueError(
                    f"ARCH-012 违反: domain={domain} state={state} 无 matched_rule_ids"
                )
            if reason is None:
                raise ValueError(
                    f"ARCH-014/§77 违反: UNDETERMINED 必须携带 reason (domain={domain})"
                )
        self.domain = domain
        self.state = state
        self.matched_rule_ids = list(matched_rule_ids)
        self.evidence_refs = list(evidence_refs)
        self.method_scope = [m.value for m in method_scope]
        self.invalidated_by = list(invalidated_by or [])
        self.reason = reason.value if reason else None
        self.reason_detail = reason_detail

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "state": self.state,
            "matched_rule_ids": self.matched_rule_ids,
            "evidence_refs": self.evidence_refs,
            "method_scope": self.method_scope,
            "invalidated_by": self.invalidated_by,
            "undetermined_reason": self.reason,
            "undetermined_detail": self.reason_detail,
        }


@dataclass
class ZiPingTemporalOverlay:
    """时间叠加层 (REV-TYPE-004 / §73): 只叠加, 永不改 Natal (ARCH-017)."""
    layer: str                     # LUCK / YEAR / MONTH / DAY
    created_by: str                # 规则/事件 ID
    modified_by: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    cleared_by: str = ""
    restored_to: str = "NATAL"
    payload: Dict[str, Any] = field(default_factory=dict)

    PRIORITY = {"NATAL": 0, "LUCK": 1, "YEAR": 2, "MONTH": 3, "DAY": 4}

    def merges_over(self, other: "ZiPingTemporalOverlay") -> "ZiPingTemporalOverlay":
        """低层叠高层 (REV-TEMPORAL-002): 高 priority 者胜出."""
        winner, loser = (self, other) if self.PRIORITY[self.layer] >= other.PRIORITY[other.layer] else (other, self)
        return ZiPingTemporalOverlay(
            layer=winner.layer,
            created_by=winner.created_by,
            modified_by=winner.modified_by + [loser.created_by],
            payload={**loser.payload, **winner.payload},
        )


def synthesize_output(
    judgments: List[ZiPingJudgment],
    undetermined: List[Tuple[str, UndeterminedReason, str]],
) -> Dict[str, Any]:
    """§28 输出契约统一出口."""
    return {
        "engine": "ZIPING_RULE_ENGINE",
        "version": "3.1",
        "judgments": [j.to_dict() for j in judgments],
        "undetermined": [
            {"domain": d, "reason": r.value, "detail": detail}
            for (d, r, detail) in undetermined
        ],
        "status": "DONE",
    }
