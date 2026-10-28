"""V2.2.2 FINAL §43-44 Canonical Gate 结果模型。

任何关键 Gate 失败必须 FAIL_CLOSED，不得继续向下游传播。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class GateOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class GateResult:
    """单个 Gate 的判定结果。"""

    gate_id: str
    outcome: GateOutcome
    detail: str = ""
    required: bool = True

    @property
    def passed(self) -> bool:
        return self.outcome == GateOutcome.PASS


@dataclass(frozen=True)
class GateSummary:
    """一组 Gate 的整体判定。"""

    results: List[GateResult] = field(default_factory=list)
    fail_closed: bool = False

    def add(self, result: GateResult) -> "GateSummary":
        new = list(self.results)
        new.append(result)
        fail_closed = self.fail_closed
        if result.required and result.outcome == GateOutcome.FAIL:
            fail_closed = True
        return GateSummary(results=new, fail_closed=fail_closed)

    @property
    def all_passed(self) -> bool:
        return not self.fail_closed and all(r.passed for r in self.results)

    @property
    def failed_gates(self) -> List[str]:
        return [r.gate_id for r in self.results if not r.passed]
