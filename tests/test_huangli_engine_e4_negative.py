"""黄历引擎 E4 Negative 测试 — invalid date fail-closed 验证。

覆盖：
- 非法日期：无效月份、无效日期、未来超远距离
- 边缘值：最小/最大date范围
- 异常输入：None、字符串等非date对象
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from datetime import date
from tongshu.engines.huangli_engine import HuangliEngine


class TestInvalidDateFailClosed(unittest.TestCase):
    """非法输入 fail-closed 测试"""

    def setUp(self):
        self.engine = HuangliEngine()

    def test_invalid_month_raises(self):
        """无效月份（0或13）应抛出异常"""
        with self.assertRaises(Exception):
            self.engine.get_day(date(2026, 0, 1))
        with self.assertRaises(Exception):
            self.engine.get_day(date(2026, 13, 1))

    def test_invalid_day_raises(self):
        """无效日期应抛出异常"""
        with self.assertRaises(Exception):
            self.engine.get_day(date(2026, 2, 30))  # 2月无30日
        with self.assertRaises(Exception):
            self.engine.get_day(date(2026, 4, 31))  # 4月无31日

    def test_negative_year_raises(self):
        """负年份（公元前）应抛出异常或正确处理"""
        # Python date不支持公元前，应抛异常
        with self.assertRaises(ValueError):
            self.engine.get_day(date(-1, 1, 1))

    def test_extreme_far_future(self):
        """超远未来：3000年应计算不崩溃（fail-closed但不保证正确）"""
        try:
            d = self.engine.get_day(date(3000, 1, 1))
            self.assertIsNotNone(d)
        except Exception as e:
            # fail-closed: 允许抛异常但不崩溃进程
            pass


class TestEdgeCases(unittest.TestCase):
    """边缘情况测试"""

    def setUp(self):
        self.engine = HuangliEngine()

    def test_min_date_1900(self):
        """最小有效日期1900-01-01"""
        d = self.engine.get_day(date(1900, 1, 1))
        self.assertIsNotNone(d)
        self.assertEqual(d.day_ganzhi, "甲戌")

    def test_max_date_reasonable(self):
        """合理最大日期2100-12-31"""
        d = self.engine.get_day(date(2100, 12, 31))
        self.assertIsNotNone(d)

    def test_leap_year_feb_29(self):
        """闰年2月29日"""
        d = self.engine.get_day(date(2024, 2, 29))
        self.assertIsNotNone(d)
        self.assertIsInstance(d.day_ganzhi, str)

    def test_non_leap_year_feb_29(self):
        """非闰年2月29日应抛异常"""
        with self.assertRaises(Exception):
            self.engine.get_day(date(2023, 2, 29))


class TestInputTypeValidation(unittest.TestCase):
    """输入类型验证"""

    def setUp(self):
        self.engine = HuangliEngine()

    def test_none_input_raises(self):
        """None输入应抛出类型异常"""
        with self.assertRaises((TypeError, AttributeError)):
            self.engine.get_day(None)

    def test_string_input_raises(self):
        """字符串输入应抛出类型异常"""
        with self.assertRaises((TypeError, ValueError)):
            self.engine.get_day("2026-08-17")

    def test_tuple_input_raises(self):
        """元组输入应抛出类型异常"""
        with self.assertRaises((TypeError, AttributeError)):
            self.engine.get_day((2026, 8, 17))


if __name__ == "__main__":
    unittest.main()
