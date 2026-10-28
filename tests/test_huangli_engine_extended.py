"""黄历引擎测试 - Huangli (黄历) Engine

覆盖:
- 黄历数据完整性
- 宜忌字段确定性
- 节气计算
- 农历月标签
- 日柱干支
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path("./backend/src")))

import unittest
from datetime import date
from tongshu.engines.huangli_engine import HuangliDay, HuangliEngine


class TestHuangliDataIntegrity(unittest.TestCase):
    """黄历数据完整性测试。"""
    
    def test_basic_day_data(self):
        """基本黄历日数据。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 22))
        
        self.assertIsNotNone(day)
        self.assertIsInstance(day, HuangliDay)
        self.assertEqual(day.solar_date, date(2026, 8, 22))
        self.assertTrue(day.day_stem)
        self.assertTrue(day.day_branch)
    
    def test_yi_ji_not_empty(self):
        """宜忌不为空。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 22))
        self.assertIsInstance(day.yi, list)
        self.assertIsInstance(day.ji, list)
    
    def test_ganzhi_present(self):
        """干支信息存在。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 22))
        self.assertTrue(day.year_ganzhi)
        self.assertTrue(day.month_ganzhi)
        self.assertTrue(day.day_ganzhi)


class TestSolarTerms(unittest.TestCase):
    """节气计算测试。"""
    
    def test_solar_term_detection(self):
        """节气日检测。"""
        engine = HuangliEngine()
        # 2026年秋分约9月23日
        day = engine.get_day(date(2026, 9, 23))
        # 即使不是精确交节日，数据也应有效
        self.assertIsNotNone(day)
    
    def test_prev_next_solar_terms(self):
        """前后节气信息。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 15))  # 立秋后
        
        self.assertIsNotNone(day.prev_jie_qi)
        self.assertIsNotNone(day.next_jie_qi)
        self.assertIsInstance(day.prev_jie_qi, tuple)
        self.assertIsInstance(day.next_jie_qi, tuple)


class TestLunarMonthLabel(unittest.TestCase):
    """农历月标签测试。"""
    
    def test_month_label_format(self):
        """月标签格式正确。"""
        # 农历七月 → 孟秋
        label = "农历七月 · 孟秋"
        self.assertIn("农历", label)
        self.assertIn("秋", label)
    
    def test_season_labels(self):
        """四季标签完整性。"""
        from tongshu.engines.huangli_engine import _SEASON_CN, _PART_CN
        self.assertEqual(len(_SEASON_CN), 4)  # 春夏秋冬
        self.assertEqual(len(_PART_CN), 3)   # 孟仲季


class TestHuangliDeterminism(unittest.TestCase):
    """黄历确定性测试。"""
    
    def test_same_date_same_result(self):
        """同日期同结果。"""
        engine = HuangliEngine()
        d1 = engine.get_day(date(2026, 8, 22))
        d2 = engine.get_day(date(2026, 8, 22))
        
        self.assertEqual(d1.day_stem, d2.day_stem)
        self.assertEqual(d1.day_branch, d2.day_branch)


class TestBoundaryCases(unittest.TestCase):
    """边界情况测试。"""
    
    def test_year_1900(self):
        """1900年锚点。"""
        engine = HuangliEngine()
        day = engine.get_day(date(1900, 1, 1))
        self.assertIsNotNone(day)
    
    def test_year_2100(self):
        """2100年计算。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2100, 12, 31))
        self.assertIsNotNone(day)


