# -*- coding: utf-8 -*-
"""Z74c: 流月应期层测试（QTN-CMB-054/055）"""

import sys

sys.path.insert(0, r"D:\shuntian-ziwei-v2\src")

import pytest

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.qintian.combinations import PRODUCTION_DETECTORS


@pytest.fixture(scope="module")
def engine():
    return ZiweiEngine()


class TestQtnCmbZ74c:
    """流月四化应用（斗君）+ 流月化忌入天刑（应期到月）。"""

    def test_rules_registered(self):
        ids = [d.__name__ for d in PRODUCTION_DETECTORS]
        assert any("054_liuyue" in n for n in ids)
        assert any("055_liuyue_ji_tianxing" in n for n in ids)

    def test_054_liuyue_sihua_data(self, engine):
        """1983 盘流月 1 → 钦天斗君（本命寅位=夫妻，地支寅）起正月，甲干太阳忌。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male", flow_month=1)
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r54 = next((c for c in hits if c.rule_id == "QTN-CMB-054"), None)
        assert r54 is not None
        f = r54.facts
        assert f["flow_month"] == 1
        assert f["doujun_palace"] == "夫妻"  # 本命盘寅位宫（钦天斗君）
        assert f["month_branch"] == "寅"
        assert f["liuyue_sihua"]["ji"] == "太阳"

    def test_054_fail_closed_no_month(self, engine):
        """无 flow_month（0）→ 054/055 fail-closed 不触发。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        assert not any(c.rule_id in ("QTN-CMB-054", "QTN-CMB-055") for c in hits)

    def test_055_liuyue_ji_tianxing(self, engine):
        """1983 盘流月 5 → 戊干天机忌入天刑宫（父母）→ 该月官非（钦天斗君验证）。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male", flow_month=5)
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r55 = next((c for c in hits if c.rule_id == "QTN-CMB-055"), None)
        assert r55 is not None
        assert r55.facts["flow_month"] == 5
        assert r55.facts["month_stem"] == "戊"
        assert r55.facts["ji_star"] == "天机"
        assert "tianxing_palace" in r55.facts

    def test_case38_liuyue_data(self, engine):
        """#38 车祸（丙戌年四月）：流月 4 → 仆役宫己干文曲忌（数据层可用）。"""
        ch = engine.full_chart((1954, 9, 30), 20, "male", flow_month=4)
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r54 = next((c for c in hits if c.rule_id == "QTN-CMB-054"), None)
        assert r54 is not None
        f = r54.facts
        assert f["month_palace"] == "仆役"  # 流月宫=天刑宫（仆役）
        assert f["month_stem"] == "己"
        assert f["liuyue_sihua"]["ji"] == "文曲"


class TestQtnCmbZ74e:
    """三吉化于六阴（056，OCR 54/55 残段可读文字落地）。"""

    def test_056_registered(self):
        ids = [d.__name__ for d in PRODUCTION_DETECTORS]
        assert any("056_sanjihua_liuyin" in n for n in ids)

    def test_056_liuyin_hit(self, engine):
        """1983 盘癸干：权巨门入子女(丑)、科太阴入疾厄(亥) → 三吉化于六阴。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r56 = next((c for c in hits if c.rule_id == "QTN-CMB-056"), None)
        assert r56 is not None
        assert r56.facts["gan"] == "癸"
        branches = {h["branch"] for h in r56.facts["liuyin_hits"]}
        assert branches <= {"巳", "未", "酉", "亥", "丑", "卯"}
        assert r56.semantic_summary

    def test_056_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        ev = EVIDENCE_BINDINGS.get("QTN-CMB-056")
        assert ev is not None
        assert "人和" in ev.verbatim_quote


class TestQtnCmbZ74g:
    """057 流年+流月组合（天地人三盘数据层，钦天斗君）。"""

    def test_057_registered(self):
        ids = [d.__name__ for d in PRODUCTION_DETECTORS]
        assert any("057_liunian_liuyue" in n for n in ids)

    def test_057_fail_closed(self, engine):
        """flow_month 缺省（0）→ 057 fail-closed 不触发。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male", flow_year=2006)
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        assert not any(c.rule_id == "QTN-CMB-057" for c in hits)

    def test_057_case38_double_ji(self, engine):
        """#38 丙戌年四月：流年甲干太阳忌@父母 + 流月己干文曲忌@福德（数据层）。"""
        ch = engine.full_chart((1954, 9, 30), 20, "male", flow_month=4, flow_year=2006)
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r57 = next((c for c in hits if c.rule_id == "QTN-CMB-057"), None)
        assert r57 is not None
        f = r57.facts
        assert f["flow_year"] == 2006
        assert f["flow_branch"] == "戌"
        assert f["flow_ji_palace"] == "父母"
        assert f["month_ji_palace"] == "福德"
        assert f["double_ji_same_palace"] is False

    def test_057_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        ev = EVIDENCE_BINDINGS.get("QTN-CMB-057")
        assert ev is not None
        assert "流月為人" in ev.verbatim_quote


class TestQtnCmbZ74h:
    """058 辛干四化（巨门禄/太阳权/文曲科/文昌忌）——钦天原文例补证。"""

    def test_058_registered(self):
        ids = [d.__name__ for d in PRODUCTION_DETECTORS]
        assert any("058_xin_gan" in n for n in ids)

    def test_058_xin_year_hit(self, engine):
        """辛年生（1991）→ 四化=巨门/太阳/文曲/文昌。"""
        ch = engine.full_chart((1991, 5, 10), 10, "female")
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        hits = detect_all_production(ch)
        r58 = next((c for c in hits if c.rule_id == "QTN-CMB-058"), None)
        assert r58 is not None
        f = r58.facts
        assert f["lu"] == "巨门" and f["quan"] == "太阳"
        assert f["ke"] == "文曲" and f["ji"] == "文昌"
        assert all(f[k] for k in ("lu_palace", "quan_palace", "ke_palace", "ji_palace"))

    def test_058_fail_closed_non_xin(self, engine):
        """非辛年（1983 癸）→ fail-closed 不触发。"""
        ch = engine.full_chart((1983, 9, 29), 11, "male")
        from tongshu.engines.ziwei.rules.qintian.combinations import detect_all_production
        assert not any(c.rule_id == "QTN-CMB-058" for c in detect_all_production(ch))

    def test_058_evidence_binding(self):
        from tongshu.engines.ziwei.rules.qintian.evidence import EVIDENCE_BINDINGS
        ev = EVIDENCE_BINDINGS.get("QTN-CMB-058")
        assert ev is not None
        assert "文曲化科入夫妻" in ev.verbatim_quote
