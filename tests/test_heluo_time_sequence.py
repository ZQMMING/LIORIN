"""HL-10/11/12 流年/流月/流日计算测试"""
from __future__ import annotations
import unittest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tongshu.engines.heluo.time_sequence import (
    LiuNianInput, LiuNianResult, compute_liu_nian,
    LiuYueInput, LiuYueResult, compute_liu_yue,
    LiuRiInput, LiuRiResult, compute_liu_ri,
)


class TestLiuNian(unittest.TestCase):
    """测试流年计算。"""
    
    def test_2024_liu_nian(self):
        """2024年甲辰年。"""
        inp = LiuNianInput(birth_year=1990, target_year=2024, gender="male")
        result = compute_liu_nian(inp)
        self.assertEqual(result.liu_nian_ganzhi, "甲辰")
    
    def test_2025_liu_nian(self):
        """2025年乙巳年。"""
        inp = LiuNianInput(birth_year=1990, target_year=2025, gender="male")
        result = compute_liu_nian(inp)
        self.assertEqual(result.liu_nian_ganzhi, "乙巳")
    
    def test_jiazi_year(self):
        """甲子年验证。"""
        inp = LiuNianInput(birth_year=1984, target_year=1984, gender="male")
        result = compute_liu_nian(inp)
        self.assertEqual(result.liu_nian_ganzhi, "甲子")


class TestLiuYue(unittest.TestCase):
    """测试流月计算。"""
    
    def test_basic_computation(self):
        """基本流月计算。"""
        inp = LiuYueInput(birth_year=1990, birth_month=5, 
                         target_year=2025, target_month=8, gender="male")
        result = compute_liu_yue(inp)
        self.assertIsInstance(result.liu_yue_ganzhi, str)
        self.assertEqual(len(result.liu_yue_ganzhi), 2)


class TestLiuRi(unittest.TestCase):
    """测试流日计算。"""
    
    def test_jiazi_day(self):
        """甲子日验证（公元4年1月1日）。"""
        inp = LiuRiInput(birth_year=1990, birth_month=5, birth_day=15,
                        target_date=datetime(4, 1, 1), gender="male")
        result = compute_liu_ri(inp)
        self.assertEqual(result.liu_ri_ganzhi, "甲子")
    
    def test_2025_8_21(self):
        """2025年8月21日流日计算。"""
        inp = LiuRiInput(birth_year=1990, birth_month=5, birth_day=15,
                        target_date=datetime(2025, 8, 21), gender="male")
        result = compute_liu_ri(inp)
        self.assertIsInstance(result.liu_ri_ganzhi, str)
        self.assertEqual(len(result.liu_ri_ganzhi), 2)
    
    def test_ganzhi_format(self):
        """干支格式验证。"""
        inp = LiuRiInput(birth_year=1990, birth_month=5, birth_day=15,
                        target_date=datetime(2025, 8, 21), gender="male")
        result = compute_liu_ri(inp)
        stem = result.liu_ri_ganzhi[0]
        branch = result.liu_ri_ganzhi[1]
        self.assertIn(stem, "甲乙丙丁戊己庚辛壬癸")
        self.assertIn(branch, "子丑寅卯辰巳午未申酉戌亥")


if __name__ == "__main__":
    unittest.main()
