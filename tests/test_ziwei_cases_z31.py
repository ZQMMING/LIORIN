# -*- coding: utf-8 -*-
"""Z31: 15 案例输入层验证（八字日柱 + 紫微排盘自洽）"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.bazi_engine import BaziEngine

# (公历y,m,d, 农历y,m,d(闰月负), hour, gender, 正确日柱)
CASES = [
    (1912, 11, 12, 1912, 10, 4, 12, "male", "壬辰"),
    (2027, 3, 22, 2027, 2, 15, 2, "female", "庚子"),
    (2028, 8, 3, 2028, 6, 13, 10, "male", "庚申"),
    (1974, 12, 24, 1974, 11, 11, 8, "female", "己亥"),
    (1948, 2, 4, 1947, 12, 25, 18, "male", "己未"),
    (2010, 2, 18, 2010, 1, 5, 4, "male", "己亥"),
    (1968, 7, 22, 1968, 6, 27, 14, "male", "癸巳"),
    (1965, 9, 4, 1965, 8, 9, 14, "male", "辛酉"),
    (1913, 3, 18, 1913, 2, 11, 22, "male", "戊戌"),
    (1968, 10, 21, 1968, 8, 30, 4, "female", "甲子"),
    (1950, 9, 20, 1950, 8, 9, 10, "female", "戊午"),
    (1947, 4, 20, 1947, -2, 29, 4, "female", "己巳"),
    (1964, 6, 24, 1964, 5, 15, 8, "female", "甲辰"),
    (1985, 5, 22, 1985, 4, 3, 22, "female", "辛酉"),
    (2015, 9, 21, 2015, 8, 9, 2, "female", "庚子"),
]


class TestBaziDayPillarCases:
    """八字日柱（公历输入）15/15 与案例正确四柱一致"""

    def test_all_day_pillars(self):
        bz = BaziEngine()
        for sy, sm, sd, ly, lm, ld, h, g, exp in CASES:
            r = bz.compute((sy, sm, sd, h), g)
            day = r.get_pillars_chinese().get("day", "?")
            assert day == exp, f"案例({sy}-{sm}-{sd} {h}时 {g}) 日柱 {day} != 期望 {exp}"


class TestZiweiPalaceCases:
    """紫微排盘（农历输入）15/15 成功且命身宫齐全"""

    def test_all_charts_build(self):
        eng = ZiweiEngine()
        for sy, sm, sd, ly, lm, ld, h, g, exp in CASES:
            chart = eng.full_chart((ly, lm, ld), h, g)
            assert chart.fiveElementsClass, f"案例{ly}-{lm}-{ld} 五行局为空"
            assert chart.soul_earthly_branch, f"案例{ly}-{lm}-{ld} 命宫为空"
            assert chart.body_earthly_branch, f"案例{ly}-{lm}-{ld} 身宫为空"

    def test_leap_month_case(self):
        """1947闰二月廿九：闰月输入（month=-2）可排盘"""
        eng = ZiweiEngine()
        chart = eng.full_chart((1947, -2, 29), 4, "female")
        assert chart.fiveElementsClass == "金四局"
        assert chart.soul_earthly_branch == "寅"
