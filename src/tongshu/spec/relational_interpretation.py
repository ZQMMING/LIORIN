"""
V-Validation V1.2 — Relational Interpretation Schema (Schema 8)

Contract:
  InterpInput must NOT contain raw calculation fields.
 禁止 bazi_pillars, heluo_hexagram, ziwei_ming_gong, raw_calculation, CalculationContext.
  Yi Engine output flows through Canonicalization before entering Interpretation.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Optional


class InterpretationLayer(enum.Enum):
    TRUTH_HEXAGRAM = "TRUTH_HEXAGRAM"
    TRUE_LINE = "TRUE_LINE"
    CLASSICAL_TEXT = "CLASSICAL_TEXT"
    IMAGE_EXTENSION = "IMAGE_EXTENSION"


@dataclass
class YiStructure:
    """Yi Engine structural output — consumed by RelationalInterpretation."""

    truth_hexagram: str = ""      # e.g. "QIAN"
    true_line: int = 0            # 1–6
    classical_quote: str = ""
    image_meaning: str = ""
    layer: InterpretationLayer = InterpretationLayer.TRUTH_HEXAGRAM

    def to_dict(self) -> dict:
        return {
            "truth_hexagram": self.truth_hexagram,
            "true_line": self.true_line,
            "classical_quote": self.classical_quote,
            "image_meaning": self.image_meaning,
            "layer": self.layer.value,
        }


# ─── InterpInput (strict boundary — no raw calculation fields) ────────────────


@dataclass
class InterpInput:
    """Input to RelationalInterpretation Engine.

    CONTRACT: This schema MUST NOT expose any raw calculation fields.
    Forbidden fields (checked by test):
      - bazi_pillars
      - heluo_hexagram
      - ziwei_ming_gong
      - raw_calculation
      - CalculationContext
    Allowed fields come only from Canonicalized outputs.
    """

    # Only these canonicalized fields are permitted:
    yi_structure: Optional[YiStructure] = None
    event_type_id: Optional[str] = None       # FK → EventDefinition.id
    severity_class: Optional[str] = None      # LOW|MODERATE|HIGH|CRITICAL
    evidence_refs: List[str] = field(default_factory=list)  # → evidence_id
    signal_refs: List[str] = field(default_factory=list)    # → CanonicalSignal.signal_id
    interpretation_phase: int = 0             # must be >= 6 for Phase 6+

    @classmethod
    def from_dict(cls, data: dict) -> "InterpInput":
        """Factory: raises ValueError if forbidden fields are present."""
        FORBIDDEN_FIELDS = {
            "bazi_pillars",
            "heluo_hexagram",
            "ziwei_ming_gong",
            "raw_calculation",
            "calculation_context",
            "calculation_result",
        }
        unexpected = FORBIDDEN_FIELDS & set(data.keys())
        if unexpected:
            raise ValueError(
                f"InterpInput forbidden fields detected: {unexpected}. "
                "InterpInput must receive only canonicalized outputs, not raw calculations."
            )
        return cls(
            yi_structure=data.get("yi_structure"),
            event_type_id=data.get("event_type_id"),
            severity_class=data.get("severity_class"),
            evidence_refs=data.get("evidence_refs", []),
            signal_refs=data.get("signal_refs", []),
            interpretation_phase=data.get("interpretation_phase", 0),
        )

    def to_dict(self) -> dict:
        return {
            "yi_structure": self.yi_structure.to_dict() if self.yi_structure else None,
            "event_type_id": self.event_type_id,
            "severity_class": self.severity_class,
            "evidence_refs": self.evidence_refs,
            "signal_refs": self.signal_refs,
            "interpretation_phase": self.interpretation_phase,
        }


@dataclass
class RelationalInterpretation:
    """Output of the RelationalInterpretation Engine."""

    interpretation_id: str
    interp_input_ref: str            # → InterpInput (via report_id)
    yi_structure: YiStructure
    evidence_refs: List[str] = field(default_factory=list)
    interpretation_text: str = ""
    phase: int = 0                   # must be >= 6 per V1.2 contract

    def to_dict(self) -> dict:
        return {
            "interpretation_id": self.interpretation_id,
            "yi_structure": self.yi_structure.to_dict(),
            "evidence_refs": self.evidence_refs,
            "interpretation_text": self.interpretation_text,
            "phase": self.phase,
        }
