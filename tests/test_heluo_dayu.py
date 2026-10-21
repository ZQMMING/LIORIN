"""HL-09 大运计算测试"""
from __future__ import annotations
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tongshu.engines.heluo.dayu import (
    HeluoBirthInput,
    DaYunResult,
    compute_da_yun,
    get_ganzhi,
    calculate_dayun_element,
)


class TestDayunInput(unittest.TestCase):
    """测试输入数据类型。"""
    
    def test_yang_male_shun_pai(self):
        """阳男顺排。"""
        # 1984年 = 甲子年，甲=阳，男性=阳男
        inp = HeluoBirthInput(birth_year=1984, birth_month=1, birth_day=1, 
                             birth_hour=0, gender="male")
        self.assertTrue(inp.is_yang_male)
        self.assertTrue(inp.is_shun_pai)
        self.assertFalse(inp.is_yin_female)
    
    def test_yin_female_shun_pai(self):
        """阴女顺排。"""
        # 1985年 = 乙丑年，乙=阴，女性=阴女
        inp = HeluoBirthInput(birth_year=1985, birth_month=1, birth_day=1,
                             birth_hour=0, gender="female")
        self.assertTrue(inp.is_yin_female)
        self.assertTrue(inp.is_shun_pai)
        self.assertFalse(inp.is_yang_male)
    
    def test_yang_male_not_shun_pai(self):
        """阳男不满足阴女条件。"""
        inp = HeluoBirthInput(birth_year=1984, birth_month=1, birth_day=1,
                             birth_hour=0, gender="male")
        self.assertFalse(inp.is_yin_female)
    
    def test_yin_female_not_shun_pai(self):
        """阴女不满足阳男条件。"""
        inp = HeluoBirthInput(birth_year=1985, birth_month=1, birth_day=1,
                             birth_hour=0, gender="female")
        self.assertFalse(inp.is_yang_male)


class TestGanzhiCalculation(unittest.TestCase):
    """测试干支计算。"""
    
    def test_get_ganzhi_basic(self):
        """基本干支计算。"""
        result = get_ganzhi(0, 0)  # 甲子
        self.assertEqual(result, "甲子")
    
    def test_get_ganzhi_cycle(self):
        """干支循环。"""
        # 10%10=0, 12%12=0 → 甲子
        result = get_ganzhi(10, 12)
        self.assertEqual(result, "甲子")
    
    def test_year_ganzhi_1984(self):
        """1984年甲子年。"""
        inp = HeluoBirthInput(birth_year=1984, birth_month=1, birth_day=1,
                             birth_hour=0, gender="male")
        self.assertEqual(inp.year_stem_idx, 0)  # 甲
        self.assertEqual(inp.year_branch_idx, 0)  # 子


class TestDaYunComputation(unittest.TestCase):
    """测试大运计算。"""
    
    def test_compute_basic(self):
        """基本大运计算。"""
        inp = HeluoBirthInput(birth_year=1984, birth_month=1, birth_day=1,
                             birth_hour=0, gender="male")
        result = compute_da_yun(inp)
        
        self.assertTrue(result.is_shun_pai)
        self.assertEqual(len(result.da_yun_sequence), 10)
    
    def test_da_yun_sequence_count(self):
        """大运序列长度为10。"""
        inp = HeluoBirthInput(birth_year=1990, birth_month=5, birth_day=15,
                             birth_hour=12, gender="male")
        result = compute_da_yun(inp)
        self.assertEqual(len(result.da_yun_sequence), 10)
    
    def test_da_yun_age_range(self):
        """大运年龄范围正确。"""
        inp = HeluoBirthInput(birth_year=1990, birth_month=5, birth_day=15,
                             birth_hour=12, gender="male")
        result = compute_da_yun(inp)
        
        # 检查年龄范围递增
        for i, entry in enumerate(result.da_yun_sequence):
            expected_start = result.qi_yun_age + i * 10
            expected_end = expected_start + 9
            self.assertEqual(entry.age_start, expected_start)
            self.assertEqual(entry.age_end, expected_end)
    
    def test_da_yun_stem_branch_format(self):
        """大运干支格式正确。"""
        inp = HeluoBirthInput(birth_year=1990, birth_month=5, birth_day=15,
                             birth_hour=12, gender="male")
        result = compute_da_yun(inp)
        
        for entry in result.da_yun_sequence:
            self.assertEqual(len(entry.stem_branch), 2)
            self.assertIn(entry.stem_branch[0], "甲乙丙丁戊己庚辛壬癸")
            self.assertIn(entry.stem_branch[1], "子丑寅卯辰巳午未申酉戌亥")


class TestDayunElement(unittest.TestCase):
    """测试大运五行计算。"""
    
    def test_element_jia(self):
        """甲木五行。"""
        result = calculate_dayun_element(0, 0)  # 甲子
        self.assertEqual(result, "木")
    
    def test_element_bing(self):
        """丙火五行。"""
        result = calculate_dayun_element(2, 6)  # 丙午
        self.assertEqual(result, "火")


if __name__ == "__main__":
    unittest.main()
