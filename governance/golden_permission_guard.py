"""V2.2.2 FINAL §55 Golden Permission Guard。

- Agent: READ / RUN / REPORT
- Agent: CANNOT CREATE FINAL GOLDEN / CANNOT MODIFY APPROVED GOLDEN / CANNOT DELETE GOLDEN
- Human Architect: CREATE / APPROVE / FREEZE
- CI: REJECT unauthorized Golden modifications
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from shared_types.errors import GoldenPermissionError


class GoldenAction(str, Enum):
    READ = "READ"
    RUN = "RUN"
    REPORT = "REPORT"
    CREATE = "CREATE"
    APPROVE = "APPROVE"
    FREEZE = "FREEZE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class ActorRole(str, Enum):
    AGENT = "AGENT"
    HUMAN_ARCHITECT = "HUMAN_ARCHITECT"
    CI = "CI"


@dataclass(frozen=True)
class GoldenRecord:
    golden_id: str
    status: str  # DEFINED / NOT_APPROVED / APPROVED / FROZEN
    approved_by: Optional[str] = None


# 角色权限矩阵
PERMISSIONS = {
    ActorRole.AGENT: {GoldenAction.READ, GoldenAction.RUN, GoldenAction.REPORT},
    ActorRole.HUMAN_ARCHITECT: {GoldenAction.CREATE, GoldenAction.APPROVE, GoldenAction.FREEZE, GoldenAction.READ, GoldenAction.RUN, GoldenAction.REPORT, GoldenAction.MODIFY},
    ActorRole.CI: {GoldenAction.READ, GoldenAction.RUN, GoldenAction.REPORT},
}


class GoldenPermissionGuard:
    def __init__(self, registry_path) -> None:
        self.registry_path = registry_path

    def assert_allowed(self, role: ActorRole, action: GoldenAction, golden: Optional[GoldenRecord] = None) -> None:
        allowed = PERMISSIONS[role]
        if action not in allowed:
            raise GoldenPermissionError(f"{role.value} 不允许 {action.value}")
        # 已审批/冻结的 Golden 对 Agent 的写操作一律拒绝（§55）；READ/RUN/REPORT 允许
        if role == ActorRole.AGENT and golden is not None:
            if action in (GoldenAction.CREATE, GoldenAction.MODIFY, GoldenAction.DELETE) and golden.status in ("APPROVED", "FROZEN"):
                raise GoldenPermissionError(
                    f"Agent 试图 {action.value} 已{'冻结' if golden.status=='FROZEN' else '审批'}的 Golden {golden.golden_id}"
                )

    def check_registry_integrity(self, records: List[dict]) -> List[str]:
        """CI 检查：未审批 Golden 不得标记为 FROZEN；缺 approved_by 的 FROZEN 违规。"""
        problems: List[str] = []
        for r in records:
            if r.get("status") == "FROZEN" and r.get("approval_status") != "APPROVED":
                problems.append(f"{r.get('golden_id')}: FROZEN 但未 APPROVED")
            if r.get("status") == "FROZEN" and not r.get("approved_by"):
                problems.append(f"{r.get('golden_id')}: FROZEN 缺 approved_by")
        return problems
