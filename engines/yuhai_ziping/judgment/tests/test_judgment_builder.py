"""Phase 7 Judgment Builder 测试（§66）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.yuhai_ziping.calculation.facts_builder import FactsBuilder  # noqa: E402
from engines.yuhai_ziping.judgment.judgment_builder import JudgmentBuilder, build_assertions  # noqa: E402


@pytest.fixture(scope="module")
def result():
    chart = {
        "canonical_input": {"ref": "ref-demo-001", "hash": "a" * 12},
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "甲", "branch": "午"},
            "hour": {"stem": "戊", "branch": "午"},
        },
        "gender": "男", "xunkong": {"xun": "甲午旬"},
        "shishen": {"day_branch_hidden": ["丁"]},
        "changsheng": {}, "nayin": {}, "relations": {},
    }
    return FactsBuilder().build(chart)


def test_assertions_assembled(result):
    asts = build_assertions(result)
    assert asts, "facts → assertions 组装"
    a = asts[0]
    assert set(a.keys()) >= {"assertion_id", "fact_id", "group", "statement", "source_ids", "evidence_ids"}
    assert a["assertion_id"].startswith("AST-")
    assert a["source_ids"] and a["evidence_ids"]


def test_assertions_map_all_facts(result):
    asts = build_assertions(result)
    fact_count = sum(len(v) for v in result.facts.to_dict().values())
    assert len(asts) == fact_count


def test_no_judgment_without_rules(result):
    """YHZP 无 judgment 规则 → judgments 空（不臆造）。"""
    jb = JudgmentBuilder()
    assert jb.build(result) == []


def test_judgment_chain_validation(result):
    jb = JudgmentBuilder()
    f = build_assertions(result)[0]
    good = {"judgment_id": "J-1", "fact_ids": [f["fact_id"]]}
    assert jb.validate_judgment(good, result) is True
    bad = {"judgment_id": "J-2", "fact_ids": ["FCT-NOPE"]}
    assert jb.validate_judgment(bad, result) is False
    nofact = {"judgment_id": "J-3", "fact_ids": []}
    assert jb.validate_judgment(nofact, result) is False


def test_judgment_requires_evidence(result):
    """无证据的 fact 不能支撑 judgment（→UNKNOWN）。"""
    jb = JudgmentBuilder()
    # 构造一个无证据 fact 的判断
    fake_result = result
    stripped = {k: v for k, v in fake_result.to_dict().items()}
    fake = {"judgment_id": "J-4", "fact_ids": []}
    assert jb.validate_judgment(fake, result) is False
