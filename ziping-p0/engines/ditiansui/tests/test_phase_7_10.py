"""Phase 7-10 管线测试 · ditiansui。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.common.facts_builder import FactsBuilder  # noqa: E402

REG = "dts"
ENGINE_ID = "DITIANSUI"

CHART = {
    "canonical_input": {"ref": "p7t", "hash": "z" * 12},
    "pillars": {
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "酉"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "戊", "branch": "午"},
    },
    "gender": "男",
    "xunkong": {"xun": "甲午旬"},
    "shishen": {"day_branch_hidden": ["丁"]},
    "changsheng": {}, "nayin": {}, "relations": {},
}


def test_judgment_assertions():
    from engines.ditiansui.judgment.judgment_builder import build_assertions
    r = FactsBuilder(engine=REG).build(CHART)
    asts = build_assertions(r)
    assert all(a["assertion_id"].startswith("AST-") for a in asts)
    for a in asts:
        assert a["fact_id"] and a["evidence_ids"]


def test_golden_runner_approved():
    from engines.ditiansui.golden.golden_runner import GoldenRunner
    gr = GoldenRunner()
    assert len(gr.approved_technical_goldens()) == 12  # Human 已整体审批（§67）


def test_provenance_record():
    from engines.ditiansui.provenance.provenance import ProvenanceRecorder
    rec = ProvenanceRecorder(engine=REG)
    p = rec.record({}, "ref", ["R1"], ["S1"], ["E1"])
    assert p["engine"] == ENGINE_ID
    assert p["rule_version"] and p["source_version"]


def test_regression_harness():
    from engines.ditiansui.regression.regression_harness import DEMO_CHART, compare, snapshot_all
    r1 = FactsBuilder(engine=REG).build(DEMO_CHART)
    r2 = FactsBuilder(engine=REG).build(DEMO_CHART)
    assert compare(snapshot_all(r1), snapshot_all(r2))["pass"]


def test_production_admission_passes():
    from engines.ditiansui.production.admission import ProductionAdmission
    res = ProductionAdmission(engine=REG).check()
    assert res["golden"]["status"] == "PASS"          # TG 已整体审批
    assert res["admission"] == "ADMITTED"            # 全 gate 通过
    assert res["cross_domain"]["status"] == "PASS"
    for gate in ("contract", "schema", "rule", "evidence", "regression", "boundary", "provenance"):
        assert res[gate] is True, f"{gate} gate 失败: {res[gate]}"
