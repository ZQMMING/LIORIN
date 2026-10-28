"""Phase 1 Skeleton 测试（§60）· ziping_zhenquan。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.common.facts_builder import FactsBuilder  # noqa: E402
from engines.yuhai_ziping.rule.rule_engine import RuleEngine  # noqa: E402
from engines.yuhai_ziping.evidence.evidence_registry import EvidenceRegistry  # noqa: E402

DIRNAME = "ziping_zhenquan"
REG = "pzzq"
ENGINE_ID = "ZIPING_ZHENQUAN"

CHART = {
    "canonical_input": {"ref": "smoke", "hash": "x" * 12},
    "pillars": {
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "寅"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "戊", "branch": "午"},
    },
    "gender": "男",
    "xunkong": {"xun": "甲午旬"},
    "shishen": {"day_branch_hidden": ["丁"]},
    "changsheng": {}, "nayin": {}, "relations": {},
}


def test_engine_id():
    from importlib import import_module
    m = import_module(f"engines.{DIRNAME}")
    assert m.ENGINE_ID == ENGINE_ID


def test_contract_loads():
    import json
    c = json.load(open(ROOT / "engines" / DIRNAME / "contract.json", encoding="utf-8"))
    assert c["engine"] == ENGINE_ID
    assert c["input"]["allowed_fields"]


def test_facts_builder_engine_param():
    fb = FactsBuilder(engine=REG)
    assert fb.engine_id == ENGINE_ID
    assert len(fb.rules.rules) > 0


def test_registry_load():
    eng = RuleEngine(engine=REG)
    evd = EvidenceRegistry(engine=REG)
    assert len(eng.source_grade) > 0
    assert evd.record_count > 0


def test_chart_smoke():
    fb = FactsBuilder(engine=REG)
    r = fb.build(CHART)
    assert r.engine == ENGINE_ID
    assert set(r.to_dict()["facts"].keys()) == {
        "ten_god_facts", "six_relative_facts", "palace_facts",
        "basic_structure_facts", "geju_candidates", "relation_facts"}
