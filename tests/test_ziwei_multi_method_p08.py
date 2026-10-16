"""
P0-8 / Z17 Tests — MultiMethodSignal 两派集成器

8 维度验证 (Z17 两派收敛后):
  1. 两派集成成功 (2 MethodBundle: SANHE + QINTIAN)
  2. 派别隔离 (各派 evidence_bindings 互不污染)
  3. graph_id 唯一
  4. fail-closed (空 chart → 不 crash)
  5. evidence grade 保留
  6. unmatched 列表准确
  7. draft_detected 全为空
  8. 跨派别共识检测
"""

from __future__ import annotations

import pytest
from pathlib import Path
import sys

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.ziwei.rules.multi_method import (
    compute_multi_method_signals,
    MultiMethodSignal, MethodBundle, MethodMatch,
)
from tongshu.engines.ziwei.rules.feixing_rule_graph import (
    PalaceStemFact, FlyingTransformFact,
)


# ----- Test chart factory -----

def make_chart(*, birth_year=1984, palaces=None, palace_stems=None, flying=None):
    """通用 Mock chart (兼容两派 API)"""
    class MockChart:
        pass
    c = MockChart()
    c.birth_year = birth_year
    c.palaces = palaces or {}
    c.palace_stems = palace_stems or []
    c.flying_transforms = flying or []
    return c


def full_12_palaces_dict():
    """12 宫齐全 dict (钦天要)"""
    return {
        n: {"major": [], "minor": [], "stem": "甲", "branch": "亥", "main_stars": []}
        for n in ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                  "迁移", "交友", "官禄", "田宅", "福德", "父母"]
    }


def full_12_palace_stems():
    """12 宫齐全 PalaceStemFact list (钦天要)"""
    return [PalaceStemFact(palace_name=n, stem="甲", branch="亥")
            for n in ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                      "迁移", "交友", "官禄", "田宅", "福德", "父母"]]


def jiazi_flying():
    """1984 甲子年自化样本"""
    return [
        FlyingTransformFact(
            source_palace="命宫", source_stem="甲",
            transformation="化忌", target_star="太阳",
            target_palace="命宫", direction="self",
        ),
    ]


# ============================================================
# 维度 1: 两派集成
# ============================================================

class TestIntegration:
    def test_two_bundles(self):
        """南派 + 北派 = 2 MethodBundle"""
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        sig = compute_multi_method_signals(chart)
        assert "SANHE" in sig.bundles
        assert "QINTIAN" in sig.bundles
        assert len(sig.bundles) == 2

    def test_sanhe_without_qintian_override(self):
        """include_sanhe=False 时不含南派"""
        chart = make_chart(palaces=full_12_palaces_dict())
        sig = compute_multi_method_signals(chart, include_sanhe=False)
        assert "SANHE" not in sig.bundles
        assert len(sig.bundles) == 1


# ============================================================
# 维度 2: 派别隔离 (命名前缀)
# ============================================================

class TestMethodIsolation:
    @pytest.fixture
    def sig(self):
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        return compute_multi_method_signals(chart)

    def test_sanhe_sanhe_prefix(self, sig):
        """南派 rule_id 前缀 SANHE-*"""
        for m in sig.bundles["SANHE"].matched_rules:
            assert m.rule_id.startswith("SANHE-"), f"SANHE 命名前缀错: {m.rule_id}"

    def test_qintian_qtn_prefix(self, sig):
        """钦天 rule_id 前缀 QTN-*"""
        for rid in sig.bundles["QINTIAN"].evidence_bindings:
            assert rid.startswith("QTN-"), f"QINTIAN 命名前缀错: {rid}"

    def test_rule_prefixes_disjoint(self, sig):
        """两派 rule_id 互不重名"""
        sanhe = {m.rule_id for m in sig.bundles["SANHE"].matched_rules}
        qtn = set(sig.bundles["QINTIAN"].evidence_bindings)
        assert sanhe.isdisjoint(qtn)


# ============================================================
# 维度 3: graph_id 唯一
# ============================================================

