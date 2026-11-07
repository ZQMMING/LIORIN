"""shared_types 包：V2.2.2 FINAL §11 共享类型。"""

from shared_types.enums import (
    EngineID, EngineStatus, RuleMatchState, TextLayer, EvidenceGrade,
    RuleStatus, SourceStatus, Operator, RuleOperator, RuleType,
    PZZQFormationState, PZZQDestructionState, PZZQRescueState,
    PZZQStructureState, PZZQChengbaiState, DTSQiType, DTSSupportState,
    DTSStrengthState, DTSEffectState, QTBJRequirementType,
    SMTHCombinationType, SMTHCompleteness, SMTHActivationStatus,
    SFTKDiseaseType, SFTKMedicineType, SFTKDongjingState, SFTKGaitouState,
    Scope,
)
from shared_types.errors import (
    ShuntianError, SchemaValidationError, ContractError, CanonicalGateError,
    BoundaryViolation, ForbiddenSymbolError, GoldenPermissionError,
    RegistryError, StateModelError,
)
from shared_types.gate_result import GateOutcome, GateResult, GateSummary
from shared_types.fail_closed import FailClosedReason, FailClosedError, fail_closed

__all__ = [
    "EngineID", "EngineStatus", "RuleMatchState", "TextLayer", "EvidenceGrade",
    "RuleStatus", "SourceStatus", "Operator", "RuleOperator", "RuleType",
    "PZZQFormationState", "PZZQDestructionState", "PZZQRescueState",
    "PZZQStructureState", "PZZQChengbaiState", "DTSQiType", "DTSSupportState",
    "DTSStrengthState", "DTSEffectState", "QTBJRequirementType",
    "SMTHCombinationType", "SMTHCompleteness", "SMTHActivationStatus",
    "SFTKDiseaseType", "SFTKMedicineType", "SFTKDongjingState", "SFTKGaitouState",
    "Scope",
    "ShuntianError", "SchemaValidationError", "ContractError",
    "CanonicalGateError", "BoundaryViolation", "ForbiddenSymbolError",
    "GoldenPermissionError", "RegistryError", "StateModelError",
    "GateOutcome", "GateResult", "GateSummary",
    "FailClosedReason", "FailClosedError", "fail_closed",
]
