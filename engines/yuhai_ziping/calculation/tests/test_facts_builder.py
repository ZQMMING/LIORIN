"""Phase 6 Facts Builder 测试（§65/§B-3/§B-5）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.fail_closed import FailClosedError  # noqa: E402
from engines.yuhai_ziping.calculation.facts_builder import FactsBuilder  # noqa: E402
from engines.yuhai_ziping.calculation.l0_adapter import build_base_view, build_contexts  # noqa: E402
from engines.yuhai_ziping.validator import YHZPOutputValidator  # noqa: E402


@pytest.fixture(scope="module")
def chart():
    # 甲日干命盘：月干丙（食神）、时干戊（偏财）、日支午藏丁（伤官）
    return {
        "canonical_input": {"ref": "ref-demo-001", "hash": "a" * 12},
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "甲", "branch": "午"},
            "hour": {"stem": "戊", "branch": "午"},
        },
        "gender": "男",
        "xunkong": {"xun": "甲午旬"},
        "shishen": {"day_branch_hidden": ["丁"]},
        "changsheng": {},
        "nayin": {},
        "relations": {},
    }


def test_base_view_mapping(chart):
    v = build_base_view(chart)
    assert v["day_stem"] == "甲"
    assert v["month_branch"] == "寅"
    assert v["season"] == "春"
    assert v["day_element"] == "木"
    assert set(v["branch"]) == {"子", "寅", "午"}
    assert v["stem_branch_pair"] == "甲午"


def test_contexts_generated(chart):
    v = build_base_view(chart)
    ctxs = build_contexts(v)
    assert any(c["context"] == "day_pillar" for c in ctxs)
    assert any(c["context"] == "ten_god" and c["target_stem"] == "甲" for c in ctxs)
    assert any(c["context"] == "branch_pair" for c in ctxs)
    assert any(c["context"] == "branch_single" and c["branch"] == "午" for c in ctxs)
    assert any(c["context"] == "year_pillar" and c["stem_branch_pair"] == "甲子" for c in ctxs)


def test_facts_builder_groups(chart):
    fb = FactsBuilder()
    r = fb.build(chart)
    d = r.to_dict()
    assert d["engine"] == "YUHAI_ZIPING"
    assert d["status"] == "PASS"
    groups = d["facts"]
    assert set(groups.keys()) == {
        "ten_god_facts", "six_relative_facts", "palace_facts",
        "basic_structure_facts", "geju_candidates", "relation_facts",
    }
    total = sum(len(v) for v in groups.values())
    assert total > 0, "至少应产出 facts"


def test_ten_god_injection_enables_six_relative(chart):
    """十神派生回填 → 六亲规则触发（食神→子(男)、偏财→父、伤官→女）。"""
    fb = FactsBuilder()
    r = fb.build(chart)
    lq = r.facts.six_relative_facts
    assert lq, "六亲规则应被十神回填触发"
    values = {f["value"] for f in lq}
    assert "父" in values          # 甲+戊=偏财 → 父
    assert "子(男)" in values       # 甲+丙=食神 → 子(男)
    assert "女" in values           # 甲+丁=伤官 → 女


def test_facts_have_evidence_chain(chart):
    fb = FactsBuilder()
    r = fb.build(chart)
    for group in r.facts.to_dict().values():
        for f in group:
            assert f["rule_id"].startswith("CAND-YHZP-")
            assert f["source_ids"], f"缺 source_ids: {f}"
            assert f["evidence_ids"], f"缺 evidence_ids: {f}"
            assert f["evidence_grade"] in {"A", "B", "C", "D"}
            assert f["fact_id"].startswith("FCT-")


def test_output_schema_valid(chart):
    fb = FactsBuilder()
    r = fb.build(chart)
    YHZPOutputValidator().validate(r.to_dict())


def test_no_forbidden_output_fields(chart):
    fb = FactsBuilder()
    r = fb.build(chart)
    forbidden = {"global_strength", "global_yongshen", "modern_signal",
                 "modern_conclusion", "llm_judgment", "cross_classic_priority"}
    for group in r.facts.to_dict().values():
        for f in group:
            for k in f:
                if k.lower() in forbidden:
                    pytest.fail(f"禁用输出字段: {k} @ {f['fact_id']}")


def test_missing_canonical_input_fails_closed():
    fb = FactsBuilder()
    with pytest.raises(FailClosedError):
        fb.build({})
