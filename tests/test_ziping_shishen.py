"""十神域: p0 五行力量 → 最旺十神, 对照药/病判吉凶（原典·论十神）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.tongshu.reasoning.ziping_bridge import _engines_p0_synthesis


def _pillars(*p):
    return {pos: [gz[0], gz[1]] for pos, gz in zip(("year", "month", "day", "hour"), p)}


@pytest.mark.parametrize(
    "case,expected",
    [
        # 002 戊子 癸亥 庚寅 戊寅: 食伤(水)当权且为病 → 十神凶
        (("戊子", "癸亥", "庚寅", "戊寅"), "SEMANTIC_NEGATIVE"),
        # 004 乙酉 甲申 丁巳 庚戌: 财(金)最旺且为用药 → 十神吉
        (("乙酉", "甲申", "丁巳", "庚戌"), "SEMANTIC_POSITIVE"),
        # 1990 庚午 戊寅 乙丑 壬午: 最旺食伤(火)非喜非忌 → 不硬断
        (("庚午", "戊寅", "乙丑", "壬午"), "UNKNOWN"),
    ],
)
def test_shishen_conclusion(case, expected):
    from engines.production_entry import production_entry, FrozenCanonicalBaziChart

    p = _pillars(*case)
    res = production_entry(FrozenCanonicalBaziChart(pillars=p))
    synth = _engines_p0_synthesis(res, p)
    assert synth.shishen.conclusion.value == expected
    assert synth.shishen.reasoning


def test_shishen_evidence_resolves():
    from engines.production_entry import production_entry, FrozenCanonicalBaziChart
    from src.tongshu.reasoning import p0_evidence

    p = _pillars("戊子", "癸亥", "庚寅", "戊寅")
    res = production_entry(FrozenCanonicalBaziChart(pillars=p))
    synth = _engines_p0_synthesis(res, p)
    refs = synth.shishen.evidence_refs
    assert refs
    assert "FOUNDATION.RELATION.SHI_SHEN.001" in refs
    resolved = [r for r in refs if p0_evidence.lookup(r)]
    assert resolved
    assert any(r in resolved for r in ("FOUNDATION.RELATION.SHI_SHEN.001",))
    assert "FOUNDATION.RELATION.SHI_SHEN.001" in synth.shishen.rule_refs


def test_pipeline_emits_shishen_claim():
    """端到端: 十神凶 claim 进入 V13 断言并过审计闸。"""
    from pathlib import Path as _P
    from tongshu.pipeline import TONGSHUPipeline

    from datetime import date

    pipeline = TONGSHUPipeline.for_demo(_P(r"D:\shuntian"))
    res = pipeline.run(
        analysis_date=date(2024, 1, 1),
        birth_date=(1984, 12, 7, 16),
        gender="male",
        theme="WORK",
    )
    assert res.validation_passed is True
    claims = res.canonical.atomic_claims
    ids = [c.get("claim_id") for c in claims]
    assert "AC-ZP-shishen-semantic_negative" in ids
    target = [c for c in claims if c.get("claim_id") == "AC-ZP-shishen-semantic_negative"][0]
    assert target.get("evidence_refs")
    assert "FOUNDATION.RELATION.SHI_SHEN.001" in target.get("rule_refs", [])
