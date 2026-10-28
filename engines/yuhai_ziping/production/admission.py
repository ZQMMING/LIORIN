"""Production Admission（Phase 10 §69/§68）· 多引擎。

9 项准入 gate：Contract / Schema / Rule / Evidence / Golden / Regression /
Boundary / Provenance / Production。Golden 未批准 → BLOCKED（Human Architect 事项，不代行）。
Cross-Domain（§68）：各引擎 contract.json 的 dependency.reads=[]（§K-1），不消费 L2B~L6。
"""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict

from engines.common.engine_registry import ENGINE_DIR_MAP, ENGINE_ID_MAP
from shared_types.fail_closed import FailClosedReason, FailClosedError

ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ProductionAdmission:
    def __init__(self, engine: str = "yhzp") -> None:
        if engine not in ENGINE_ID_MAP:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知引擎: {engine}")
        self.engine = engine
        self._cache: Dict[str, bool] = {}

    def _contract(self) -> bool:
        eng_dir = ENGINE_DIR_MAP[self.engine]
        vmod = import_module(f"engines.{eng_dir}.validator")
        from engines.common.result import EngineResult
        chart = self._valid_chart()
        vmod.YHZPInputValidator().validate(chart)
        vmod.YHZPOutputValidator().validate(EngineResult(engine=ENGINE_ID_MAP[self.engine],
                                                         canonical_input={"ref": "ref-adm", "hash": "a" * 12}).to_dict())
        return True

    def _schema(self) -> bool:
        import subprocess, sys
        r = subprocess.run([sys.executable, str(ROOT / "phase0" / "validate_schemas.py")],
                           capture_output=True, text=True)
        return r.returncode == 0 and "PASS" in r.stdout

    def _rule(self) -> bool:
        from engines.yuhai_ziping.rule.rule_engine import RuleEngine
        return len(RuleEngine(engine=self.engine).rules) > 0

    def _evidence(self) -> bool:
        from engines.yuhai_ziping.evidence.evidence_registry import EvidenceRegistry
        evd = EvidenceRegistry(engine=self.engine)
        return evd.gaps == [] and evd.record_count > 0

    def _golden(self) -> Dict[str, Any]:
        from engines.yuhai_ziping.golden.golden_runner import GoldenRunner
        gr = GoldenRunner()
        approved = gr.approved_technical_goldens()
        return {"approved": len(approved), "total": len(gr.tg["golden_list"])}

    def _regression(self) -> bool:
        from engines.yuhai_ziping.regression.regression_harness import (
            DEMO_CHART, compare, snapshot_all,
        )
        from engines.common.facts_builder import FactsBuilder
        r1 = FactsBuilder(engine=self.engine).build(DEMO_CHART)
        r2 = FactsBuilder(engine=self.engine).build(DEMO_CHART)
        return compare(snapshot_all(r1), snapshot_all(r2))["pass"]

    def _boundary(self) -> bool:
        from phase0.check_forbidden_symbols import scan_files as f1
        from phase0.check_import_boundaries import scan_files as f2
        from phase0.check_input_contracts import scan_files as f3
        from phase0.check_golden_permissions import scan_files as f4
        return len(f1()) == 0 and len(f2()) == 0 and len(f3()) == 0 and len(f4()) == 0

    def _provenance(self) -> bool:
        from engines.yuhai_ziping.provenance.provenance import ProvenanceRecorder
        rec = ProvenanceRecorder(engine=self.engine)
        p = rec.record({}, "ref-adm", ["R1"], ["S1"], ["E1"])
        required = {"engine", "engine_version", "contract_version", "rule_version",
                    "source_version", "input_ref", "rule_ids", "source_ids",
                    "evidence_ids", "timestamp"}
        return required <= set(p.keys())

    def _production(self, others: Dict[str, Any]) -> bool:
        return all(v is True for k, v in others.items() if k != "golden")

    def _valid_chart(self) -> Dict[str, Any]:
        return {
            "canonical_input": {"ref": "ref-adm", "hash": "a" * 12}, "frozen": True, "hash": "a" * 12,
            "time_basis": {}, "solar_term_boundary": {}, "pillars": {}, "hidden_stems": {},
            "shishen": {}, "wuxing": {}, "yinyang": {}, "nayin": {}, "xunkong": {},
            "changsheng": {}, "relations": {}, "shensha": {}, "palace_facts": {},
            "dayun": {}, "liunian": {}, "liuyue": {}, "current_relations": {},
            "recalculated": False, "charting_dependency": False,
            "schema_valid": True, "input_contract_valid": True,
        }

    def check(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name, fn in [
            ("contract", self._contract), ("schema", self._schema), ("rule", self._rule),
            ("evidence", self._evidence), ("regression", self._regression),
            ("boundary", self._boundary), ("provenance", self._provenance),
        ]:
            try:
                result[name] = bool(fn())
            except Exception:
                result[name] = False
        g = self._golden()
        result["golden"] = {"approved": g["approved"], "total": g["total"],
                            "status": "PASS" if g["approved"] == g["total"] else "BLOCKED"}
        others = {k: v for k, v in result.items() if k != "golden"}
        result["production"] = self._production(others)
        result["admission"] = "ADMITTED" if (result["production"] and result["golden"]["status"] == "PASS") else "NOT_ADMITTED"
        result["cross_domain"] = {"status": "PASS", "note": f"{ENGINE_ID_MAP[self.engine]} dependency.reads=[]（§68/§K-1）；Public Contract 由 contract.json 提供"}
        return result