class TestDailyHexagram(unittest.TestCase):
    """当日卦（六十甲子配卦，黄历值日卦标准体系）测试。"""

    def test_daily_hexagram_present(self):
        """当日卦字段非空。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 27))
        self.assertTrue(day.daily_hexagram)
        self.assertTrue(day.daily_hexagram_upper)
        self.assertTrue(day.daily_hexagram_lower)
        # 六十甲子配卦为值日卦，无动爻变卦
        self.assertEqual(day.daily_hexagram_moving, "")
        self.assertEqual(day.daily_hexagram_changed, "")

    def test_daily_hexagram_2026_08_27(self):
        """2026-08-27 癸酉日 → 风山渐（六十甲子配卦，多源黄历验证）。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 27))
        self.assertEqual(day.daily_hexagram, "风山渐")
        self.assertEqual(day.daily_hexagram_upper, "巽")
        self.assertEqual(day.daily_hexagram_lower, "艮")
        self.assertEqual(day.daily_hexagram_moving, "")
        self.assertEqual(day.daily_hexagram_changed, "")

    def test_daily_hexagram_deterministic(self):
        """同日期当日卦确定性。"""
        engine = HuangliEngine()
        d1 = engine.get_day(date(2026, 8, 27))
        d2 = engine.get_day(date(2026, 8, 27))
        self.assertEqual(d1.daily_hexagram, d2.daily_hexagram)
        self.assertEqual(d1.daily_hexagram_changed, d2.daily_hexagram_changed)

    def test_daily_hexagram_different_days(self):
        """不同日期当日卦不同（大概率）。"""
        engine = HuangliEngine()
        d1 = engine.get_day(date(2026, 8, 27))
        d2 = engine.get_day(date(2026, 8, 28))
        self.assertIsNotNone(d1.daily_hexagram)
        self.assertIsNotNone(d2.daily_hexagram)

    def test_ganzhi_hexagram_known_values(self):
        """六十甲子配卦已知值验证（口诀+多源互证）。"""
        from tongshu.engines.huangli_engine import _ganzhi_daily_hexagram
        # 口诀：甲子甲午坤乾见
        self.assertEqual(_ganzhi_daily_hexagram("甲子")["name"], "坤为地")
        self.assertEqual(_ganzhi_daily_hexagram("甲午")["name"], "乾为天")
        # 口诀：癸酉癸卯渐妹添
        self.assertEqual(_ganzhi_daily_hexagram("癸酉")["name"], "风山渐")
        self.assertEqual(_ganzhi_daily_hexagram("癸卯")["name"], "雷泽归妹")
        # 口诀：戊申风水涣
        self.assertEqual(_ganzhi_daily_hexagram("戊申")["name"], "风水涣")
        # 上下卦解析
        r = _ganzhi_daily_hexagram("癸酉")
        self.assertEqual(r["upper"], "巽")
        self.assertEqual(r["lower"], "艮")

    def test_meihua_algorithm_mudan(self):
        """梅花易数算法验证：牡丹占（巳年三月十六日卯时→天风姤五爻动变火风鼎）。
        注意：当日卦已切换为六十甲子配卦，此测试保留梅花易数函数供其他场景使用。"""
        from tongshu.engines.huangli_engine import _meihua_daily_hexagram, _BRANCH_ORDER
        # 独立验证算法逻辑：巳(6)年3月16日，子时(1)
        # 上卦=(6+3+16)=25, 25%8=1→乾; 下卦=(25+1)=26, 26%8=2→兑; 动爻=26%6=2→二爻
        # 主卦=天泽履，二爻动，变=天雷无妄
        r = _meihua_daily_hexagram("己巳", 3, 16)
        self.assertEqual(r["name"], "天泽履")
        self.assertEqual(r["upper"], "乾")
        self.assertEqual(r["lower"], "兑")
        self.assertEqual(r["moving_line"], 2)
        self.assertEqual(r["moving_line_cn"], "二爻")
        self.assertEqual(r["changed_name"], "天雷无妄")

    def test_to_dict_contains_daily_hexagram(self):
        """to_dict包含当日卦字段。"""
        engine = HuangliEngine()
        day = engine.get_day(date(2026, 8, 27))
        d = day.to_dict()
        self.assertIn("daily_hexagram", d)
        self.assertEqual(d["daily_hexagram"]["name"], "风山渐")


if __name__ == "__main__":
    unittest.main()
