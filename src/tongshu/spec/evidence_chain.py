"""
V-Validation V1.2 — Evidence Chain Schema (Schema 7)

Contract:
  Five-level chain: SOURCE → PASSAGE → CLAIM → EVIDENCE → SIGNAL
  LEVEL_1~4 only for formal Claim/Passage/Evidence nodes.
  LEVEL_5 is Interpretive Supplement ONLY, never enters canonical chain.
  CLAIM.created_by MUST be HUMAN or RULE_ENGINE, NEVER LLM.
  CLAIM_DRAFT allows LLM but must go through PENDING_REVIEW → APPROVED/REJECTED.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Optional


# ─── EvidenceLevel (5 levels, LEVEL_5 restricted) ────────────────────────────


class EvidenceLevel(enum.Enum):
    """Five-level evidence hierarchy (V1.2).

    LEVEL_5 is Interpretive Supplement ONLY.
    Formal CLAIM / PASSAGE / EVIDENCE nodes MUST use LEVEL_1 through LEVEL_4.
    """

    LEVEL_1 = "LEVEL_1"   # 经典原点  (《易经》《黄历》原文)
    LEVEL_2 = "LEVEL_2"   # 历史记载  (传记、史书)
    LEVEL_3 = "LEVEL_3"   # 注疏传统  (王弼注、程颐《易程传》等)
    LEVEL_4 = "LEVEL_4"   # 结构推导  (卦体、爻位、互体)
    LEVEL_5 = "LEVEL_5"   # 现代映射  (Interpretive Supplement only)

    @classmethod
    def formal_levels(cls) -> List["EvidenceLevel"]:
        """Levels permitted in formal chain (excluding LEVEL_5)."""
        return [cls.LEVEL_1, cls.LEVEL_2, cls.LEVEL_3, cls.LEVEL_4]

    def is_formal(self) -> bool:
        return self in self.formal_levels()


# ─── VerificationStatus ───────────────────────────────────────────────────────


class VerificationStatus(enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    INVALID = "INVALID"


# ─── ClaimType ────────────────────────────────────────────────────────────────


class ClaimType(enum.Enum):
    DESCRIBE_STATE = "DESCRIBE_STATE"
    PREDICT_TENDENCY = "PREDICT_TENDENCY"
    WARN_RISK = "WARN_RISK"
    RECOMMEND_ACTION = "RECOMMEND_ACTION"


# ─── AllowedClaimCreators (contract enforcement) ──────────────────────────────


ALLOWED_CLAIM_CREATORS = frozenset({"HUMAN", "RULE_ENGINE"})
ALLOWED_CLAIM_DRAFT_CREATORS = frozenset({"HUMAN", "LLM", "RULE_ENGINE"})


# ─── SOURCE node ──────────────────────────────────────────────────────────────


@dataclass
class Source:
    source_id: str
    source_type: str    # "CLASSICAL" | "HISTORICAL" | "COMMENTARY"
    title: str
    edition: str
    verified: bool = False
    cross_verify_sources: List[str] = field(default_factory=list)


# ─── PASSAGE node ─────────────────────────────────────────────────────────────


@dataclass
class Passage:
    passage_id: str
    source_id: str          # FK → Source.source_id
    text: str
    context: str = ""
    ocr_risk: Optional[str] = None
    interpolation_risk: Optional[str] = None
    fragment_status: Optional[str] = None
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_1
    verified: bool = False

    def validate_level(self) -> List[str]:
        errors: List[str] = []
        if not self.evidence_level.is_formal():
            errors.append(f"Passage evidence_level={self.evidence_level.value} must be LEVEL_1–4")
        return errors


# ─── CLAIM node (LLM cannot directly create formal claims) ────────────────────


@dataclass
class Claim:
    claim_id: str
    passage_id: str         # FK → Passage.passage_id
    claim_text: str
    claim_type: ClaimType
    evidence_level: EvidenceLevel  # MUST be LEVEL_1–4
    support_score: float = 0.0    # 0.0–1.0
    created_by: str = "HUMAN"     # MUST be in ALLOWED_CLAIM_CREATORS
    created_at: str = ""          # ISO8601
    verified: bool = False
    review_status: str = "APPROVED"  # PENDING_REVIEW | APPROVED | REJECTED

    def validate(self) -> List[str]:
        errors: List[str] = []
        if self.created_by not in ALLOWED_CLAIM_CREATORS:
            errors.append(
                f"Claim.created_by={self.created_by!r} not in {ALLOWED_CLAIM_CREATORS}"
            )
        if not self.evidence_level.is_formal():
            errors.append(
                f"Claim.evidence_level={self.evidence_level.value} must be LEVEL_1–4"
            )
        return errors


# ─── CLAIM_DRAFT (LLM intermediate, needs human review) ──────────────────────


@dataclass
class ClaimDraft:
    """LLM-generated draft claim — must go through review before becoming Claim."""

    draft_id: str
    passage_id: str
    claim_text: str
    claim_type: ClaimType
    created_by: str   # can be "LLM"
    review_status: str = "PENDING_REVIEW"  # PENDING_REVIEW | APPROVED | REJECTED

    def validate_creator(self) -> List[str]:
        errors: List[str] = []
        if self.created_by not in ALLOWED_CLAIM_DRAFT_CREATORS:
            errors.append(f"ClaimDraft.created_by={self.created_by!r} not allowed")
        return errors


# ─── EVIDENCE node (formal chain, LEVEL_5 forbidden) ─────────────────────────


@dataclass
class Evidence:
    evidence_id: str
    claim_id: str         # FK → Claim.claim_id
    evidence_level: EvidenceLevel  # MUST be LEVEL_1–4
    source_id: str        # FK → Source.source_id
    passage_id: str       # FK → Passage.passage_id (nullable, Source-only trace OK)
    verification_status: VerificationStatus = VerificationStatus.PENDING
    cross_verify_refs: List[str] = field(default_factory=list)
    created_at: str = ""

    def validate_level(self) -> List[str]:
        errors: List[str] = []
        if not self.evidence_level.is_formal():
            errors.append(
                f"Evidence.evidence_level={self.evidence_level.value} must be LEVEL_1–4"
            )
        return errors


# ─── EvidenceChain integrity validator ────────────────────────────────────────


class EvidenceChainIntegrityError(Exception):
    """Raised when evidence chain linkage is broken."""


def validate_chain(
    sources: dict[str, Source],
    passages: dict[str, Passage],
    claims: dict[str, Claim],
    evidences: dict[str, Evidence],
) -> List[str]:
    """Return list of integrity violations (empty = chain is intact)."""
    errors: List[str] = []

    for pid, p in passages.items():
        if p.source_id not in sources:
            errors.append(f"Passage {pid} references missing Source {p.source_id}")
        for err in p.validate_level():
            errors.append(f"Passage {pid}: {err}")

    for cid, c in claims.items():
        if c.passage_id not in passages:
            errors.append(f"Claim {cid} references missing Passage {c.passage_id}")
        for err in c.validate():
            errors.append(f"Claim {cid}: {err}")

    for eid, e in evidences.items():
        if e.claim_id not in claims:
            errors.append(f"Evidence {eid} references missing Claim {e.claim_id}")
        if e.source_id not in sources:
            errors.append(f"Evidence {eid} references missing Source {e.source_id}")
        for err in e.validate_level():
            errors.append(f"Evidence {eid}: {err}")

    return errors
