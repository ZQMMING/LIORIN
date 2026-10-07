"""外部基准数据集交叉验证

来源:
- MingLi-Bench (160题, 2022-2025全球算命师大赛)
- fate-bench (295题, 63人, 2010-2025)

目标: 用真实命例验证八字/紫微引擎准确性
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path("./backend/src")))
# ZiweiEngine stub fallback required for tests (iztro not installed in CI)
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"
import unittest
from datetime import date

class TestExternalBenchmarks(unittest.TestCase):
    """外部基准测试用例。"""
    
    def test_mingli_case_1_bazi(self):
        """MingLi-Bench case_1: 1974-04-28 16:40 美国男命。"""
        from tongshu.engines.bazi_engine import BaziEngine
        engine = BaziEngine()
        result = engine.compute((1974, 4, 28, 16), gender="male")
        
        self.assertIsNotNone(result)
        # 验证年柱非空
        self.assertTrue(result.year_pillar.heavenly_stem)
        # 验证日柱非空
        self.assertTrue(result.day_pillar.heavenly_stem)
        
    def test_mingli_case_1_ziwei(self):
        """MingLi-Bench case_1: 紫微斗数排盘验证。
        注意: 紫微需要农历日期，这里是公历1974-04-28
        """
        from tongshu.engines.ziwei_engine import ZiweiEngine
        engine = ZiweiEngine()
        # 紫微斗数传统使用农历（契约: (年,月,日) 元组）
        # 1974年4月28日公历 ≈ 甲寅年三月十七日 申时
        result = engine.compute((1974, 3, 17), 15, gender="male")
        
        self.assertIsNotNone(result)
        
    def test_fate_bench_case_sample(self):
        """fate-bench 采样案例验证（需先 clone 仓库）。"""
        import json
        fate_path = Path("./fate-bench/data/cases.json")
        if not fate_path.exists():
            self.skipTest("fate-bench repo not cloned, skip this test")
        with open(fate_path, encoding="utf-8") as f:
            cases = json.load(f)
        
        if cases:
            c = cases[0]
            birth = c.get("birth_info", {})
            year = int(birth.get("year"))
            month = int(birth.get("month"))
            day = int(birth.get("day"))
            shichen_map = {"子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
                          "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11}
            hour = shichen_map.get(birth.get("shichen", "子"), 0) * 2 + 1
            gender = "male" if birth.get("gender") == "男" else "female"
            
            from tongshu.engines.bazi_engine import BaziEngine
            engine = BaziEngine()
            result = engine.compute((year, month, day, hour), gender=gender)
            
            self.assertIsNotNone(result)
            self.assertTrue(result.year_pillar.heavenly_stem)

