# -*- coding: utf-8 -*-
"""Z21: 大限/流年论断层测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals
from tongshu.engines.ziwei.rules.interpretation import interpret_with_nihai
from tongshu.engines.ziwei.rules.decadal import build_decadal_fortune, build_liunian_fortune


def _chart():
    engine = ZiweiEngine()
    return engine.full_chart((1983, 9, 29), 11, "male")


class TestDecadalFortune:
    def test_12_palaces_all(self):
        """大限 12 宫全量输出"""
        dec = build_decadal_fortune(_chart())
        assert len(dec) == 12

    def test_age_range_sequence(self):
        """大限年龄连续递增（命宫5-14起）"""
        dec = build_decadal_fortune(_chart())
        ranges = [d["age_range"] for d in dec]
        # 按起始年龄排序后相邻衔接
        ranges.sort()
        for a, b in zip(ranges, ranges[1:]):
            assert a[1] + 1 == b[0], f"大限断层: {a} -> {b}"

    def test_decadal_sihua(self):
        """命宫大限丙辰 → 丙干四化 天同/天机/文昌/廉贞"""
        dec = {d["palace"]: d for d in build_decadal_fortune(_chart())}
        ming = dec["命宫"]
        assert ming["stem"] == "丙"
        assert ming["branch"] == "辰"
        assert ming["sihua"][0] == "天同"  # 丙干化禄天同
        assert len(ming["sihua"]) == 4

    def test_palace_assertions(self):
        """大限宫位断言非空（宫位总论断言）"""
        dec = build_decadal_fortune(_chart())
        assert all(len(d["assertions"]) >= 1 for d in dec)

    def test_output_field(self):
        """interpret_with_nihai 输出含 decadal_fortune"""
        chart = _chart()
        sig = compute_multi_method_signals(chart)
        out = interpret_with_nihai(sig, chart)
        assert len(out.decadal_fortune) == 12
        d = out.to_dict()
        assert len(d["decadal_fortune"]) == 12


class TestLiuNian:
    def test_2026_palace(self):
        """2026 丙午年流年落夫妻宫（命宫地支辰起数）"""
        ln = build_liunian_fortune(_chart(), 2026)
        assert ln["year"] == 2026
        assert ln["branch"] == "午"
        assert ln["stem"] == "丙"
        assert ln["palace"] == "夫妻"

    def test_2025_palace(self):
        """2025 乙巳年流年落兄弟宫"""
        ln = build_liunian_fortune(_chart(), 2025)
        assert ln["palace"] == "兄弟"

    def test_sihua_and_assertions(self):
        """流年四化 + 断言"""
        ln = build_liunian_fortune(_chart(), 2026)
        assert len(ln["sihua"]) == 4
        assert len(ln["assertions"]) >= 1

    def test_output_field(self):
        """interpret_with_nihai 输出含 liunian_fortune"""
        chart = _chart()
        sig = compute_multi_method_signals(chart)
        out = interpret_with_nihai(sig, chart)
        assert out.liunian_fortune["year"] == 2026
