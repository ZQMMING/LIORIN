"""ZiweiChart producer contract and downstream consumption regressions."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter
from tongshu.engines.ziwei_engine import (
    ZiweiChart,
    ZiweiEngine,
    ZiweiEngineUnavailableError,
)
from tongshu.engines.ziwei.evidence_producer import ZiweiEvidenceProducer


ROOT = Path(__file__).resolve().parents[1]
NODE_MODULES = ROOT / "node_modules"


def test_chart_from_dict_backfills_legacy_nested_palaces():
    legacy = {
        "source": "iztro",
        "soul_palace_main_stars": ["QISHA"],
        "palace_data": {
            "soul_earthly_branch": "午",
            "body_earthly_branch": "辰",
            "five_elements_class": "火六局",
            "palaces": {"命宫": {"stem": "庚", "branch": "午", "major": ["QISHA"]}},
        },
    }
    chart = ZiweiChart.from_dict(legacy)
    assert chart.soul_earthly_branch == "午"
    assert chart.body_earthly_branch == "辰"
    assert chart.fiveElementsClass == "火六局"
    assert chart.palaces == legacy["palace_data"]["palaces"]
    assert ZiweiChart.from_dict(chart.to_dict()).to_dict() == chart.to_dict()


@pytest.mark.skipif(not (NODE_MODULES / "iztro").exists(), reason="real iztro unavailable")
def test_engine_compute_has_complete_top_level_contract():
    chart = ZiweiEngine(node_modules_dir=NODE_MODULES).compute(
        (1984, 10, 15), 10, gender="male"
    )
    assert chart.source == "iztro"
    assert len(chart.palaces) == 12
    assert chart.soul_earthly_branch
    assert chart.body_earthly_branch
    assert chart.palaces == chart.palace_data["palaces"]
    assert chart.palaces["命宫"]["major"]
    assert len(chart.palace_stems) == 12
    assert chart.flying_transforms


@pytest.mark.skipif(not (NODE_MODULES / "iztro").exists(), reason="real iztro unavailable")
def test_full_chart_and_compute_share_structural_contract():
    engine = ZiweiEngine(node_modules_dir=NODE_MODULES)
    computed = engine.compute((1984, 10, 15), 10, gender="male")
    full = engine.full_chart((1984, 10, 15), 10, gender="male")
    assert computed.source == full.source == "iztro"
    assert computed.soul_earthly_branch == full.soul_earthly_branch
    assert computed.body_earthly_branch == full.body_earthly_branch
    assert set(computed.palaces) == set(full.palaces)


@pytest.mark.skipif(not (NODE_MODULES / "iztro").exists(), reason="real iztro unavailable")
def test_solar_adapter_has_complete_top_level_contract():
    chart = ZiweiSolarAdapter().compute(1984, 11, 9, 10, gender="male")
    assert chart.source == "iztro"
    assert len(chart.palaces) == 12
    assert chart.soul_earthly_branch
    assert chart.body_earthly_branch
    assert chart.palaces == chart.palace_data["palaces"]
    assert chart.palaces["命宫"]["major"]
    assert len(chart.palace_stems) == 12


def test_evidence_producer_consumes_real_chart_palaces():
    if not (NODE_MODULES / "iztro").exists():
        pytest.skip("real iztro unavailable")
    chart = ZiweiEngine(node_modules_dir=NODE_MODULES).compute(
        (1984, 10, 15), 10, gender="male"
    )
    evidences = ZiweiEvidenceProducer().produce(chart, birth_year=1984)
    palace_evidence = [e for e in evidences if "PALACE" in e.rule_id]
    assert palace_evidence
    assert {e.attributes["palace"] for e in palace_evidence} >= {"命宫"}


def test_stub_gate_and_stub_structure(monkeypatch):
    missing = ROOT / "node_modules_nonexistent"
    monkeypatch.delenv("TONGSHU_ALLOW_ZIWEI_STUB", raising=False)
    with pytest.raises(ZiweiEngineUnavailableError):
        ZiweiEngine(node_modules_dir=missing).compute((1984, 10, 15), 10)

    monkeypatch.setenv("TONGSHU_ALLOW_ZIWEI_STUB", "1")
    chart = ZiweiEngine(node_modules_dir=missing).compute((1984, 10, 15), 10)
    assert chart.source == "stub"
    assert isinstance(chart.palaces, dict)


def test_time_index_and_solar_policy_boundaries():
    from tongshu.engines.ziwei_engine import time_index_from_hour

    assert time_index_from_hour(0) == 0
    assert time_index_from_hour(23) == 12
    assert time_index_from_hour(12) == 6
    assert time_index_from_hour(1) == 1


def test_unknown_main_star_is_retained_for_diagnostics():
    chart = ZiweiChart.from_dict(
        {
            "source": "iztro",
            "soul_palace_main_star": "未知星",
            "soul_palace_main_stars": ["未知星"],
            "palaces": {"命宫": {"major": ["未知星"], "minor": []}},
        }
    )
    assert chart.soul_palace_main_stars == ["未知星"]
    assert chart.palaces["命宫"]["major"] == ["未知星"]
