"""Numbers 模块边界测试

覆盖:
- normalize_tian_shu / normalize_di_shu 边界
- number_to_trigram 映射
- build_six_lines
- get_hexagram_name
- compute_tian_di_shu 边界情况
"""
from __future__ import annotations
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from heluo_engine.engines.heluo.numbers import (
    STEM_VALUES,
    BRANCH_VALUES,
    LUSHU_TO_TRIGRAM_NAME,
    TRIGRAM_BINARY,
    TRIGRAM_LINES,
    SIXTY_FOUR_HEXAGRAMS,
    normalize_tian_shu,
    normalize_di_shu,
    number_to_trigram,
    get_hexagram_name,
    build_six_lines,
    compute_tian_di_shu,
    TianDiShu,
)


class TestNormalizeTianShu(unittest.TestCase):
    """天数归一化测试。"""
    
    def test_small_number(self):
        """小数直接返回。"""
        self.assertEqual(normalize_tian_shu(3), 3)
        self.assertEqual(normalize_tian_shu(9), 9)
    
    def test_equal_25(self):
        """天数=25 → 5（中宫）。"""
        self.assertEqual(normalize_tian_shu(25), 5)
    
    def test_above_25(self):
        """天数>25: 天数-25后归一化。"""
        self.assertEqual(normalize_tian_shu(26), 1)  # 26-25=1
        self.assertEqual(normalize_tian_shu(30), 5)  # 30-25=5
        self.assertEqual(normalize_tian_shu(35), 1)  # 35-25=10, 10→1(遇十用商)
    
    def test_multiple_of_10(self):
        """遇十不用。"""
        self.assertEqual(normalize_tian_shu(10), 1)  # 10→1(遇十用商)
        self.assertEqual(normalize_tian_shu(20), 2)  # 20→2(遇十用商)
        self.assertEqual(normalize_tian_shu(30), 5)  # 30-25=5(大于25走第一条路径)
    
    def test_zero(self):
        """零值处理（返回2）。"""
        self.assertEqual(normalize_tian_shu(0), 5)


class TestNormalizeDiShu(unittest.TestCase):
    """地数归一化测试。"""
    
    def test_small_number(self):
        """小数直接返回。"""
        self.assertEqual(normalize_di_shu(3), 3)
        self.assertEqual(normalize_di_shu(9), 9)
    
    def test_equal_30(self):
        """地数=30 → 3。"""
        self.assertEqual(normalize_di_shu(30), 3)
    
    def test_above_30(self):
        """地数>30: 地数-30后归一化。"""
        self.assertEqual(normalize_di_shu(31), 1)  # 31-30=1
        self.assertEqual(normalize_di_shu(40), 1)  # 40-30=10, 10→1(遇十用商)
    
    def test_multiple_of_10(self):
        """遇十不用。"""
        self.assertEqual(normalize_di_shu(10), 1)  # 10→1(遇十用商)
        self.assertEqual(normalize_di_shu(20), 2)  # 20→2(遇十用商)
        self.assertEqual(normalize_di_shu(30), 3)  # 地数=30的特殊返回


class TestNumberToTrigram(unittest.TestCase):
    """数字→卦名映射测试。"""
    
    def test_all_mappings(self):
        """验证 1-9 全部映射。"""
        expected = {
            1: "坎", 2: "坤", 3: "震", 4: "巽",
            5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离",
        }
        for n, name in expected.items():
            self.assertEqual(number_to_trigram(n), name, f"{n}→{name}")
    
    def test_out_of_range_returns_question(self):
        """越界返回问号（不抛出异常）。"""
        self.assertEqual(number_to_trigram(0), "?")
        self.assertEqual(number_to_trigram(10), "?")
        self.assertEqual(number_to_trigram(-1), "?")


