"""河洛流年卦推演回归测试（《河洛真数》古籍 + 权威案例二验证）。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest

from tongshu.engines.heluo.timeline_yun import compute_liunian, compute_liuyue
from tongshu.engines.heluo.canonical import HeluoCanonical


class TestLiuNianGuji(unittest.TestCase):
    """古籍《河洛真数》小象行年卦气示例验证。"""

    def test_guji_tongren_jiu3_yang_year(self):
        """古籍同人九三（元堂阳爻）阳年 1-9 岁。"""
        # 同人=[初九,六二,九三,九四,九五,上九]=[1,-1,1,1,1,1]
        r = compute_liunian([1, -1, 1, 1, 1, 1], 2, [1, 1, 1, 1, 1, 1], 3, 1984, 1, 9)
        names = [y.hexagram_name for y in r.years]
        self.assertEqual(names, [
            '天火同人', '泽火革', '泽雷随', '水雷屯', '地雷复',
            '山雷颐', '山地剥', '山水蒙', '山风蛊',
        ])

    def test_guji_tongren_liu2_yin_year(self):
        """古籍同人六二（元堂阴爻）1-6 岁，自本爻起逐爻。"""
        r = compute_liunian([1, -1, 1, 1, 1, 1], 1, [1, 1, 1, 1, 1, 1], 3, 1984, 1, 6)
        names = [y.hexagram_name for y in r.years]
        self.assertEqual(names, [
            '乾为天', '天泽履', '风泽中孚', '山泽损', '地泽临', '地水师',
        ])


class TestLiuYueGuji(unittest.TestCase):
    """古籍《河洛真数》论月卦从世上起例 观卦上九元堂示例。"""

    def test_guji_guan_liuyue(self):
        """观卦元堂上九：阳月逐爻累积、阴月取月爻应爻。"""
        # 观=风地观=[初六,六二,六三,六四,九五,上九]，元堂上九(yt=5)
        r = compute_liuyue([-1, -1, -1, -1, 1, 1], 5)
        yang = [m['name'] for m in r.months if m['kind'] == '阳月']
        yin = [m['name'] for m in r.months if m['kind'] == '阴月']
        self.assertEqual(yang, ['风雷益', '风泽中孚', '风天小畜', '乾为天', '火天大有', '雷天大壮'])
        self.assertEqual(yin, ['天雷无妄', '山泽损', '水天需', '天风姤', '离为火', '雷泽归妹'])


class TestLiuNianCase2(unittest.TestCase):
    """权威案例二（SO玄奥，先天艮为山元堂九三，2013 癸巳）1-12 岁。"""

    def test_case2_full_12_years(self):
        c = HeluoCanonical()
        r = c.calculate([('癸', '巳'), ('壬', '戌'), ('己', '巳'), ('甲', '戌')],
                        'male', '戌', 'zhong', 2013)
        names = [y['hexagram'] for y in r.timeline.yearly_hexagrams[:12]]
        self.assertEqual(names, [
            '山地剥', '坤为地', '地山谦', '雷山小过', '泽山咸', '天山遁',
            '天火同人', '乾为天', '天泽履', '火山旅', '天山遁', '泽山咸',
        ])


if __name__ == '__main__':
    unittest.main()
