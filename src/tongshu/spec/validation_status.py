"""
V-Validation V1.2 — Validation Status Schema (Schema 1)

Contract:
  NOT_IMPLEMENTED ≠ FAIL, NOT_EVALUABLE ≠ FAIL, BLOCKED ≠ FAIL
  NOT_IMPLEMENTED dimensions are EXCLUDED from denominator
  BLOCKED dimensions are INCLUDED in denominator but marked BLOCKED

"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─── ValidationStatus enum ────────────────────────────────────────────────────


class ValidationStatus(enum.Enum):
    """Dimension diagnostic status.

    IMPORTANT: These five non-PASS statuses are mutually exclusive and
    must NOT be conflated with FAIL.

    - NOT_IMPLEMENTED : component not yet built; excluded from denominator
    - NOT_EVALUABLE   : data insufficient for assessment
    - BLOCKED         : depends on upstream schema not yet available
    - PARTIAL         : partial coverage; no failures recorded
    - PASS / FAIL     : definitive diagnostic result
    """

    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    BLOCKED = "BLOCKED"
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"

    @property
    def is_diagnostic(self) -> bool:
        """True for statuses that contribute to diagnostic denominator."""
        return self in (
            ValidationStatus.PASS,
            ValidationStatus.FAIL,
            ValidationStatus.PARTIAL,
        )

    @property
    def is_final(self) -> bool:
        """True for definitive terminal states."""
        return self in (ValidationStatus.PASS, ValidationStatus.FAIL)

    @property
    def is_skippable(self) -> bool:
        """True if this status should be excluded from denominator."""
        return self in (
            ValidationStatus.NOT_IMPLEMENTED,
            ValidationStatus.NOT_EVALUABLE,
        )


# ─── F1 aggregation method ────────────────────────────────────────────────────


class F1AggregationMethod(enum.Enum):
    """V1.2 mandates Micro-F1 for Overall F1. Macro-F1 is auxiliary only."""

    MICRO = "MICRO"
    MACRO = "MACRO"


# ─── DimensionStatus ──────────────────────────────────────────────────────────


@dataclass
class DimensionStatus:
    """Diagnostic state of a single Validation Dimension."""

    dimension_id: str  # e.g. "CALCULATION", "SIGNAL", …
    status: ValidationStatus
    score: Optional[float] = None       # 0.0–1.0, only when status ∈ {PASS, FAIL, PARTIAL}
    failures: List[str] = field(default_factory=list)  # failure_type list
    coverage_ratio: Optional[float] = None  # only for PARTIAL
    blocked_by: Optional[str] = None    # only for BLOCKED

    def to_dict(self) -> dict:
        d: Dict = {
            "dimension_id": self.dimension_id,
            "status": self.status.value,
        }
        if self.score is not None:
            d["score"] = self.score
        if self.failures:
            d["failures"] = self.failures
        if self.coverage_ratio is not None:
            d["coverage_ratio"] = self.coverage_ratio
        if self.blocked_by is not None:
            d["blocked_by"] = self.blocked_by
        return d


# ─── VALIDATION_STATUS_REPORT ────────────────────────────────────────────────


# V1.2-defined 9 Dimension IDs (strict order)
VALIDATION_DIMENSIONS: List[str] = [
    "CALCULATION",
    "SIGNAL",
    "ONTOLOGY",
    "TEMPORAL",
    "SEVERITY",
    "EVIDENCE",
    "INTERPRETATION",
    "CROSS_ENGINE_AGREE",
    "DIRECTIONALITY",
]


@dataclass
class ValidationStatusReport:
    """Schema 1 output: whole-validation diagnostic summary."""

    report_id: str
    generated_at: str               # ISO8601
    v1_2_version: str               # e.g. "V1.2"
    dataset_version: str            # Golden Dataset version

    # 9+1 structure: 9 Dimensions + VALIDATION_STATUS summary
    dimensions: Dict[str, DimensionStatus] = field(default_factory=dict)

    # Micro-F1 is MANDATORY for Overall F1 (P0 contract)
    f1_aggregation_method: F1AggregationMethod = F1AggregationMethod.MICRO
    overall_f1: Optional[float] = None
    overall_precision: Optional[float] = None
    overall_recall: Optional[float] = None

    # Auxiliary metrics (must NOT be confused with overall_f1)
    jaccard_match_rate: Optional[float] = None   # old Jaccard/IoU formula, renamed
    macro_f1: Optional[float] = None             # auxiliary only

    # Summary stats
    total_events: int = 0
    total_dimensions_evaluated: int = 0
    total_failures: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "v1_2_version": self.v1_2_version,
            "dataset_version": self.dataset_version,
            "f1_aggregation_method": self.f1_aggregation_method.value,
            "overall_f1": self.overall_f1,
            "overall_precision": self.overall_precision,
            "overall_recall": self.overall_recall,
            "jaccard_match_rate": self.jaccard_match_rate,
            "macro_f1": self.macro_f1,
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
            "total_events": self.total_events,
            "total_dimensions_evaluated": self.total_dimensions_evaluated,
            "total_failures": self.total_failures,
        }
