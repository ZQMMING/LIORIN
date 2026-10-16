"""
V-Validation V1.2 — Spec Package (L0: Data Contract Layer)

Contract:
  This package contains L0 data contracts (Schema types only).
  No business logic. No engine calls. No LLM calls.
  L1 (engines), L2 (reasoning policies), L3 (interpretation), L4 (validation)
  are separate packages.
"""
from __future__ import annotations

# L0: Data Contract exports
from .validation_status import (
    ValidationStatus,
    F1AggregationMethod,
    DimensionStatus,
    ValidationStatusReport,
    VALIDATION_DIMENSIONS,
)
from .failure_taxonomy import (
    FailureType,
    FailureRecord,
    DimensionFailureAnalysis,
    FailureAnalysisReport,
)
from .event_ontology_v1 import (
    Domain,
    EventDirection,
    TemporalGranularity,
    EventDefinition,
    EVENT_TYPES,
    EVENT_TYPE_BY_ID,
    DOMAIN_BY_ID,
    DIRECTION_BY_ID,
    validate_ontology_invariants,
)
from .canonical_signal import (
    SignalLayer,
    SourceEngine,
    SignalTemporalScope,
    CanonicalSignal,
)
from .temporal_evidence import (
    TemporalSignal,
    PredictionWindow,
    EvaluationToleranceWindow,
)
from .severity import (
    SeverityClass,
    SEVERITY_WEIGHTS,
    SeverityInput,
    EventSeverity,
    EvidenceCompleteness,
    InterpretationAvailability,
)
from .evidence_chain import (
    EvidenceLevel,
    VerificationStatus,
    ClaimType,
    ALLOWED_CLAIM_CREATORS,
    Source,
    Passage,
    Claim,
    ClaimDraft,
    Evidence,
    validate_chain,
)
from .relational_interpretation import (
    InterpretationLayer,
    YiStructure,
    InterpInput,
    RelationalInterpretation,
)
from .validation_dimensions import (
    DimensionRequirement,
    ValidationDimension,
    VALIDATION_DIMENSION_DEFS,
    DIMENSION_BY_ID,
    ValidationDimensionResult,
    enforce_read_only,
)

__all__ = [
    # Schema 1
    "ValidationStatus",
    "F1AggregationMethod",
    "DimensionStatus",
    "ValidationStatusReport",
    "VALIDATION_DIMENSIONS",
    # Schema 2
    "FailureType",
    "FailureRecord",
    "DimensionFailureAnalysis",
    "FailureAnalysisReport",
    # Schema 3
    "Domain",
    "EventDirection",
    "TemporalGranularity",
    "EventDefinition",
    "EVENT_TYPES",
    "EVENT_TYPE_BY_ID",
    "DOMAIN_BY_ID",
    "DIRECTION_BY_ID",
    "validate_ontology_invariants",
    # Schema 4
    "SignalLayer",
    "SourceEngine",
    "SignalTemporalScope",
    "CanonicalSignal",
    # Schema 5
    "TemporalSignal",
    "PredictionWindow",
    "EvaluationToleranceWindow",
    # Schema 6
    "SeverityClass",
    "SEVERITY_WEIGHTS",
    "SeverityInput",
    "EventSeverity",
    "EvidenceCompleteness",
    "InterpretationAvailability",
    # Schema 7
    "EvidenceLevel",
    "VerificationStatus",
    "ClaimType",
    "ALLOWED_CLAIM_CREATORS",
    "Source",
    "Passage",
    "Claim",
    "ClaimDraft",
    "Evidence",
    "validate_chain",
    # Schema 8
    "InterpretationLayer",
    "YiStructure",
    "InterpInput",
    "RelationalInterpretation",
    # Schema 9
    "DimensionRequirement",
    "ValidationDimension",
    "VALIDATION_DIMENSION_DEFS",
    "DIMENSION_BY_ID",
    "ValidationDimensionResult",
    "enforce_read_only",
]
