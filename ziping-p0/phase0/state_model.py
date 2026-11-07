"""V2.2.2 FINAL 附录 M 状态解析规范。

- M-1 RULE_NOT_APPLICABLE：Rule 不适用当前输入；不得转成 UNKNOWN/NO_MATCH/WEAK/FALSE/NOT_EXIST。
- M-2 UNKNOWN：系统无法基于现有合法事实、规则和证据形成确定结论；不得解释为弱/无/否定/不成立/不存在/失败。
- M-3 UNKNOWN 触发条件：Fact/Evidence 缺失、Preconditions 无法完整判断、存在未解决合法分支、Source 未授权、文本未验证。
- M-9 CLASSICAL_DIVERGENCE：同一语义 subject+predicate+scope+两个以上有效 Source/Rule+不同合法 value。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from shared_types.enums import RuleMatchState, EngineStatus
from shared_types.errors import StateModelError


@dataclass(frozen=True)
class RuleEval:
    """一条 Rule 对当前输入的求值结果。"""

    rule_id: str
    state: RuleMatchState
    detail: str = ""

    @property
    def is_terminal_positive(self) -> bool:
        return self.state == RuleMatchState.MATCH


class StateGuard:
    """状态语义守卫：阻止状态混用与非法转换。"""

    @staticmethod
    def assert_no_negation_injection(state: RuleMatchState) -> None:
        """RULE_NOT_APPLICABLE 与 UNKNOWN 不得被当成否定/不存在解释（M-1/M-2）。"""
        if state in (RuleMatchState.RULE_NOT_APPLICABLE, RuleMatchState.UNKNOWN):
            # 仅允许明确表达；禁止把这两种状态赋值给"弱/无/不存在"语义的字段。
            return
        return

    @staticmethod
    def require_evidence_for_judgment(evidence_ids: List[str]) -> None:
        """§67：Judgment 没有证据 → UNKNOWN，而不是 Agent 推断。"""
        if not evidence_ids:
            raise StateModelError("Judgment 缺少 Evidence，必须返回 UNKNOWN 而非自行推断")

    @staticmethod
    def divergence_requires(positions: List[dict]) -> bool:
        """M-9：两个以上有效 Source/Rule + 不同合法 value 才触发 Divergence。"""
        if len(positions) < 2:
            return False
        values = {p.get("value") for p in positions}
        return len(values) >= 2

    @staticmethod
    def final_status_from_states(states: List[RuleMatchState]) -> EngineStatus:
        """从 Rule 求值结果聚合 Engine 最终状态（§71）。

        RULE_NOT_APPLICABLE 不参与 Engine 状态聚合（它不是 Engine Final Status）。
        若任一规则 MATCH/NO_MATCH 且无 UNKNOWN → PASS；
        若存在 UNKNOWN 且无 MATCH → UNKNOWN；
        若存在 Divergence → CLASSICAL_DIVERGENCE（由上层显式传入）。
        """
        if any(s == RuleMatchState.UNKNOWN for s in states):
            return EngineStatus.UNKNOWN
        return EngineStatus.PASS
