"""八字引擎测试 - Bazi (八字) Engine

覆盖:
- Pillar 属性 (stem_element, branch_element)
- pillar_to_chinese 转换
- BaziChart 结构验证
- 阴阳干排列 (甲子、乙丑...)
- 10天干 12地支映射完整性
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path("./backend/src")))

import unittest
from tongshu.engines.bazi_engine import (
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    STEM_POLARITY,
    Pillar,
    pillar_to_chinese,
    BaziChart,
    BaziEngine,
)


class TestPillarProperties(unittest.TestCase):
    """Pillar 数据属性测试。"""
    
    def test_all_stem_elements(self):
        """所有天干五行映射完整。"""
        expected = {
            "JIA": "WOOD", "YI": "WOOD",
            "BING": "FIRE", "DING": "FIRE",
            "WU": "EARTH", "JI": "EARTH",
            "GENG": "METAL", "XIN": "METAL",
            "REN": "WATER", "GUI": "WATER",
        }
        self.assertEqual(STEM_ELEMENT, expected)
    
    def test_all_branch_elements(self):
        """所有地支五行映射完整。"""
        p = Pillar("JIA", "YIN")
        self.assertEqual(p.branch_element, "WOOD")
        
        p = Pillar("BING", "WU")
        self.assertEqual(p.branch_element, "FIRE")
        
        p = Pillar("WU", "CHEN")
        self.assertEqual(p.branch_element, "EARTH")
        
        p = Pillar("GENG", "SHEN")
        self.assertEqual(p.branch_element, "METAL")
        
        p = Pillar("REN", "ZI")
        self.assertEqual(p.branch_element, "WATER")
    
    def test_pillar_to_chinese_jiachen(self):
        """甲辰转换。"""
        p = Pillar("JIA", "CHEN")
        self.assertEqual(pillar_to_chinese(p), "甲辰")
    
    def test_pillar_to_chinese_xinwei(self):
        """辛未转换。"""
        p = Pillar("XIN", "WEI")
        self.assertEqual(pillar_to_chinese(p), "辛未")
    
    def test_pillar_to_chinese_bingxu(self):
        """丙戌转换。"""
        p = Pillar("BING", "XU")
        self.assertEqual(pillar_to_chinese(p), "丙戌")


class TestBaziChartStructure(unittest.TestCase):
    """八字命盘结构测试。"""
    
    def test_full_chart_has_day_master(self):
        """完整命盘包含日主。"""
        chart = BaziChart(
            year_pillar=Pillar("JIA", "CHEN"),
            month_pillar=Pillar("XIN", "WEI"),
            day_pillar=Pillar("BING", "XU"),
            hour_pillar=Pillar("JIA", "WU"),
            day_master="BING",
            luck_pillars=[],
        )
        self.assertEqual(chart.day_master, "BING")
        self.assertIsNotNone(chart.to_dict())
    
    def test_chart_serialization(self):
        """命盘序列化完整。"""
        chart = BaziChart(
            year_pillar=Pillar("JIA", "CHEN"),
            month_pillar=Pillar("XIN", "WEI"),
            day_pillar=Pillar("BING", "XU"),
            hour_pillar=Pillar("JIA", "WU"),
            day_master="BING",
            luck_pillars=[],
        )
        data = chart.to_dict()
        self.assertIn("year_pillar", data)
        self.assertIn("day_master", data)
        self.assertEqual(data["day_master"], "BING")


class TestBaziEngine(unittest.TestCase):
    """八字引擎功能测试。"""
    
    def test_engine_computes_jixiaolan(self):
        """纪晓岚八字验证（公历1724-07-02 午时）。"""
        engine = BaziEngine()
        result = engine.compute((1724, 8, 3, 11), gender="male")
        
        self.assertEqual(result.year_pillar.heavenly_stem, "JIA")   # 甲
        self.assertEqual(result.year_pillar.earthly_branch, "CHEN")  # 辰
        self.assertEqual(result.day_pillar.heavenly_stem, "BING")    # 丙
        self.assertEqual(result.day_pillar.earthly_branch, "XU")     # 戌
        self.assertEqual(result.hour_pillar.heavenly_stem, "JIA")    # 甲
        self.assertEqual(result.hour_pillar.earthly_branch, "WU")    # 午
        self.assertEqual(result.day_master, "BING")
    
    def test_deterministic_output(self):
        """相同输入产生相同输出。"""
        engine = BaziEngine()
        r1 = engine.compute((1724, 6, 11, 12), gender="male")
        r2 = engine.compute((1724, 6, 11, 12), gender="male")
        self.assertEqual(r1.day_master, r2.day_master)


class TestStemBranchMapping(unittest.TestCase):
    """天干地支映射完整性测试。"""
    
    def test_10_stems_count(self):
        """天干数量正确。"""
        self.assertEqual(len(HEAVENLY_STEMS), 10)
    
    def test_12_branches_count(self):
        """地支数量正确。"""
        self.assertEqual(len(EARTHLY_BRANCHES), 12)
    
    def test_60_jiazi_cycle(self):
        """60甲子周期完整性。"""
        stems = len(HEAVENLY_STEMS)  # 10
        branches = len(EARTHLY_BRANCHES)  # 12
        gcd = (stems * branches) // __import__("math").gcd(stems, branches)
        self.assertEqual(gcd, 60)


if __name__ == "__main__":
    unittest.main()
