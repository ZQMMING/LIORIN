"""V2.2.2 FINAL §43-44 Canonical Gate。

必须机器可执行；建议注册 G-001~G-024（附录 §43）。
任何关键 Gate 失败 → FAIL_CLOSED，不得继续向下游传播。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from shared_types.gate_result import GateOutcome, GateResult, GateSummary
from shared_types.fail_closed import FailClosedReason, FailClosedError
from shared_types.errors import CanonicalGateError


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    description: str
    check: Callable[[dict], str]  # 返回空字符串=通过，否则返回失败原因


class CanonicalGate:
    """Canonical Gate 注册与执行器。

    输入为一个「Frozen Canonical Bazi Chart」字典，含 L0 Fact 字段。
    任何 required Gate 失败 → FAIL_CLOSED。
    """

    def __init__(self) -> None:
        self._specs: Dict[str, GateSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        def field_present(field: str):
            def _check(chart: dict) -> str:
                return "" if chart.get(field) is not None else f"缺少字段 {field}"
            return _check

        defaults: List[GateSpec] = [
            GateSpec("G-001", "canonical_input_present", lambda c: "" if c.get("canonical_input") else "缺少 canonical_input"),
            GateSpec("G-002", "canonical_chart_frozen", lambda c: "" if c.get("frozen", False) else "Chart 未冻结"),
            GateSpec("G-003", "canonical_hash_valid", lambda c: "" if isinstance(c.get("hash"), str) and len(c["hash"]) >= 8 else "hash 缺失或过短"),
            GateSpec("G-004", "time_basis_present", field_present("time_basis")),
            GateSpec("G-005", "solar_term_boundary_present", field_present("solar_term_boundary")),
            GateSpec("G-006", "four_pillars_present", field_present("pillars")),
            GateSpec("G-007", "hidden_stems_present", field_present("hidden_stems")),
            GateSpec("G-008", "ten_gods_present", field_present("shishen")),
            GateSpec("G-009", "wuxing_present", field_present("wuxing")),
            GateSpec("G-010", "yinyang_present", field_present("yinyang")),
            GateSpec("G-011", "nayin_present", field_present("nayin")),
            GateSpec("G-012", "xunkong_present", field_present("xunkong")),
            GateSpec("G-013", "changsheng_present", field_present("changsheng")),
            GateSpec("G-014", "relations_present", field_present("relations")),
            GateSpec("G-015", "shensha_present", field_present("shensha")),
            GateSpec("G-016", "palace_facts_present", field_present("palace_facts")),
            GateSpec("G-017", "dayun_present", field_present("dayun")),
            GateSpec("G-018", "liunian_present", field_present("liunian")),
            GateSpec("G-019", "liuyue_present", field_present("liuyue")),
            GateSpec("G-020", "current_relations_present", field_present("current_relations")),
            GateSpec("G-021", "no_recalculation", lambda c: "" if c.get("recalculated") is not True else "禁止重新排盘/重算 L0 Fact"),
            GateSpec("G-022", "no_charting_dependency", lambda c: "" if c.get("charting_dependency") is not True else "禁止依赖排盘库"),
            GateSpec("G-023", "schema_valid", lambda c: "" if c.get("schema_valid", False) else "Chart 未通过 Schema 校验"),
            GateSpec("G-024", "input_contract_valid", lambda c: "" if c.get("input_contract_valid", False) else "输入 Contract 未通过"),
        ]
        for spec in defaults:
            self.register(spec)

    def register(self, spec: GateSpec) -> None:
        if spec.gate_id in self._specs:
            raise CanonicalGateError(spec.gate_id, f"Gate 重复注册: {spec.gate_id}")
        self._specs[spec.gate_id] = spec

    @property
    def gate_ids(self) -> List[str]:
        return list(self._specs.keys())

    def run(self, chart: dict, gate_ids: List[str] | None = None) -> GateSummary:
        """执行（默认全部）Gate；返回 GateSummary。"""
        targets = gate_ids if gate_ids is not None else list(self._specs.keys())
        summary = GateSummary()
        for gid in targets:
            spec = self._specs.get(gid)
            if spec is None:
                result = GateResult(gid, GateOutcome.FAIL, "未注册的 Gate")
            else:
                try:
                    detail = spec.check(chart)
                    outcome = GateOutcome.PASS if detail == "" else GateOutcome.FAIL
                    result = GateResult(gid, outcome, detail)
                except Exception as exc:  # noqa: BLE001
                    result = GateResult(gid, GateOutcome.FAIL, f"Gate 执行异常: {exc}")
            summary = summary.add(result)
        return summary

    def run_or_fail(self, chart: dict, gate_ids: List[str] | None = None) -> GateSummary:
        """执行 Gate；任何 required Gate 失败立即 raise FailClosedError（§72/§44）。"""
        summary = self.run(chart, gate_ids)
        if summary.fail_closed:
            failed = ",".join(summary.failed_gates)
            raise FailClosedError(FailClosedReason.CANONICAL_GATE, f"Canonical Gate 失败: {failed}")
        return summary
