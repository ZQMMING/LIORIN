"""
V-Validation V1.2 — Canonical Signal Schema (Schema 4)

Contract:
  Phase 1: Schema ONLY — no aggregation, no voting, no weights.
  SignalAdapter converts engine signals → CanonicalSignal.
  Phase 3: Aggregation policy goes in reasoning/signals.py (separate module).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SignalLayer(enum.Enum):
    """Signal temporal layer enum (V1.2)."""

    BASELINE = "BASELINE"                       # 本命/大运基线
    CYCLE_CONTEXT = "CYCLE_CONTEXT"             # 流年/流月周期背景
    DAILY_ACTIVATION = "DAILY_ACTIVATION"       # 日/时激活


class SourceEngine(enum.Enum):
    """Source engine enum (V1.2)."""

    BAZI = "Bazi"
    HELUO = "Heluo"
    ZIWEI = "Ziwei"
    HUANGLI = "Huangli"
    KNOWLEDGE = "Knowledge"
    BLIND = "Blind"  # 盲派八字


@dataclass
class SignalTemporalScope:
    """Time window attached to a single Canonical Signal."""

    start_year: Optional[int] = None
    end_year: Optional[int] = None
    start_month: Optional[int] = None
    end_month: Optional[int] = None
    start_day: Optional[int] = None
    end_day: Optional[int] = None
    granularity: str = "YEARLY"   # YEARLY | MONTHLY | DAILY

    def to_dict(self) -> dict:
        d = {k: v for k, v in {
            "start_year": self.start_year,
            "end_year": self.end_year,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "start_day": self.start_day,
            "end_day": self.end_day,
        }.items() if v is not None}
        if self.granularity != "YEARLY":
            d["granularity"] = self.granularity
        return d


@dataclass
class CanonicalSignal:
    """Schema 4: standardized canonical signal struct.

    Phase 1 contract: This is a pure data schema.
    No aggregation, no weight, no voting lives here.
    """

    signal_id: str
    source_engine: SourceEngine
    ontology_type: str   # USO type: ACTION|OUTPUT|CONSTRAINT|RESOURCE|SUPPORT|RELATION|REFLECTION|CHANGE
    event_types: List[str]        # FK → EventDefinition.id (from Schema 3)
    direction: str                # POSITIVE|NEGATIVE|CHANGE|NEUTRAL|UNKNOWN
    confidence: float             # 0.0–1.0
    temporal_scope: SignalTemporalScope
    evidence_refs: List[str]      # → evidence_id (from Schema 7)
    rule_refs: List[str] = field(default_factory=list)
    layer: SignalLayer = SignalLayer.BASELINE
    extracted_at: str = ""        # ISO8601
    
    # Phase 4 extensions (T0-1)
    system: str = ""              # Which system generated this: BAZI/ZIWEI/HELUO/YI/BLIND
    theme: str = ""               # Event theme: MARRIAGE/HEALTH/CAREER/WEALTH/FAMILY/CHILDREN/ACADEMICS
    time_scope: str = ""          # Granularity: YEARLY/MONTHLY/DAILY/HOURLY
    conflict_group: str = ""      # For conflict resolution grouping
    domain: str = ""              # 辨证域：WANGSHUAI/GEJU/YONGSHEN/SHISHEN/SHIJIAN
    
    def to_dict(self) -> dict:
        result = {
            "signal_id": self.signal_id,
            "source_engine": self.source_engine.value,
            "ontology_type": self.ontology_type,
            "event_types": self.event_types,
            "direction": self.direction,
            "confidence": self.confidence,
            "temporal_scope": self.temporal_scope.to_dict(),
            "evidence_refs": self.evidence_refs,
            "rule_refs": self.rule_refs,
            "layer": self.layer.value,
            "extracted_at": self.extracted_at,
        }
        # Add new fields if set
        for field in ('system', 'theme', 'time_scope', 'conflict_group', 'domain'):
            if getattr(self, field):
                result[field] = getattr(self, field)
        return result