class TestGraphIdUniqueness:
    def test_graph_ids_unique(self):
        """2 bundles, 2 unique graph_ids"""
        chart = make_chart(palaces=full_12_palaces_dict())
        sig = compute_multi_method_signals(chart)
        gids = [b.graph_id for b in sig.bundles.values()]
        assert len(set(gids)) == len(gids)


# ============================================================
# 维度 4: fail-closed (空 chart)
# ============================================================

class TestFailClosed:
    def test_empty_chart_no_crash(self):
        """空 chart 不 crash"""
        chart = make_chart()
        sig = compute_multi_method_signals(chart)
        assert sig.compute_status in ("OK", "PARTIAL")

    def test_no_palaces_no_flying(self):
        """palaces=空, flying=空 → QINTIAN 仍 OK (不 crash)"""
        chart = make_chart(birth_year=1990)
        sig = compute_multi_method_signals(chart)
        assert sig.compute_status in ("OK", "PARTIAL")


# ============================================================
# 维度 5: evidence grade 保留
# ============================================================

class TestEvidenceGrade:
    def test_qintian_evidence_grade_1(self):
        """钦天 evidence grade=1 全部保留"""
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        sig = compute_multi_method_signals(chart)
        for rid, info in sig.bundles["QINTIAN"].evidence_bindings.items():
            # Z46: 014 北派身宫 / Z66: 035 五行局×身宫为 derived（grade=3），其余 production 须 grade=1
            if rid in ('QTN-CMB-014', 'QTN-CMB-035'):
                assert info["grade"] == 3, f"{rid} grade={info['grade']} (derived 应为 3)"
            else:
                assert info["grade"] == 1, f"{rid} grade={info['grade']} (应为 1)"

    def test_sanhe_evidence_grade_present(self):
        """南派匹配项均带 evidence_grade"""
        chart = make_chart(palaces=full_12_palaces_dict())
        sig = compute_multi_method_signals(chart)
        for m in sig.bundles["SANHE"].matched_rules:
            assert m.evidence_grade in (0, 1, 2)


# ============================================================
# 维度 6: unmatched 列表
# ============================================================

class TestUnmatched:
    def test_qintian_14_rules_total(self):
        """Z46: 钦天 rule_count=9（Z44 8条 + Z46 北派身宫 + Z48 生年四化015 + Z49 流年四化016 + Z50 大限四化017 + Z51 自化018 + Z52 斗君019）, matched + unmatched = 14"""
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        sig = compute_multi_method_signals(chart)
        qtn = sig.bundles["QINTIAN"]
        assert qtn.rule_count == 60  # Z74i +059/060 双忌三忌；前序 Z74g +058
        total = len(qtn.matched_rules) + len(qtn.unmatched_production_rules)
        assert total == 60  # Z74i +059/060 双忌三忌；前序 Z74g +058


# ============================================================
# 维度 7: draft_detected 全空
# ============================================================

class TestDraftNeverTrigger:
    @pytest.fixture
    def sig(self):
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        return compute_multi_method_signals(chart)

    def test_qintian_draft_empty(self, sig):
        assert sig.bundles["QINTIAN"].draft_detected == []


# ============================================================
# 维度 8: 跨派别共识
# ============================================================

class TestCrossMethodConsensus:
    def test_consensus_detection_no_crash(self):
        """跨派共识检测不 crash（两派事实交集可能为空，不强制命中）"""
        chart = make_chart(
            birth_year=1984,
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        sig = compute_multi_method_signals(chart)
        assert isinstance(sig.cross_method_consensus, list)


# ============================================================
# 额外: total_matched_rules 聚合
# ============================================================

class TestAggregation:
    def test_total_matched_aggregation(self):
        """total_matched_rules = 两派 matched_rules 之和"""
        chart = make_chart(
            palaces=full_12_palaces_dict(),
            palace_stems=full_12_palace_stems(),
            flying=jiazi_flying(),
        )
        sig = compute_multi_method_signals(chart)
        expected = sum(len(b.matched_rules) for b in sig.bundles.values())
        assert sig.total_matched_rules == expected
