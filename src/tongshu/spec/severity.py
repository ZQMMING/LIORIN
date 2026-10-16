"""
V-Validation V1.2 — Severity Schema (Schema 6)

Contract:
  Three separate concepts: EvidenceCompleteness, EventSeverity, InterpretationAvailability.
  EventSeverity uses weighted ARITHMETIC MEAN, NOT product.
  Weights sum to 1.0 exactly.
  Evidence Quality ≠ Evidence Level Number.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class SeverityClass(enum.Enum):
    """Severity classification thresholds (V1.2 frozen)."""

    LOW = "LOW"          # [0.0, 0.3)
    MODERATE = "MODERATE"  # [0.3, 0.6)
    HIGH = "HIGH"        # [0.6, 0.85)
    CRITICAL = "CRITICAL"  # [0.85, 1.0]


# V1.2 weighted arithmetic mean coefficients (sum = 1.0)
SEVERITY_WEIGHTS: dict[str, float] = {
    "signal_strength": 0.20,
    "temporal_convergence": 0.15,
    "ontology_specificity": 0.20,
    "evidence_quality": 0.25,
    "agreement_evidence": 0.20,
}

assert abs(sum(SEVERITY_WEIGHTS.values()) - 1.0) < 1e-9, \
    f"Severity weights must sum to 1.0, got {sum(SEVERITY_WEIGHTS.values())}"


# ─── SeverityInput (strictly typed, no validation Dimension output allowed) ──


@dataclass
class SeverityInput:
    """Inputs to Severity calculation.

    Each field comes from a SPECIFIC upstream schema:
      - signal_strength       ← Schema 4 (CanonicalSignal.confidence)
      - temporal_convergence  ← Schema 5 (TemporalConvergence.convergence_score)
      - ontology_specificity  ← Ontology Specificity Policy V1
      - evidence_quality      ← Evidence Quality Policy V1
      - agreement_evidence    ← Agreement Evidence Engine (raw compute, NOT Dimension output)
    """

    signal_strength: float = 0.0
    temporal_convergence: float = 0.0
    ontology_specificity: float = 0.0
    evidence_quality: float = 0.0
    agreement_evidence: float = 0.0

    def validate_ranges(self) -> list[str]:
        """Return list of range violations (empty = valid)."""
        errors: list[str] = []
        for name, val in [
            ("signal_strength", self.signal_strength),
            ("temporal_convergence", self.temporal_convergence),
            ("ontology_specificity", self.ontology_specificity),
            ("evidence_quality", self.evidence_quality),
            ("agreement_evidence", self.agreement_evidence),
        ]:
            if not (0.0 <= val <= 1.0):
                errors.append(f"{name}={val} out of [0,1]")
        return errors


# ─── EventSeverity (the computed result) ─────────────────────────────────────


@dataclass
class EventSeverity:
    """Computed severity score + classification."""

    severity_score: float          # 0.0–1.0
    severity_class: SeverityClass
    input_summary: SeverityInput

    @classmethod
    def calculate(cls, inputs: SeverityInput) -> "EventSeverity":
        """V1.2 weighted arithmetic mean formula."""
        w = SEVERITY_WEIGHTS
        score = (
            inputs.signal_strength       * w["signal_strength"]
            + inputs.temporal_convergence * w["temporal_convergence"]
            + inputs.ontology_specificity * w["ontology_specificity"]
            + inputs.evidence_quality     * w["evidence_quality"]
            + inputs.agreement_evidence   * w["agreement_evidence"]
        )
        if score < 0.3:
            cls_result = SeverityClass.LOW
        elif score < 0.6:
            cls_result = SeverityClass.MODERATE
        elif score < 0.85:
            cls_result = SeverityClass.HIGH
        else:
            cls_result = SeverityClass.CRITICAL
        return cls(severity_score=score, severity_class=cls_result, input_summary=inputs)


# ─── EvidenceCompleteness (SEPARATE from EventSeverity) ──────────────────────


@dataclass
class EvidenceCompleteness:
    """Evidence chain completeness score — product of 5 sub-ratios.

    This is NOT evidence quality. It measures whether the chain is complete.
    Separated from EventSeverity per V1.2 contract.
    """

    source_completeness: float = 1.0
    passage_completeness: float = 1.0
    claim_traceability: float = 1.0
    evidence_level_completeness: float = 1.0
    signal_traceability: float = 1.0

    @property
    def overall(self) -> float:
        return (
            self.source_completeness
            * self.passage_completeness
            * self.claim_traceability
            * self.evidence_level_completeness
            * self.signal_traceability
        )

    def validate_ranges(self) -> list[str]:
        errors: list[str] = []
        for name, val in [
            ("source_completeness", self.source_completeness),
            ("passage_completeness", self.passage_completeness),
            ("claim_traceability", self.claim_traceability),
            ("evidence_level_completeness", self.evidence_level_completeness),
            ("signal_traceability", self.signal_traceability),
        ]:
            if not (0.0 <= val <= 1.0):
                errors.append(f"{name}={val} out of [0,1]")
        return errors


# ─── InterpretationAvailability (SEPARATE from both above) ───────────────────


@dataclass
class InterpretationAvailability:
    """Whether interpretation can proceed. Independent of EvidenceCompleteness."""

    llm_engine_ready: bool = False
    evidence_chain_readable: bool = False

    @property
    def available(self) -> bool:
        return self.llm_engine_ready and self.evidence_chain_readable
