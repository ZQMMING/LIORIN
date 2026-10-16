# -*- coding: utf-8 -*-
"""Z22: 辅星断言接入 + 流月论断测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals
from tongshu.engines.ziwei.rules.interpretation import interpret_with_nihai, NihaiAssertionResolver
from tongshu.engines.ziwei.rules.decadal import build_liuyue_fortune, build_liunian_fortune


def _chart():
    engine = ZiweiEngine()
    return engine.full_chart((1983, 9, 29), 11, "male")


class TestMinorStarAssertions:
    def test_minor_stars_included(self):
        """命宫辅星（文昌/铃星）断言触发"""
        chart = _chart()
        entries = NihaiAssertionResolver().resolve(chart)
        stars = {e.star for e in entries}
        assert "文昌" in stars  # 命宫 minor 含文昌
        assert "铃星" in stars

    def test_total_increased(self):
        """1983 案例断言 >= 11（Z19 基线 9 + 辅星 2）"""
        chart = _chart()
        entries = NihaiAssertionResolver().resolve(chart)
        assert len(entries) >= 11


class TestLiuYue:
    def test_month_branch(self):
        """月建：1月寅、9月戌"""
        chart = _chart()
        m1 = build_liuyue_fortune(chart, 2026, 1)
        m9 = build_liuyue_fortune(chart, 2026, 9)
        assert m1["branch"] == "寅"
        assert m9["branch"] == "戌"

    def test_month_stem_wuxing_hudun(self):
        """2026 丙年九月 = 戊戌月（五虎遁：丙年正月庚寅）"""
        chart = _chart()
        m9 = build_liuyue_fortune(chart, 2026, 9)
        assert m9["stem"] == "戊"
        assert m9["branch"] == "戌"

    def test_month_sihua(self):
        """戊干四化：贪狼/太阴/右弼/天机"""
        chart = _chart()
        m9 = build_liuyue_fortune(chart, 2026, 9)
        assert m9["sihua"] == ["贪狼", "太阴", "右弼", "天机"]

    def test_month_palace(self):
        """2026-09 戊戌落迁移宫（命宫地支辰起数）"""
        chart = _chart()
        m9 = build_liuyue_fortune(chart, 2026, 9)
        assert m9["palace"] == "迁移"

    def test_month_assertions(self):
        """流月断言非空"""
        chart = _chart()
        m9 = build_liuyue_fortune(chart, 2026, 9)
        assert len(m9["assertions"]) >= 1

    def test_output_field(self):
        """interpret_with_nihai 输出含 liuyue_fortune"""
        chart = _chart()
        sig = compute_multi_method_signals(chart)
        out = interpret_with_nihai(sig, chart)
        assert out.liuyue_fortune["year"] == 2026
        d = out.to_dict()
        assert "liuyue_fortune" in d
