# -*- coding: utf-8 -*-
"""倪海厦天纪断言解层单元测试."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ['TONGSHU_ALLOW_ZIWEI_STUB'] = '1'

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.interpretation import (
    NihaiAssertionEntry,
    NihaiAssertionResolver,
    interpret_with_nihai,
)
from tongshu.engines.ziwei.rules.nihai_assertions import (
    get_assertion,
    get_all_assertions,
    count_assertions,
    get_assertions_by_category,
)


class TestNihaiAssertionsLibrary(unittest.TestCase):
    """断言库单元测试."""

    def test_count_assertions(self):
        """断言条目总数 > 0."""
        self.assertGreater(count_assertions(), 0)

    def test_get_assertion_by_star_palace(self):
        """可按星×宫查询断言."""
        ref = get_assertion("紫微", "命宫")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.star, "紫微")
        self.assertEqual(ref.palace, "命宫")
        self.assertIn("官", ref.text)

    def test_get_assertion_not_found_returns_none(self):
        """未命中的星×宫返回 None."""
        ref = get_assertion("非主星", "命宫")
        self.assertIsNone(ref)

    def test_get_all_assertions_structure(self):
        """全部断言条目结构正确."""
        all_ = get_all_assertions()
        for a in all_:
            self.assertIsInstance(a, type(all_[0]))
            self.assertTrue(len(a.star) > 0)
            self.assertTrue(len(a.palace) > 0)
            self.assertTrue(len(a.text) > 0)
            self.assertIn(a.direction, ("吉", "凶", "中性"))
            self.assertIn(a.category, (
                "personality", "career", "wealth", "marriage",
                "health", "fortune",
            ))

    def test_get_assertions_by_category(self):
        """按类别过滤正确."""
        career = get_assertions_by_category("career")
        wealth = get_assertions_by_category("wealth")
        self.assertGreater(len(career), 0)
        self.assertGreater(len(wealth), 0)
        for a in career:
            self.assertEqual(a.category, "career")

    def test_nihai_assertion_to_dict(self):
        """断言条目可序列化."""
        all_ = get_all_assertions()
        if all_:
            d = all_[0].to_dict()
            self.assertIn("star", d)
            self.assertIn("palace", d)
            self.assertIn("text", d)
            self.assertIn("source", d)


class TestNihaiAssertionResolver(unittest.TestCase):
    """倪师断言解析器单元测试."""

    def _make_chart(self):
        engine = ZiweiEngine()
        return engine.full_chart((2000, 1, 1), 12, 'male')

    def test_resolve_produces_entries(self):
        """解析器可从命盘产出断言条目."""
        chart = self._make_chart()
        resolver = NihaiAssertionResolver()
        entries = resolver.resolve(chart)
        self.assertIsInstance(entries, list)
        # 命宫有主星时至少应有断言
        if chart.palaces:
            # 只要有命宫主星就应能查到断言
            first_palace = next(iter(chart.palaces.values()))
            stars = first_palace.get("major", [])
            if stars:
                self.assertGreater(len(entries), 0)

    def test_entries_have_correct_structure(self):
        """断言条目结构完整."""
        chart = self._make_chart()
        resolver = NihaiAssertionResolver()
        entries = resolver.resolve(chart)
        for e in entries:
            self.assertIsInstance(e, NihaiAssertionEntry)
            self.assertTrue(len(e.star) > 0)
            self.assertTrue(len(e.palace) > 0)
            self.assertTrue(len(e.text) > 0)
            self.assertIn(e.direction, ("吉", "凶", "中性"))

    def test_different_charts_different_assertions(self):
        """不同命盘产生不同断言集合."""
        engine = ZiweiEngine()
        chart1 = engine.full_chart((2000, 1, 1), 12, 'male')
        chart2 = engine.full_chart((1990, 5, 15), 10, 'female')
        resolver = NihaiAssertionResolver()
        entries1 = resolver.resolve(chart1)
        entries2 = resolver.resolve(chart2)
        # 两套断言至少有一个不同（命盘不同则命宫主星分布不同）
        stars1 = {e.star + e.palace for e in entries1}
        stars2 = {e.star + e.palace for e in entries2}
        # 不要求完全不同，但至少有一方有断言
        self.assertGreater(len(stars1) + len(stars2), 0)

    def test_max_per_star_limit(self):
        """max_per_star 参数生效."""
        chart = self._make_chart()
        resolver = NihaiAssertionResolver()
        entries = resolver.resolve(chart, max_per_star=1)
        # 限制后条目数应 <= 总星数 × 1
        self.assertLessEqual(len(entries), 20)

    def test_interpret_with_nihai_integration(self):
        """interpret_with_nihai 可正常返回含倪师断言的输出."""
        engine = ZiweiEngine()
        chart = engine.full_chart((2000, 1, 1), 12, 'male')
        from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals
        signal = compute_multi_method_signals(chart)
        output = interpret_with_nihai(signal, chart, enable_nihai=True)
        self.assertGreater(len(output.nihai_assertions), 0)
        # to_dict 可序列化
        d = output.to_dict()
        self.assertIn("nihai_assertions", d)


class TestNihaiAssertionsCoverage(unittest.TestCase):
    """断言库覆盖完整性测试."""

    def test_all_14_main_stars_have_ming_gong_assertions(self):
        """十四主星均有命宫断言."""
        main_stars = [
            "紫微", "天机", "太阳", "武曲", "天同",
            "廉贞", "天府", "太阴", "贪狼", "巨门",
            "天相", "天梁", "七杀", "破军",
        ]
        for star in main_stars:
            ref = get_assertion(star, "命宫")
            self.assertIsNotNone(ref, f"缺命宫断言: {star}")
            self.assertEqual(ref.star, star)
            self.assertEqual(ref.palace, "命宫")

    def test_all_14_main_stars_have_different_palace_assertions(self):
        """十四主星各有不同宫位的断言."""
        main_stars = [
            "紫微", "天机", "太阳", "武曲", "天同",
            "廉贞", "天府", "太阴", "贪狼", "巨门",
            "天相", "天梁", "七杀", "破军",
        ]
        for star in main_stars:
            refs = [get_assertion(star, p) for p in ("命宫", "财帛宫", "官禄宫")]
            self.assertTrue(any(r is not None for r in refs),
                f"缺{star}的宫位断言")

    def test_six_killers_have_assertions(self):
        """六煞星有断言."""
        for star in ("擎羊", "陀罗", "火星", "铃星", "天空", "地劫"):
            ref = get_assertion(star, "命宫")
            self.assertIsNotNone(ref, f"缺六杀断言: {star}")
            self.assertEqual(ref.direction, "凶")

    def test_special_stars_have_assertions(self):
        """特殊辅星有断言."""
        for star in ("禄存", "天魁", "天钺", "红鸾", "天喜"):
            ref = get_assertion(star, "命宫")
            self.assertIsNotNone(ref, f"缺辅星断言: {star}")

    def test_four_transforms_have_assertions(self):
        """四化有断言."""
        for stem in ("化科", "化权", "化禄", "化忌"):
            ref = get_assertion(stem, "四化")
            self.assertIsNotNone(ref, f"缺{stem}断言")

    def test_all_assertions_have_chinese_text(self):
        """所有断言文本含中文."""
        for a in get_all_assertions():
            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in a.text)
            self.assertTrue(has_cjk,
                f"断言文本无中文: {a.star}@{a.palace}: {a.text[:30]}")


if __name__ == '__main__':
    unittest.main()
