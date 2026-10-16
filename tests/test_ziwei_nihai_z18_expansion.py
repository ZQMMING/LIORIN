# -*- coding: utf-8 -*-
"""Z18 断言库扩容专项测试.

覆盖：
  - 同星宫多条断言（get_assertions）
  - 断言库总量（Z18 由 44 扩容至 80+）
  - 十二宫总论断言齐全
  - 同星宫多条断言端到端输出
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ['TONGSHU_ALLOW_ZIWEI_STUB'] = '1'

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.nihai_assertions import (
    get_assertion,
    get_assertions,
    get_all_assertions,
    count_assertions,
    count_keys,
)
from tongshu.engines.ziwei.rules.interpretation import (
    NihaiAssertionResolver,
    interpret_with_nihai,
)


class TestZ18MultiAssertions(unittest.TestCase):
    """Z18: 同星宫多条断言."""

    def test_get_assertions_returns_multiple(self):
        """紫微命宫应有 2+ 条断言（Z18 list 结构）."""
        items = get_assertions("紫微", "命宫")
        self.assertGreaterEqual(len(items), 2)

    def test_get_assertion_returns_first(self):
        """get_assertion（旧接口）返回首条."""
        first = get_assertion("紫微", "命宫")
        items = get_assertions("紫微", "命宫")
        self.assertIsNotNone(first)
        self.assertEqual(first, items[0])

    def test_total_count_grew(self):
        """断言总数 ≥ 80（Z17 为 44，Z18 扩容）."""
        self.assertGreaterEqual(count_assertions(), 80)
        self.assertGreaterEqual(count_keys(), 50)

    def test_all_assertions_distinct(self):
        """断言文本重复仅允许出现在六杀组（共用总论原话）."""
        from collections import Counter
        all_a = get_all_assertions()
        texts = Counter(a.text for a in all_a)
        dup_stars = {a.star for a in all_a if texts[a.text] > 1}
        SIX_KILLERS = {"擎羊", "陀罗", "火星", "铃星", "天空", "地劫"}
        for s in dup_stars:
            self.assertIn(s, SIX_KILLERS,
                f"非六杀断言文本重复: {s}")


class TestZ18PalaceOverviews(unittest.TestCase):
    """Z18: 十二宫总论断言齐全."""

    PALACES = ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫",
               "迁移宫", "仆役宫", "官禄宫", "田宅宫", "福德宫", "父母宫"]

    def test_all_palaces_have_overview(self):
        """十一宫均有总论断言."""
        for p in self.PALACES:
            items = get_assertions(p, p)
            self.assertGreaterEqual(len(items), 1,
                f"缺{p}总论断言")
            self.assertEqual(items[0].palace, p)

    def test_palace_overview_categories(self):
        """宫位总论类别合理."""
        for p in self.PALACES:
            items = get_assertions(p, p)
            for a in items:
                self.assertIn(a.category,
                    ("personality", "career", "wealth", "marriage",
                     "health", "fortune"))


class TestZ18ResolverMulti(unittest.TestCase):
    """Z18: 解析器支持多条断言."""

    def _chart(self):
        return ZiweiEngine().full_chart((1983, 9, 29), 11, 'male')

    def test_same_star_palace_multiple_entries(self):
        """同一 (星,宫) 可输出多条断言条目."""
        chart = self._chart()
        resolver = NihaiAssertionResolver()
        entries = resolver.resolve(chart)
        qisha = [e for e in entries if e.star == "七杀" and e.palace == "命宫"]
        self.assertGreaterEqual(len(qisha), 2,
            f"七杀@命宫应输出 2+ 条断言, 实际 {len(qisha)}")

    def test_interpret_with_nihai_multiple(self):
        """interpret_with_nihai 输出 2+ 条倪师断言."""
        chart = self._chart()
        from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals
        signal = compute_multi_method_signals(chart)
        output = interpret_with_nihai(signal, chart)
        self.assertGreaterEqual(len(output.nihai_assertions), 2,
            f"1983 案例应输出 2+ 条断言, 实际 {len(output.nihai_assertions)}")

    def test_entries_source_attribution(self):
        """每条断言带出处."""
        chart = self._chart()
        resolver = NihaiAssertionResolver()
        for e in resolver.resolve(chart):
            self.assertTrue(len(e.source) > 0,
                f"断言缺出处: {e.star}@{e.palace}")


if __name__ == '__main__':
    unittest.main()
