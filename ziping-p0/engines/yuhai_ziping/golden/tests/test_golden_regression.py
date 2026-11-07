"""Phase 8 Golden/Regression 测试（§67）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.yuhai_ziping.calculation.facts_builder import FactsBuilder  # noqa: E402
from engines.yuhai_ziping.golden.golden_runner import GoldenRunner  # noqa: E402
from engines.yuhai_ziping.regression.regression_harness import (  # noqa: E402
    DEMO_CHART, compare, normalize, snapshot_all,
)


def test_golden_runner_runs_all_approved():
    """TG 已整体批准 → 12 条全部可运行（Agent 只 run/compare/report，§67）。"""
    gr = GoldenRunner()
    assert len(gr.approved_technical_goldens()) == 12
    rpt = gr.run_approved()
    assert rpt["technical_summary"]["total"] == 12
    assert rpt["technical_summary"]["approved"] == 12
    assert rpt["technical_summary"]["not_approved"] == 0
    assert len(rpt["technical_goldens"]) == 12


def test_golden_runner_runs_approved(tmp_path):
    """模拟 TG-001/TG-006 被批准 → 可运行（Agent 只 run/compare/report）。"""
    gr = GoldenRunner()
    for g in gr.tg["golden_list"]:
        if g["golden_id"] in ("TG-001", "TG-006"):
            g["approval_status"] = "APPROVED"
    rpt = gr.run_approved()
    by_id = {r["golden_id"]: r for r in rpt["technical_goldens"]}
    assert by_id["TG-001"]["status"] == "PASS"
    assert by_id["TG-006"]["status"] == "PASS"


def test_business_golden_empty():
    gr = GoldenRunner()
    assert gr.bg.get("golden_list", []) == []


def test_normalize_stable():
    f1 = [{"rule_id": "R1", "field": "f", "value": "甲", "context": "c",
           "source_ids": ["S1"], "evidence_ids": ["E1"], "evidence_grade": "A", "extra": "x"}]
    f2 = [{"rule_id": "R1", "field": "f", "value": "甲", "context": "c",
           "source_ids": ["S1"], "evidence_ids": ["E1"], "evidence_grade": "A", "extra": "y"}]
    assert normalize(f1) == normalize(f2)


def test_snapshot_and_compare_deterministic():
    r1 = FactsBuilder().build(DEMO_CHART)
    r2 = FactsBuilder().build(DEMO_CHART)
    rep = compare(snapshot_all(r1), snapshot_all(r2))
    assert rep["pass"] is True
    total = sum(v["baseline"] for v in rep["groups"].values())
    assert total > 0


def test_compare_detects_change():
    r1 = FactsBuilder().build(DEMO_CHART)
    base = snapshot_all(r1)
    current = {g: list(items) for g, items in base.items()}
    if current["basic_structure_facts"]:
        modified = dict(current["basic_structure_facts"][0])
        modified["value"] = "改"  # 篡改一个 fact → 回归应报差异
        current["basic_structure_facts"].append(modified)
    rep = compare(base, current)
    assert rep["pass"] is False
    assert rep["groups"]["basic_structure_facts"]["added"] >= 1
