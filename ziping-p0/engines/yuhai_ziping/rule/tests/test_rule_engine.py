"""Phase 4 Rule Engine 测试（§63 Source→Rule→Test）。

覆盖：全部算子（equals/in/not_in/exists/not_exists）、conjunction/disjunction、
emit 输出、FAIL_CLOSED（未知算子/无 Source 绑定）、全量 340 规则可编译可执行。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.fail_closed import FailClosedError  # noqa: E402
from engines.yuhai_ziping.rule.rule_engine import RuleEngine  # noqa: E402


@pytest.fixture(scope="module")
def engine():
    return RuleEngine()


def test_load_full_registry(engine):
    """340 条规则全量可编译（无坏数据、无孤儿）。"""
    assert len(engine.rules) == 340
    assert len(engine.source_grade) == 592


def test_equals_conjunction_emit(engine):
    """CAND-YHZP-001：甲+己 → 甲己合。"""
    facts = engine.run({"stem": "甲", "partner_stem": "己"})
    hit = [f for f in facts if f["rule_id"] == "CAND-YHZP-001"]
    assert len(hit) == 1
    assert hit[0]["field"] == "stem_he"
    assert hit[0]["value"] == "甲己"
    assert hit[0]["source_ids"] == ["YHZP-003-001"]
    assert hit[0]["evidence_grade"] in {"A", "B", "C", "D"}


def test_in_operator(engine):
    """CAND-YHZP-006：stem in [甲,乙] → 木。"""
    facts = engine.run({"stem": "乙"})
    hit = [f for f in facts if f["rule_id"] == "CAND-YHZP-006"]
    assert hit and hit[0]["value"] == "木"
    facts2 = engine.run({"stem": "丙"})
    assert not [f for f in facts2 if f["rule_id"] == "CAND-YHZP-006"]


def test_not_in_operator():
    """构造 not_in 规则验证。"""
    r = {
        "rule_id": "CAND-TEST-001", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-001-001"],
        "scope": "natal", "preconditions": {"type": "conjunction", "conditions": [
            {"field": "stem", "operator": "not_in", "value": ["甲", "乙"]}]},
        "operator": "emit", "output": {"field": "test", "value": "非甲乙"}, "version": "0.1.0",
        "status": "CANDIDATE",
    }
    eng = RuleEngine()
    eng.rules = [r]
    assert eng.run({"stem": "丙"})[0]["value"] == "非甲乙"
    assert eng.run({"stem": "甲"}) == []


def test_exists_not_exists():
    r = {
        "rule_id": "CAND-TEST-002", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-001-001"],
        "scope": "natal", "preconditions": {"type": "conjunction", "conditions": [
            {"field": "yangshen", "operator": "exists"},
            {"field": "yin_shen", "operator": "not_exists"}]},
        "operator": "emit", "output": {"field": "test", "value": "存阴阳"}, "version": "0.1.0",
        "status": "CANDIDATE",
    }
    eng = RuleEngine()
    eng.rules = [r]
    assert eng.run({"yangshen": "甲"})[0]["value"] == "存阴阳"
    assert eng.run({"yangshen": "甲", "yin_shen": ""})[0]["value"] == "存阴阳"  # 空串视为不存在
    assert eng.run({"yin_shen": "乙"}) == []


def test_disjunction():
    r = {
        "rule_id": "CAND-TEST-003", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-001-001"],
        "scope": "natal", "preconditions": {"type": "disjunction", "conditions": [
            {"field": "stem", "operator": "equals", "value": "甲"},
            {"field": "stem", "operator": "equals", "value": "乙"}]},
        "operator": "emit", "output": {"field": "test", "value": "甲乙之一"}, "version": "0.1.0",
        "status": "CANDIDATE",
    }
    eng = RuleEngine()
    eng.rules = [r]
    assert len(eng.run({"stem": "甲"})) == 1
    assert len(eng.run({"stem": "乙"})) == 1
    assert eng.run({"stem": "丙"}) == []


def test_unknown_operator_fail_closed():
    eng = RuleEngine()
    eng.rules = [{
        "rule_id": "CAND-TEST-004", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-001-001"],
        "scope": "natal", "preconditions": {"type": "conjunction", "conditions": [
            {"field": "stem", "operator": "greater_than", "value": "甲"}]},
        "operator": "emit", "output": {"field": "test", "value": "x"}, "version": "0.1.0", "status": "CANDIDATE",
    }]
    with pytest.raises(FailClosedError):
        eng._compile()


def test_orphan_rule_fail_closed():
    eng = RuleEngine()
    eng.rules = [{
        "rule_id": "CAND-TEST-005", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-999-999"],
        "scope": "natal", "preconditions": {"type": "conjunction", "conditions": [
            {"field": "stem", "operator": "equals", "value": "甲"}]},
        "operator": "emit", "output": {"field": "test", "value": "x"}, "version": "0.1.0", "status": "CANDIDATE",
    }]
    with pytest.raises(FailClosedError):
        eng._compile()


def test_nested_field_path():
    """点路径取值：pillars.day_stem。"""
    r = {
        "rule_id": "CAND-TEST-006", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-001-001"],
        "scope": "natal", "preconditions": {"type": "conjunction", "conditions": [
            {"field": "pillars.day_stem", "operator": "equals", "value": "甲"}]},
        "operator": "emit", "output": {"field": "day_stem", "value": "甲"}, "version": "0.1.0",
        "status": "CANDIDATE",
    }
    eng = RuleEngine()
    eng.rules = [r]
    assert len(eng.run({"pillars": {"day_stem": "甲"}})) == 1
    assert eng.run({"pillars": {"day_stem": "乙"}}) == []


def test_all_emit_rules_have_source_chain(engine):
    """每个 emit 输出 fact 都带 rule_id + source_ids + evidence_grade（§64 链不断）。"""
    for f in engine.run({"stem": "甲", "partner_stem": "己"}):
        assert f["rule_id"].startswith("CAND-YHZP-")
        assert f["source_ids"]
        assert f["evidence_grade"] in {"A", "B", "C", "D"}
