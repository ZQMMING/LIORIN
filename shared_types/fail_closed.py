"""V2.2.2 FINAL §72 Fail Closed 机制。

以下任何情况必须 FAIL_CLOSED，不得「尽量继续」：
- Canonical Gate failed
- Contract invalid
- Input forbidden
- Rule missing
- Source missing
- Evidence missing
- Golden unauthorized
- Boundary violation
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from shared_types.errors import ShuntianError


class FailClosedReason(str, Enum):
    CANONICAL_GATE = "CANONICAL_GATE"
    CONTRACT_INVALID = "CONTRACT_INVALID"
    INPUT_FORBIDDEN = "INPUT_FORBIDDEN"
    RULE_MISSING = "RULE_MISSING"
    SOURCE_MISSING = "SOURCE_MISSING"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    GOLDEN_UNAUTHORIZED = "GOLDEN_UNAUTHORIZED"
    BOUNDARY_VIOLATION = "BOUNDARY_VIOLATION"
    UNKNOWN = "UNKNOWN"


class FailClosedError(ShuntianError):
    """Fail Closed 信号：下游必须停止传播。"""

    def __init__(self, reason: FailClosedReason, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"FAIL_CLOSED[{reason.value}] {detail}".strip())


def fail_closed(reason: FailClosedReason, detail: str = "") -> "FailClosedError":
    """构造 FailClosedError；调用方应 raise 该结果。"""
    return FailClosedError(reason, detail)
