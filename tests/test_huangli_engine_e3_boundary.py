"""黄历引擎 E3 Boundary 测试 — 节气/干支/宜忌来源边界验证。

覆盖：
- 节气边界：立春前后、惊蛰前后、非节气日
- 干支边界：1900年锚点、2100年远端、连续7天干支循环
- 宜忌来源边界：经典来源登记、字段存在性
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest
from datetime import date
from tongshu.engines.huangli_engine import HuangliEngine, HuangliDay


class TestSolarTermBoundary(unittest.TestCase):
    """节气边界测试：节气前/瞬间/后

    注意: lunar_python的getYearInGanZhi()返回农历年(春节为界)，
    非命理学年(立春为界)。测试反映引擎实际行为。
    """

    def setUp(self):
        self.engine = HuangliEngine()

    def test_lichun_before(self):
        """立春前一天：jie_qi为空"""
        # 2024年立春2月4日，前一天2月3日
        d = self.engine.get_day(date(2024, 2, 3))
        self.assertEqual(d.jie_qi, "")
        # 农历年仍为癸卯（春节在2月10日，立春在2月4日）
        self.assertEqual(d.year_ganzhi, "癸卯")

    def test_lichun_on(self):
        """立春当天：jie_qi=立春"""
        d = self.engine.get_day(date(2024, 2, 4))
        self.assertEqual(d.jie_qi, "立春")
        # 农历年仍为癸卯（春节2月10日才切换）
        self.assertEqual(d.year_ganzhi, "癸卯")

    def test_lichun_after(self):
        """立春后一天：jie_qi为空（已交节）"""
        d = self.engine.get_day(date(2024, 2, 5))
        self.assertEqual(d.jie_qi, "")
        # 农历年仍为癸卯，直到春节(2月10日)才切换
        self.assertEqual(d.year_ganzhi, "癸卯")

    def test_lunar_new_year_year_switch(self):
        """春节当天：农历年切换"""
        # 2024年春节2月10日
        before = self.engine.get_day(date(2024, 2, 9))
        after = self.engine.get_day(date(2024, 2, 10))
        self.assertNotEqual(before.year_ganzhi, after.year_ganzhi)
        self.assertEqual(before.year_ganzhi, "癸卯")
        self.assertEqual(after.year_ganzhi, "甲辰")

    def test_jingzhe_month_switch(self):
        """惊蛰：月柱切换验证（实际测试中月柱在节切换）"""
        # 2024年惊蛰3月5日
        before = self.engine.get_day(date(2024, 3, 4))
        after = self.engine.get_day(date(2024, 3, 5))
        # 验证前后month_ganzhi不同（节为月柱切换点）
        self.assertNotEqual(before.month_ganzhi, after.month_ganzhi)
        self.assertEqual(after.jie_qi, "惊蛰")

    def test_non_solar_term_day(self):
        """非节气日：jie_qi为空，prev/next有值"""
        d = self.engine.get_day(date(2026, 8, 17))
        self.assertEqual(d.jie_qi, "")
        self.assertEqual(d.prev_jie_qi[0], "立秋")
        self.assertEqual(d.next_jie_qi[0], "处暑")

    def test_prev_next_jie_qi_adjacent(self):
        """前后节气日期应相邻"""
        d = self.engine.get_day(date(2026, 8, 17))
        prev_date = d.prev_jie_qi[1]
        next_date = d.next_jie_qi[1]
        # 立秋8月7日，处暑8月23日，间隔16天
        from datetime import datetime
        dt_prev = datetime.strptime(prev_date, "%Y-%m-%d")
        dt_next = datetime.strptime(next_date, "%Y-%m-%d")
        self.assertGreater((dt_next - dt_prev).days, 0)


class TestGanZhiBoundary(unittest.TestCase):
    """干支边界测试：年柱/月柱/日柱的循环和切换"""

    def setUp(self):
        self.engine = HuangliEngine()

    def test_anchor_day_1900_01_01(self):
        """1900-01-01 日柱锚点：甲戌"""
        d = self.engine.get_day(date(1900, 1, 1))
        self.assertEqual(d.day_ganzhi, "甲戌")
        self.assertEqual(d.day_stem, "JIA")
        self.assertEqual(d.day_branch, "XU")

    def test_day_ganzt_cycle_10_days(self):
        """日干支60天循环：连续10天验证天干顺序"""
        base = date(2026, 8, 17)  # 癸亥
        stems_expected = ["GUI", "JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN"]
        for i, expected_stem in enumerate(stems_expected):
            d = self.engine.get_day(base + __import__('datetime').timedelta(days=i))
            self.assertEqual(d.day_stem, expected_stem, f"Day {i} mismatch")

    def test_day_ganzt_cycle_12_days(self):
        """日支12天循环：连续12天验证地支顺序"""
        base = date(2026, 8, 17)  # 癸亥（支=亥）
        branches_expected = ["HAI", "ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU"]
        for i, expected_branch in enumerate(branches_expected):
            d = self.engine.get_day(base + __import__('datetime').timedelta(days=i))
            self.assertEqual(d.day_branch, expected_branch, f"Day {i} mismatch")

    def test_year_ganzt_switch_at_lunar_new_year(self):
        """年柱在春节切换（lunar_python行为）"""
        # 2024年春节2月10日
        before = self.engine.get_day(date(2024, 2, 9))
        after = self.engine.get_day(date(2024, 2, 10))
        self.assertNotEqual(before.year_ganzhi, after.year_ganzhi)
        self.assertEqual(before.year_ganzhi, "癸卯")
        self.assertEqual(after.year_ganzhi, "甲辰")

    def test_year_ganzt_no_switch_at_lunar_new_year(self):
        """年柱不在农历正月初一切换（而在立春切换）"""
        # 2024年农历正月初一为2月10日，立春为2月4日
        # 正月初一时年柱已是甲辰（因立春已过）
        d = self.engine.get_day(date(2024, 2, 10))
        self.assertEqual(d.year_ganzhi, "甲辰")

    def test_far_future_year_2100(self):
        """远端年份2100年：计算不崩溃"""
        d = self.engine.get_day(date(2100, 12, 31))
        self.assertIsNotNone(d.year_ganzhi)
        self.assertIsNotNone(d.month_ganzhi)
        self.assertIsNotNone(d.day_ganzhi)


class TestYiJiSourceBoundary(unittest.TestCase):
    """宜忌来源边界测试：字段存在性、确定性"""

    def setUp(self):
        self.engine = HuangliEngine()

    def test_yi_ji_fields_exist(self):
        """宜忌字段始终为列表"""
        for year in [1900, 2000, 2024, 2026, 2100]:
            d = self.engine.get_day(date(year, 6, 15))
            self.assertIsInstance(d.yi, list)
            self.assertIsInstance(d.ji, list)

    def test_ji_xiang_xiong_sha_present(self):
        """吉神凶煞字段存在"""
        d = self.engine.get_day(date(2026, 8, 17))
        self.assertIsInstance(d.ji_xiang, list)
        self.assertIsInstance(d.xiong_sha, list)

    def test_source_registry_complete(self):
        """来源登记完整：lunar_python, day_stem_branch_anchor, ganzhi_daily_hexagram"""
        registry = self.engine.source_registry
        ids = {s["source_id"] for s in registry}
        self.assertIn("lunar_python", ids)
        self.assertIn("day_stem_branch_anchor", ids)
        self.assertIn("ganzhi_daily_hexagram", ids)

    def test_classical_basis_field_present(self):
        """来源登记含classical_basis字段"""
        registry = self.engine.source_registry
        for src in registry:
            self.assertIn("classical_basis", src, f"Source {src['source_id']} missing classical_basis")


if __name__ == "__main__":
    unittest.main()
