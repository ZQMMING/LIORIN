"""Phase 9/10 测试（§68/§69/§40）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.yuhai_ziping.provenance.provenance import ProvenanceRecorder  # noqa: E402
from engines.yuhai_ziping.production.admission import ProductionAdmission  # noqa: E402
from engines.yuhai_ziping.regression.regression_harness import DEMO_CHART  # noqa: E402
from engines.yuhai_ziping.calculation.facts_builder import FactsBuilder  # noqa: E402


def test_provenance_record_structure():
    rec = ProvenanceRecorder()
    p = rec.record({}, "ref-t", ["CAND-YHZP-001"], ["YHZP-003-001"], ["EVD-YHZP-001"])
    assert p["engine"] == "YUHAI_ZIPING"
    assert p["engine_version"] == "0.1.0"
    assert p["contract_version"] == "1.0.0"
    assert p["rule_version"] == "0.1.0"
    assert p["source_version"] == "1.0.0"
    assert p["input_ref"] == "ref-t"
    assert p["timestamp"]


def test_provenance_from_result():
    r = FactsBuilder().build(DEMO_CHART)
    p = ProvenanceRecorder().record_from_result(r)
    assert p["rule_ids"], "应从 facts 汇总 rule_ids"
    assert p["source_ids"] and p["evidence_ids"]
    assert r.canonical_input["ref"] == p["input_ref"]


def test_admission_contract_pass():
    adm = ProductionAdmission()
    assert adm._contract() is True


def test_admission_golden_passed():
    """TG 已批准（Human Architect 整体审批）→ golden PASS → ADMITTED。"""
    adm = ProductionAdmission()
    r = adm.check()
    assert r["golden"]["status"] == "PASS"
    assert r["golden"]["approved"] == 12
    assert r["golden"]["total"] == 12
    assert r["admission"] == "ADMITTED"


def test_admission_all_mechanical_gates_pass():
    """除 golden 外全部机制 gate 应 PASS。"""
    adm = ProductionAdmission()
    r = adm.check()
    for k in ("contract", "schema", "rule", "evidence", "regression", "boundary", "provenance"):
        assert r[k] is True, f"{k} gate FAIL: {r[k]}"


def test_cross_domain_isolated():
    """§68：YHZP 不消费 L2B~L6；reads=[]。"""
    adm = ProductionAdmission()
    r = adm.check()
    assert r["cross_domain"]["status"] == "PASS"
    import json as _json
    from engines.yuhai_ziping.validator import CONTRACT_PATH
    contract = _json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["dependency"]["reads"] == []
    assert contract["input"]["allowed_engines"] == []
