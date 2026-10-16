"""
V-Validation V1.2 — Event Ontology Schema (Schema 3)

Contract:
  Single-Parent Domain: each Event Type belongs to EXACTLY ONE Domain.
  4 Domains, 17 Event Types, 5 Directions, 3 Temporal Granularities.
  Matching Policy is SEPARATE — NOT embedded here.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Dict, List


# ─── Domain (4 values) ────────────────────────────────────────────────────────


class Domain(enum.Enum):
    """V1.2 Single-Parent Domain enum — exactly 4 values."""

    EDUCATION = "EDUCATION"      # 学业、考试、学位晋升
    CAREER = "CAREER"            # 职场、晋升、离职、收入变化
    FAMILY = "FAMILY"            # 婚姻、生育、家庭关系变化
    LIFE_EVENT = "LIFE_EVENT"    # 搬迁、健康、法律等人生重大事件


# ─── Direction (5 values) ─────────────────────────────────────────────────────


class EventDirection(enum.Enum):
    """Event direction enum — exactly 5 values."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CHANGE = "CHANGE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


# ─── TemporalGranularity (3 values) ───────────────────────────────────────────


class TemporalGranularity(enum.Enum):
    """Time granularity enum — exactly 3 values."""

    YEARLY = "YEARLY"
    MONTHLY = "MONTHLY"
    DAILY = "DAILY"


# ─── EventDefinition (frozen dataclass) ──────────────────────────────────────


@dataclass(frozen=True)
class EventDefinition:
    """A single Event Type definition in V1.2 Ontology."""

    id: str
    domain: Domain
    direction: EventDirection
    granularity: TemporalGranularity
    signal_pattern: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain.value,
            "direction": self.direction.value,
            "granularity": self.granularity.value,
            "signal_pattern": self.signal_pattern,
        }


# ─── V1.2 Frozen Event Types (17 total) ──────────────────────────────────────
# See V_VALIDATION_SPEC_V1.2.md §3 for the authoritative source.

EVENT_TYPES: List[EventDefinition] = [
    # EDUCATION (4)
    EventDefinition("EXAM",               Domain.EDUCATION, EventDirection.NEUTRAL,  TemporalGranularity.MONTHLY),
    EventDefinition("ADMISSION",           Domain.EDUCATION, EventDirection.POSITIVE, TemporalGranularity.YEARLY),
    EventDefinition("GRADUATION",          Domain.EDUCATION, EventDirection.POSITIVE, TemporalGranularity.YEARLY),
    EventDefinition("DEGREE",              Domain.EDUCATION, EventDirection.POSITIVE, TemporalGranularity.YEARLY),

    # CAREER (5)
    EventDefinition("PROMOTION",           Domain.CAREER,    EventDirection.POSITIVE, TemporalGranularity.YEARLY),
    EventDefinition("JOB_CHANGE",          Domain.CAREER,    EventDirection.CHANGE,   TemporalGranularity.YEARLY),
    EventDefinition("RESIGNATION",         Domain.CAREER,    EventDirection.CHANGE,   TemporalGranularity.YEARLY),
    EventDefinition("DEMOTION",            Domain.CAREER,    EventDirection.NEGATIVE, TemporalGranularity.YEARLY),
    EventDefinition("MAJOR_INCOME",        Domain.CAREER,    EventDirection.POSITIVE, TemporalGranularity.YEARLY),

    # FAMILY (5)
    EventDefinition("MARRIAGE",            Domain.FAMILY,    EventDirection.POSITIVE, TemporalGranularity.YEARLY),
    EventDefinition("DIVORCE",             Domain.FAMILY,    EventDirection.NEGATIVE, TemporalGranularity.YEARLY),
    EventDefinition("CHILD_BIRTH",         Domain.FAMILY,    EventDirection.POSITIVE, TemporalGranularity.YEARLY),
    EventDefinition("PARENT_DEATH",        Domain.FAMILY,    EventDirection.NEGATIVE, TemporalGranularity.YEARLY),
    EventDefinition("FAMILY_HARMONY",      Domain.FAMILY,    EventDirection.POSITIVE, TemporalGranularity.YEARLY),

    # LIFE_EVENT (3)
    EventDefinition("RELOCATION",          Domain.LIFE_EVENT,EventDirection.CHANGE,   TemporalGranularity.YEARLY),
    EventDefinition("HEALTH_ISSUE",        Domain.LIFE_EVENT,EventDirection.NEGATIVE, TemporalGranularity.YEARLY),
    EventDefinition("LEGAL_ISSUE",         Domain.LIFE_EVENT,EventDirection.NEGATIVE, TemporalGranularity.YEARLY),
]


# O(1) lookup tables
EVENT_TYPE_BY_ID: Dict[str, EventDefinition] = {e.id: e for e in EVENT_TYPES}
DOMAIN_BY_ID: Dict[str, Domain] = {e.id: e.domain for e in EVENT_TYPES}
DIRECTION_BY_ID: Dict[str, EventDirection] = {e.id: e.direction for e in EVENT_TYPES}


# ─── Validation invariant checks ─────────────────────────────────────────────


def validate_ontology_invariants() -> List[str]:
    """Return list of invariant violations (empty = all pass)."""
    errors: List[str] = []

    if len(EVENT_TYPES) != 17:
        errors.append(f"expected 17 EVENT_TYPES, got {len(EVENT_TYPES)}")

    ids = [e.id for e in EVENT_TYPES]
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate EVENT_TYPE ids: {ids}")

    for e in EVENT_TYPES:
        if e.domain not in list(Domain):
            errors.append(f"invalid domain for {e.id}: {e.domain}")
        if e.direction not in list(EventDirection):
            errors.append(f"invalid direction for {e.id}: {e.direction}")
        if e.granularity not in list(TemporalGranularity):
            errors.append(f"invalid granularity for {e.id}: {e.granularity}")

    # Single-Parent: each event_id maps to exactly one domain
    domain_counts: Dict[Domain, int] = {}
    for e in EVENT_TYPES:
        domain_counts[e.domain] = domain_counts.get(e.domain, 0) + 1
    expected = {Domain.EDUCATION: 4, Domain.CAREER: 5, Domain.FAMILY: 5, Domain.LIFE_EVENT: 3}
    if domain_counts != expected:
        errors.append(f"domain distribution mismatch: got {domain_counts}, expected {expected}")

    return errors
