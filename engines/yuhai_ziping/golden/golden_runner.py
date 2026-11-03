"""Golden Runner（Phase 8 §67）。

Agent 权限仅限 run / compare / report（§67）。
- Technical Golden：必须 approval_status=APPROVED 才可运行验收；未批准 → report 阻塞，不代行审批
- Business Golden：Registry 当前为空 → 无可运行业务 golden
- GoldenPermissionGuard：CI 拒绝任何未授权写操作
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from shared_types.fail_closed import FailClosedReason, FailClosedError
from phase0.check_forbidden_symbols import scan_files as forbidden_scan
from phase0.check_import_boundaries import scan_files as import_scan
from phase0.check_input_contracts import scan_files as input_contract_scan

ROOT = Path(__file__).resolve().parent.parent.parent.parent
TG_PATH = ROOT / "governance" / "golden" / "technical_golden_registry.json"
BG_PATH = ROOT / "governance" / "golden" / "business_golden_registry.json"


class GoldenRunner:
    """执行已批准的 Golden 并产出 report。"""

    def __init__(self) -> None:
        self.tg = json.loads(TG_PATH.read_text(encoding="utf-8"))
        bg_raw = BG_PATH.read_text(encoding="utf-8").strip()
        self.bg = json.loads(bg_raw) if bg_raw else {"golden_list": []}

    def approved_technical_goldens(self) -> List[Dict[str, Any]]:
        return [g for g in self.tg["golden_list"] if g.get("approval_status") == "APPROVED"]

    def _run_golden(self, g: Dict[str, Any]) -> Dict[str, Any]:
        """按 TG purpose 映射到对应验证器。未映射 → report 跳过。"""
        gid = g["golden_id"]
        checks: Dict[str, Callable[[], bool]] = {
            "TG-001": lambda: self._run_gate(),
            "TG-003": lambda: self._run_contract(),
            "TG-004": lambda: len(import_scan()) == 0,
            "TG-005": lambda: len(input_contract_scan()) == 0,
            "TG-006": lambda: len(forbidden_scan()) == 0,
        }
        fn = checks.get(gid)
        if fn is None:
            return {"golden_id": gid, "status": "SKIPPED", "detail": "无对应自动验证器（需 Human 配置）"}
        ok = fn()
        return {"golden_id": gid, "status": "PASS" if ok else "FAIL"}

    def _run_gate(self) -> bool:
        from phase0.canonical_gate import CanonicalGate
        gate = CanonicalGate()
        # 正例：全字段合法 chart 应过 Gate
        chart = {k: v for k, v in _valid_chart().items()}
        try:
            return gate.run_or_fail(chart).all_passed
        except Exception:
            return False

    def _run_contract(self) -> bool:
        from engines.yuhai_ziping.validator import YHZPInputValidator, YHZPOutputValidator
        from engines.yuhai_ziping.result import YHZPEngineResult
        try:
            YHZPInputValidator().validate(_valid_chart())
            YHZPOutputValidator().validate(YHZPEngineResult(
                canonical_input={"ref": "ref-tg", "hash": "a" * 12}).to_dict())
            return True
        except Exception:
            return False

    def run_approved(self) -> Dict[str, Any]:
        """run + compare + report（§67）。"""
        approved = self.approved_technical_goldens()
        results = [self._run_golden(g) for g in approved]
        bg_list = self.bg.get("golden_list", [])
        return {
            "report_id": "RPT-GOLDEN-001",
            "engine": "YUHAI_ZIPING",
            "technical_goldens": results,
            "technical_summary": {
                "total": len(self.tg["golden_list"]),
                "approved": len(approved),
                "not_approved": len(self.tg["golden_list"]) - len(approved),
            },
            "business_goldens": {"total": len(bg_list), "run": 0,
                                 "detail": "Business Golden Registry 当前为空（Human 填充后运行）"},
            "note": "Agent 仅 run/compare/report；CREATE/APPROVE/FREEZE 仅 Human Architect（§67/§91）",
        }


def _valid_chart() -> Dict[str, Any]:
    return {
        "canonical_input": {"ref": "ref-tg-001", "hash": "a" * 12}, "frozen": True, "hash": "a" * 12,
        "time_basis": {}, "solar_term_boundary": {}, "pillars": {}, "hidden_stems": {},
        "shishen": {}, "wuxing": {}, "yinyang": {}, "nayin": {}, "xunkong": {},
        "changsheng": {}, "relations": {}, "shensha": {}, "palace_facts": {},
        "dayun": {}, "liunian": {}, "liuyue": {}, "current_relations": {},
        "recalculated": False, "charting_dependency": False,
        "schema_valid": True, "input_contract_valid": True,
    }
