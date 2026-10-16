# -*- coding: utf-8 -*-
"""紫微排盘交叉验证测试 - 独立排盘公式 vs iztro

验证维度: 命宫地支/身宫地支/命宫天干/五行局(纳音)
公式来源: 《紫微斗数全书》排盘规则
"""
from __future__ import annotations
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("./backend/src")))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine

BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
STEMS = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
WUHU = {'甲':2,'己':2,'乙':4,'庚':4,'丙':6,'辛':6,'丁':8,'壬':8,'戊':0,'癸':0}
NAYIN = {
    '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火',
    '戊辰':'大林木','己巳':'大林木','庚午':'路旁土','辛未':'路旁土',
    '壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
    '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土',
    '庚辰':'白蜡金','辛巳':'白蜡金','壬午':'杨柳木','癸未':'杨柳木',
    '甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
    '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木',
    '壬辰':'长流水','癸巳':'长流水','甲午':'沙中金','乙未':'沙中金',
    '丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
    '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金',
    '甲辰':'覆灯火','乙巳':'覆灯火','丙午':'天河水','丁未':'天河水',
    '戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
    '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水',
    '丙辰':'沙中土','丁巳':'沙中土','戊午':'天上火','己未':'天上火',
    '庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
}
NAYIN_TO_JU = {'金':'金四局','木':'木三局','水':'水二局','火':'火六局','土':'土五局'}
SHICHEN_TO_HOUR = [0,2,4,6,8,10,12,14,16,18,20,22]


def calc_soul_branch(month, shichen):
    return BRANCHES[(2 + month - 1 - shichen) % 12]

def calc_body_branch(month, shichen):
    return BRANCHES[(2 + month - 1 + shichen) % 12]

def calc_soul_stem(year_stem, soul_branch):
    yin_stem = WUHU[year_stem]
    offset = (BRANCHES.index(soul_branch) - 2) % 12
    return STEMS[(yin_stem + offset) % 10]

def calc_five_ju(stem, branch):
    nayin = NAYIN.get(stem + branch, '')
    return NAYIN_TO_JU.get(nayin[-1], '未知') if nayin else '未知'


CASES = [
    ((1960,5,5), 2, 'male', '庚', '庚子年五月寅时'),
    ((1974,3,17), 8, 'male', '甲', '甲寅年三月申时'),
    ((1984,10,15), 8, 'female', '甲', '甲子年闰十月申时'),
    ((2000,1,1), 0, 'male', '庚', '庚辰年正月子时'),
    ((1990,5,15), 6, 'female', '庚', '庚午年五月午时'),
    ((1985,8,20), 4, 'male', '乙', '乙丑年八月辰时'),
    ((1976,12,8), 10, 'female', '丙', '丙辰年十二月戌时'),
    ((1995,6,6), 0, 'male', '乙', '乙亥年六月子时'),
]


class TestZiweiChartCrossValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_soul_branch(self):
        """命宫地支: 寅起正月顺数到生月, 该宫起子时逆数到生时"""
        for lunar, shichen, gender, ystem, desc in CASES:
            with self.subTest(desc=desc):
                manual = calc_soul_branch(lunar[1], shichen)
                full = self.engine.full_chart(lunar, SHICHEN_TO_HOUR[shichen], gender)
                self.assertEqual(full['soulPalaceBranch'], manual,
                                 f"{desc}: 公式={manual}, iztro={full['soulPalaceBranch']}")

    def test_body_branch(self):
        """身宫地支: 寅起正月顺数到生月, 该宫起子时顺数到生时"""
        for lunar, shichen, gender, ystem, desc in CASES:
            with self.subTest(desc=desc):
                manual = calc_body_branch(lunar[1], shichen)
                full = self.engine.full_chart(lunar, SHICHEN_TO_HOUR[shichen], gender)
                self.assertEqual(full['bodyPalaceBranch'], manual,
                                 f"{desc}: 公式={manual}, iztro={full['bodyPalaceBranch']}")

    def test_soul_stem(self):
        """命宫天干: 生年干五虎遁定寅宫天干, 顺数到命宫地支"""
        for lunar, shichen, gender, ystem, desc in CASES:
            with self.subTest(desc=desc):
                soul_b = calc_soul_branch(lunar[1], shichen)
                manual = calc_soul_stem(ystem, soul_b)
                full = self.engine.full_chart(lunar, SHICHEN_TO_HOUR[shichen], gender)
                soul_palace = next((p for p in full['palaces'].values()
                                     if p.get('branch') == full['soulPalaceBranch']), {})
                self.assertEqual(soul_palace.get('stem'), manual,
                                 f"{desc}: 公式={manual}, iztro={soul_palace.get('stem')}")

    def test_five_elements_ju(self):
        """五行局: 命宫干支纳音 -> 水二/木三/金四/土五/火六局"""
        for lunar, shichen, gender, ystem, desc in CASES:
            with self.subTest(desc=desc):
                soul_b = calc_soul_branch(lunar[1], shichen)
                soul_s = calc_soul_stem(ystem, soul_b)
                manual = calc_five_ju(soul_s, soul_b)
                full = self.engine.full_chart(lunar, SHICHEN_TO_HOUR[shichen], gender)
                self.assertEqual(full['fiveElementsClass'], manual,
                                 f"{desc}: 公式={manual}, iztro={full['fiveElementsClass']}")


if __name__ == "__main__":
    unittest.main()
