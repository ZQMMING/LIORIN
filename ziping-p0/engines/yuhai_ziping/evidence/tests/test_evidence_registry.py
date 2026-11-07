"""Phase 5 Evidence Registry 测试（§39/§64）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.fail_closed import FailClosedError  # noqa: E402
from engines.yuhai_ziping.evidence.evidence_registry import EvidenceRegistry  # noqa: E402
from engines.yuhai_ziping.rule.rule_engine import RuleEngine  # noqa: E402


@pytest.fixture(scope="module")
def evd():
    return EvidenceRegistry()


def test_every_rule_has_evidence(evd):
    """§64：每条 Rule → Source → Evidence 链完整。"""
    for r in evd.rules:
        assert evd.evidence_ids_for(r["rule_id"]), f"Rule 无 Evidence: {r['rule_id']}"


def test_no_broken_chain(evd):
    assert evd.gaps == [], "存在断链 Gap（不得强行通过）"


def test_evidence_record_structure(evd):
    """§39 Evidence Record 字段齐全。"""
    for rec in evd._by_id.values():
        assert set(rec.keys()) >= {"evidence_id", "source_id", "source_location",
                                   "text_layer", "evidence_grade", "rule_ids", "fact_ids"}
        assert rec["evidence_id"].startswith("EVD-YHZP-")
        assert rec["evidence_grade"] in {"A", "B", "C", "D"}


def test_evidence_id_unique(evd):
    ids = [r["evidence_id"] for r in evd._by_id.values()]
    assert len(ids) == len(set(ids))


def test_attach_evidence_to_fact(evd):
    """Rule Engine fact → attach evidence_ids。"""
    eng = RuleEngine()
    fact = eng.run({"stem": "甲", "partner_stem": "己"})[0]
    evd.attach(fact)
    assert fact["evidence_ids"]
    for eid in fact["evidence_ids"]:
        assert eid in evd._by_id
        src = evd._by_id[eid]
        assert src["source_id"] in fact["source_ids"]


def test_export_generates_files(evd, tmp_path):
    evd.export(evd_out=tmp_path / "evidence.jsonl", gap_out=tmp_path / "gap.jsonl")
    ev = [json.loads(l) for l in (tmp_path / "evidence.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    gp = [json.loads(l) for l in (tmp_path / "gap.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert ev
    # 4 条 UNVERIFIED source → 4 条 UNVERIFIED_SOURCE gap
    assert sum(1 for g in gp if g["type"] == "UNVERIFIED_SOURCE") == 4
    assert all(g["type"] != "BROKEN_CHAIN" for g in gp)