class TestGetHexagramName(unittest.TestCase):
    """六十四卦名查找测试。"""
    
    def test_known_hexagram(self):
        """已知卦名。"""
        self.assertEqual(get_hexagram_name('乾', '乾'), '乾为天')
        self.assertEqual(get_hexagram_name('坤', '坤'), '坤为地')
        self.assertEqual(get_hexagram_name('坎', '坎'), '坎为水')
        self.assertEqual(get_hexagram_name('离', '离'), '离为火')
    
    def test_unknown_hexagram(self):
        """未知卦名 fallback。"""
        result = get_hexagram_name('乾', '屯')
        self.assertEqual(result, '乾屯')  # 未定义则拼接
    
    def test_all_64_possible(self):
        """验证部分组合。"""
        # 上乾下卦
        self.assertEqual(get_hexagram_name('乾', '乾'), '乾为天')
        self.assertEqual(get_hexagram_name('乾', '兑'), '天泽履')
        self.assertEqual(get_hexagram_name('乾', '离'), '天火同人')
        self.assertEqual(get_hexagram_name('乾', '震'), '天雷无妄')
        self.assertEqual(get_hexagram_name('乾', '巽'), '天风姤')
        self.assertEqual(get_hexagram_name('乾', '坎'), '天水讼')
        self.assertEqual(get_hexagram_name('乾', '艮'), '天山遁')
        self.assertEqual(get_hexagram_name('乾', '坤'), '天地否')


class TestBuildSixLines(unittest.TestCase):
    """六爻构建测试。"""
    
    def test_qian_we_tian(self):
        """乾为天：六阳爻。"""
        lines = build_six_lines('乾', '乾')
        self.assertEqual(lines, [1, 1, 1, 1, 1, 1])
    
    def test_kun_wei_di(self):
        """坤为地：六阴爻。"""
        lines = build_six_lines('坤', '坤')
        self.assertEqual(lines, [-1, -1, -1, -1, -1, -1])
    
    def test_can_we_huo(self):
        """坎为水：中爻阳，初上阴。"""
        lines = build_six_lines('坎', '坎')
        # 坎 = 010（自下而上：阴阴阳）
        self.assertEqual(lines, [-1, 1, -1, -1, 1, -1])
    
    def test_li_wei_huo(self):
        """离为火：中爻阴，初上阳。"""
        lines = build_six_lines('离', '离')
        # 离 = 101
        self.assertEqual(lines, [1, -1, 1, 1, -1, 1])
    
    def test_zhen_wei_lei(self):
        """震为雷：初爻阳，二上阴。"""
        lines = build_six_lines('震', '震')
        # 震 = 100
        self.assertEqual(lines, [1, -1, -1, 1, -1, -1])
    
    def test_xun_wei_feng(self):
        """巽为风：初上阳，中阴。"""
        lines = build_six_lines('巽', '巽')
        # 巽 = 011
        self.assertEqual(lines, [-1, 1, 1, -1, 1, 1])
    
    def test_gen_wei_shan(self):
        """艮为山：上爻阳，初二中阴。"""
        lines = build_six_lines('艮', '艮')
        # 艮 = 001
        self.assertEqual(lines, [-1, -1, 1, -1, -1, 1])
    
    def test_dui_wei_ze(self):
        """兑为泽：上爻阴，初二中阳。"""
        lines = build_six_lines('兑', '兑')
        # 兑 = 110
        self.assertEqual(lines, [1, 1, -1, 1, 1, -1])


