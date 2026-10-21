"""河洛 canonical 计算器单元测试。

验证 Phase 2 重构后的新 API：HeluoCanonical。
"""

from __future__ import annotations

import unittest

from tongshu.engines.heluo import (
    HeluoCanonical,
    HeluoResult,
)
from tongshu.engines.heluo.exceptions import ForbiddenRuleError


class TestHeluoCanonical(unittest.TestCase):
    """测试 HeluoCanonical 核心功能。"""

    def test_golden_case_jixiaolan(self):
        """纪晓岚 Golden Case 验证。"""
        c = HeluoCanonical()
        passed = c.verify_golden_case("jixiaolan")
        self.assertTrue(passed, "纪晓岚 Golden Case 未通过")

    def test_run_all_golden_cases(self):
        """运行所有 Golden Case。"""
        c = HeluoCanonical()
        results = c.run_all_golden_cases()
        for case_name, passed in results.items():
            self.assertTrue(passed, f"Golden Case {case_name} 未通过")

    def test_calculate_basic(self):
        """基本计算测试。"""
        c = HeluoCanonical()
        result = c.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="zhong",
        )
        self.assertIsInstance(result, HeluoResult)
        self.assertEqual(result.prenatal.hexagram_name, "地天泰")
        self.assertEqual(result.yuantang.yuantang, "六四")
        self.assertEqual(result.postnatal.hexagram_name, "天雷无妄")

    def test_invalid_gender_raises(self):
        """无效性别应抛出异常。"""
        c = HeluoCanonical()
        with self.assertRaises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender="unknown",
                birth_hour="午",
            )


class TestNumbersModule(unittest.TestCase):
    """测试 numbers 模块基础功能。"""

    def test_stem_values(self):
        """天干取值正确性。"""
        from tongshu.engines.heluo.numbers import STEM_VALUES
        self.assertEqual(STEM_VALUES["甲"], 6)
        self.assertEqual(STEM_VALUES["乙"], 2)
        self.assertEqual(STEM_VALUES["丙"], 8)
        self.assertEqual(STEM_VALUES["丁"], 7)
        self.assertEqual(STEM_VALUES["戊"], 1)
        self.assertEqual(STEM_VALUES["己"], 9)
        self.assertEqual(STEM_VALUES["庚"], 3)
        self.assertEqual(STEM_VALUES["辛"], 4)
        self.assertEqual(STEM_VALUES["壬"], 6)
        self.assertEqual(STEM_VALUES["癸"], 2)

    def test_branch_values(self):
        """地支取值正确性。"""
        from tongshu.engines.heluo.numbers import BRANCH_VALUES
        self.assertEqual(BRANCH_VALUES["子"], (1, 6))
        self.assertEqual(BRANCH_VALUES["丑"], (5, 10))
        self.assertEqual(BRANCH_VALUES["寅"], (3, 8))
        self.assertEqual(BRANCH_VALUES["卯"], (3, 8))
        self.assertEqual(BRANCH_VALUES["巳"], (2, 7))
        self.assertEqual(BRANCH_VALUES["午"], (2, 7))
        self.assertEqual(BRANCH_VALUES["申"], (4, 9))
        self.assertEqual(BRANCH_VALUES["酉"], (4, 9))
        self.assertEqual(BRANCH_VALUES["辰"], (5, 10))
        self.assertEqual(BRANCH_VALUES["戌"], (5, 10))
        self.assertEqual(BRANCH_VALUES["亥"], (1, 6))


class TestPrenatalModule(unittest.TestCase):
    """测试 prenatal 模块核心功能。"""

    def test_prenatal_hexagram_shangyuan_male(self):
        """上元男命测试。"""
        from tongshu.engines.heluo.prenatal import determine_prenatal_hexagram
        result = determine_prenatal_hexagram(
            tian_reduced=2,  # 坤
            di_reduced=6,    # 乾
            gender="male",
            birth_year_yang=True,  # 甲辰年
            era="shang",
        )
        self.assertEqual(result.hexagram_name, "地天泰")

    def test_prenatal_hexagram_xiayuan_female(self):
        """下元女命测试。"""
        from tongshu.engines.heluo.prenatal import determine_prenatal_hexagram
        result = determine_prenatal_hexagram(
            tian_reduced=2,
            di_reduced=6,
            gender="female",
            birth_year_yang=False,  # 乙年
            era="xia",
        )
        # 阴年女命：天数在上，地数在下
        self.assertEqual(result.hexagram_name, "地天泰")


class TestYuanTangModule(unittest.TestCase):
    """测试 yuan_tang 模块。"""

    def test_find_yuantang_mixed(self):
        """杂卦元堂定位。"""
        from tongshu.engines.heluo.yuan_tang import find_yuantang
        # 地天泰：六爻为 [-1, -1, -1, 1, 1, 1]（自下而上）
        lines = [-1, -1, -1, 1, 1, 1]
        result = find_yuantang(
            six_lines=lines,
            birth_hour="午",
            gender="male",
            xiantian_name="地天泰",
        )
        self.assertIsNotNone(result)
        self.assertIn(result.yao_nature, ["阳", "阴"])


class TestPostnatalModule(unittest.TestCase):
    """测试 postnatal 模块。"""

    def test_compute_postnatal_jixiaolan(self):
        """纪晓岚后天卦验证。"""
        from tongshu.engines.heluo.postnatal import compute_postnatal
        # 地天泰六爻（自下而上，与原典一致）
        lines = [1, 1, 1, -1, -1, -1]  # 下乾上坤 = 地天泰
        result = compute_postnatal(
            six_lines=lines,
            yuantang_index=3,  # 六四
        )
        self.assertEqual(result.hexagram_name, "天雷无妄")


class TestHexagramModule(unittest.TestCase):
    """测试 hexagram 模块。"""

    def test_analyze_hexagram(self):
        """卦象结构分析。"""
        from tongshu.engines.heluo.hexagram import analyze_hexagram
        result = analyze_hexagram("地天泰")
        self.assertIsNotNone(result)
        self.assertEqual(result.upper, "坤")
        self.assertEqual(result.lower, "乾")


class TestInputModule(unittest.TestCase):
    """测试 input 模块。"""

    def test_prepare_heluo_input(self):
        """输入数据验证。"""
        from tongshu.engines.heluo.input import HeluoInput, Location
        input_data = HeluoInput(
            birth_date="2024-01-01",
            birth_time="12:00",
            gender="male",
            location=Location(latitude=39.9, longitude=116.4),
            timezone="Asia/Shanghai",
            true_solar_datetime="2024-01-01T12:00:00",
        )
        self.assertEqual(input_data.gender, "male")
        self.assertEqual(input_data.day_boundary, "23:00")

    def test_invalid_gender_raises(self):
        """无效性别应抛出异常。"""
        from tongshu.engines.heluo.input import HeluoInput, Location
        with self.assertRaises(ValueError):
            HeluoInput(
                birth_date="2024-01-01",
                birth_time="12:00",
                gender="unknown",
                location=Location(latitude=39.9, longitude=116.4),
                timezone="Asia/Shanghai",
                true_solar_datetime="2024-01-01T12:00:00",
            )


if __name__ == "__main__":
    unittest.main()
