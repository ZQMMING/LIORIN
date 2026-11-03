"""Phase 3/4 全引擎验证（五部正式化 Registry）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.yuhai_ziping.rule.rule_engine import RuleEngine  # noqa: E402
from engines.yuhai_ziping.evidence.evidence_registry import EvidenceRegistry  # noqa: E402

EXPECTED = [
    ("pzzq", 49, 81), ("dts", 258, 90), ("qtbj", 202, 109),
    ("smth", 2530, 161), ("sftk", 2519, 18),
]


@pytest.mark.parametrize("engine,src_n,rule_n", EXPECTED)
def test_multi_engine_registry_load(engine, src_n, rule_n):
    """五部正式 Registry 可加载、可编译、数量正确。"""
    eng = RuleEngine(engine=engine)
    assert len(eng.rules) == rule_n
    assert len(eng.source_grade) == src_n


@pytest.mark.parametrize("engine", [e for e, _, _ in EXPECTED])
def test_multi_engine_evidence_chain(engine):
    """五部 Evidence 链完整：无 BROKEN_CHAIN。"""
    evd = EvidenceRegistry(engine=engine)
    assert evd.record_count > 0
    assert all(g["type"] != "BROKEN_CHAIN" for g in evd.gaps)
    for r in evd.rules:
        assert evd.evidence_ids_for(r["rule_id"]), f"{engine}: Rule 无证据 {r['rule_id']}"


@pytest.mark.parametrize("engine", [e for e, _, _ in EXPECTED])
def test_multi_engine_emit_smoke(engine):
    """空 chart 冒烟：emit 规则对空输入不崩溃（返回列表）。"""
    eng = RuleEngine(engine=engine)
    facts = eng.run({})
    assert isinstance(facts, list)


def test_multi_engine_export(tmp_path):
    """五部 Evidence/Gap 导出。"""
    for engine, _, _ in EXPECTED:
        evd = EvidenceRegistry(engine=engine)
        evd.export(evd_out=tmp_path / f"evidence.{engine}.jsonl", gap_out=tmp_path / f"gap.{engine}.jsonl")
        assert (tmp_path / f"evidence.{engine}.jsonl").exists()