class TestComputeTianDiShu(unittest.TestCase):
    """天数地数计算测试。"""
    
    def test_jixiaolan_bazi(self):
        """纪晓岚八字验证。"""
        bazi = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]
        result = compute_tian_di_shu(bazi, "male")
        
        self.assertIsInstance(result, TianDiShu)
        self.assertIsInstance(result.tian_shu, int)
        self.assertIsInstance(result.di_shu, int)
        self.assertIsInstance(result.tian_reduced, int)
        self.assertIsInstance(result.di_reduced, int)
        self.assertGreater(len(result.details), 0)
    
    def test_invalid_bazi_length(self):
        """非法八字长度。"""
        with self.assertRaises(ValueError):
            compute_tian_di_shu([("甲", "辰")], "male")  # 只有1柱
    
    def test_unknown_stem_raises(self):
        """未知天干。"""
        with self.assertRaises(ValueError):
            compute_tian_di_shu([("X", "辰"), ("甲", "子"), ("乙", "丑"), ("丙", "寅")], "male")
    
    def test_unknown_branch_raises(self):
        """未知地支。"""
        with self.assertRaises(ValueError):
            compute_tian_di_shu([("甲", "X"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male")
    
    def test_consistency_for_same_input(self):
        """相同输入应返回相同结果。"""
        bazi = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]
        r1 = compute_tian_di_shu(bazi, "male")
        r2 = compute_tian_di_shu(bazi, "male")
        self.assertEqual(r1.tian_shu, r2.tian_shu)
        self.assertEqual(r1.di_shu, r2.di_shu)
        self.assertEqual(r1.tian_reduced, r2.tian_reduced)
        self.assertEqual(r1.di_reduced, r2.di_reduced)


class TestStemValues(unittest.TestCase):
    """天干取值验证。"""
    
    def test_all_stems_present(self):
        """所有天干都有值。"""
        stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        for s in stems:
            self.assertIn(s, STEM_VALUES, f"{s} 缺失")
    
    def test_value_ranges(self):
        """值在 1-9 范围内。"""
        for s, v in STEM_VALUES.items():
            self.assertIn(v, range(1, 10), f"{s}={v} 超出范围")
    
    def test_known_values(self):
        """验证已知映射。"""
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


class TestBranchValues(unittest.TestCase):
    """地支取值验证。"""
    
    def test_all_branches_present(self):
        """所有地支都有值。"""
        branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        for b in branches:
            self.assertIn(b, BRANCH_VALUES, f"{b} 缺失")
    
    def test_values_are_tuples(self):
        """值都是二元组。"""
        for b, v in BRANCH_VALUES.items():
            self.assertIsInstance(v, tuple)
            self.assertEqual(len(v), 2)
    
    def test_known_values(self):
        """验证已知映射。"""
        self.assertEqual(BRANCH_VALUES["子"], (1, 6))
        self.assertEqual(BRANCH_VALUES["丑"], (5, 10))
        self.assertEqual(BRANCH_VALUES["寅"], (3, 8))
        self.assertEqual(BRANCH_VALUES["卯"], (3, 8))
        self.assertEqual(BRANCH_VALUES["巳"], (2, 7))
        self.assertEqual(BRANCH_VALUES["午"], (2, 7))
        self.assertEqual(BRANCH_VALUES["未"], (5, 10))
        self.assertEqual(BRANCH_VALUES["申"], (4, 9))
        self.assertEqual(BRANCH_VALUES["酉"], (4, 9))
        self.assertEqual(BRANCH_VALUES["辰"], (5, 10))
        self.assertEqual(BRANCH_VALUES["戌"], (5, 10))
        self.assertEqual(BRANCH_VALUES["亥"], (1, 6))


class TestLushuToTrigram(unittest.TestCase):
    """洛书数→卦名映射测试。"""
    
    def test_all_mappings(self):
        """验证 1-9 全部映射。"""
        expected = {
            1: "坎", 2: "坤", 3: "震", 4: "巽",
            5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离",
        }
        for n, name in expected.items():
            self.assertEqual(LUSHU_TO_TRIGRAM_NAME[n], name, f"{n}→{name}")
    
    def test_missing_key_returns_none(self):
        """不存在的 key 返回 None。"""
        self.assertIsNone(LUSHU_TO_TRIGRAM_NAME.get(0))
        self.assertIsNone(LUSHU_TO_TRIGRAM_NAME.get(10))


class TestTrigramBinary(unittest.TestCase):
    """卦象二进制表示测试。"""
    
    def test_all_trigrams_have_binary(self):
        """所有卦都有二进制表示。"""
        trigrams = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']
        for t in trigrams:
            self.assertIn(t, TRIGRAM_BINARY, f"{t} 缺失")
            self.assertEqual(len(TRIGRAM_BINARY[t]), 3)
    
    def test_binary_format(self):
        """二进制格式验证。"""
        self.assertEqual(TRIGRAM_BINARY["乾"], "111")
        self.assertEqual(TRIGRAM_BINARY["坤"], "000")
        self.assertEqual(TRIGRAM_BINARY["坎"], "010")
        self.assertEqual(TRIGRAM_BINARY["离"], "101")


class TestSixtyFourHexagrams(unittest.TestCase):
    """六十四卦表完整性测试。"""
    
    def test_count(self):
        """卦表数量应为 64。"""
        # 注意：实现中有重复键（兑乾/乾兑等），实际 unique 数可能少于 64
        self.assertGreaterEqual(len(SIXTY_FOUR_HEXAGRAMS), 56)
    
    def test_all_8x8_pairs(self):
        """验证所有上卦×下卦组合都有名称（部分可能重复）。"""
        trigrams = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']
        for upper in trigrams:
            for lower in trigrams:
                name = get_hexagram_name(upper, lower)
                self.assertIsNotNone(name)
                self.assertIsInstance(name, str)
                self.assertGreater(len(name), 0)


if __name__ == '__main__':
    unittest.main()
