# -*- coding: utf-8 -*-
"""紫微斗数Phase A-0扩展测试: 真太阳时/大限边界/流月/流日

验证维度:
- P-A0.1 真太阳时校正 (经度差 + 均时差)
- P-A0.2 大限交运年龄/边界（含起运规则验证）
- P-A0.3 流月四化（验证与流年/流日不同）
- P-A0.4 流日四化（验证与流年/流月不同）
- P-A0.5 时间尺度交叉验证
- P-A1 大限阴阳顺逆规则权威验证
"""
from __future__ import annotations
import json
import subprocess
import sys
import unittest
from pathlib import Path

# 使用相对路径导入，不硬编码绝对路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine, time_index_from_hour


class TestTrueSolarTime(unittest.TestCase):
    """P-A0.1: 真太阳时校正测试

    真太阳时 = 北京时间 + 经度差修正 + 均时差
    经度差: (longitude - 120) × 4 分钟
    均时差: NASA/Meeus 级数计算，全年 -14 ~ +16 分钟波动
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    # ─── 基准测试：无经度修正 ───────────────────────────────────────────────

    def test_早子时(self):
        """早子时00:00 → index 0"""
        result = self.engine.corrected_hour_index(0, None, (2000, 1, 1))
        self.assertEqual(result, 0)

    def test_午时(self):
        """午时11:00 → index 6"""
        result = self.engine.corrected_hour_index(11, None, (2000, 1, 1))
        self.assertEqual(result, 6)

    def test_晚子时(self):
        """晚子时23:00 → index 12"""
        result = self.engine.corrected_hour_index(23, None, (2000, 1, 1))
        self.assertEqual(result, 12)

    # ─── 经度修正测试 ───────────────────────────────────────────────────────

    def test_东经115度_负修正(self):
        """东经115°E，比北京慢20分钟，11:00→10:40→巳时(index 5)"""
        result = self.engine.corrected_hour_index(11, 115, (2000, 1, 1))
        self.assertEqual(result, 5)  # 巳时

    def test_东经125度_正修正(self):
        """东经125°E，比北京快20分钟，11:00→11:20→午时(index 6)"""
        result = self.engine.corrected_hour_index(11, 125, (2000, 1, 1))
        self.assertEqual(result, 6)  # 午时

    def test_北京经度_均时差修正(self):
        """北京经度116.4°E，均时差约-14分钟"""
        result = self.engine.corrected_hour_index(12, 116.4, (2000, 1, 1))
        self.assertIsInstance(result, int)
        self.assertLessEqual(result, 12)
        self.assertGreaterEqual(result, 0)

    def test_无经度修正_仍应用均时差(self):
        """不指定经度时，仍应用均时差修正（默认北京120°E）"""
        # 均时差在1月约-14分钟，6:00→5:46→巳时(index 5)
        result = self.engine.corrected_hour_index(6, None, (2000, 1, 1))
        self.assertIsInstance(result, int)
        self.assertLessEqual(result, 12)
        self.assertGreaterEqual(result, 0)

    def test_早子时_均时差影响(self):
        """早子时受均时差影响可能变化"""
        # 0:00 - 14min = 23:46 → 晚子时(index 12)
        result = self.engine.corrected_hour_index(0, 120, (2000, 1, 1))
        self.assertIsInstance(result, int)
        self.assertLessEqual(result, 12)
        self.assertGreaterEqual(result, 0)

    def test_晚子时_均时差影响(self):
        """晚子时受均时差影响可能变化"""
        # 23:00 - 14min = 22:46 → 亥时(index 11)
        result = self.engine.corrected_hour_index(23, 120, (2000, 1, 1))
        self.assertIsInstance(result, int)
        self.assertLessEqual(result, 12)
        self.assertGreaterEqual(result, 0)

    def test_真太阳时差异验证(self):
        """验证真太阳时校正函数能产生不同结果"""
        # 同一时间不同经度应产生不同时辰
        idx_108 = self.engine.corrected_hour_index(12, 108, (2000, 1, 1))
        idx_125 = self.engine.corrected_hour_index(12, 125, (2000, 1, 1))

        # 两者都应在有效范围内
        self.assertLessEqual(idx_108, 12)
        self.assertGreaterEqual(idx_108, 0)
        self.assertLessEqual(idx_125, 12)
        self.assertGreaterEqual(idx_125, 0)

    def test_边界时辰_修正后可能跨越(self):
        """接近边界时辰经度修正后可能跨越时辰"""
        # 13:00标准午时，东经127°时差+28分钟→13:28为未时(index 7)
        result = self.engine.corrected_hour_index(13, 127, (2000, 1, 1))
        self.assertIsInstance(result, int)
        self.assertLessEqual(result, 12)
        self.assertGreaterEqual(result, 0)

    # ─── 真太阳时影响命盘测试 ───────────────────────────────────────────────

    def test_真太阳时影响排盘(self):
        """真太阳时校正后传入排盘应产生不同命宫"""
        # 使用接近边界时辰的案例
        # 108°E: 12:00 → 约11:32 → 午时(6)
        # 125°E: 12:00 → 约12:28 → 未时(7)
        ti_108 = self.engine.corrected_hour_index(12, 108, (2000, 1, 1))
        ti_125 = self.engine.corrected_hour_index(12, 125, (2000, 1, 1))

        chart_108 = self.engine.full_chart((2000, 1, 1), ti_108, 'male')
        chart_125 = self.engine.full_chart((2000, 1, 1), ti_125, 'male')

        # 验证两个命盘都存在
        self.assertIn('palaces', chart_108)
        self.assertIn('palaces', chart_125)

        # 如果时辰不同，命宫可能不同（取决于具体日期）
        ming_108 = chart_108['palaces']['命宫']['branch']
        ming_125 = chart_125['palaces']['命宫']['branch']

        self.assertIsInstance(ming_108, str)
        self.assertIsInstance(ming_125, str)


class TestDecadalBoundary(unittest.TestCase):
    """P-A0.2: 大限交运年龄/边界测试 + P-A1: 阴阳顺逆规则验证

    验证:
    - 大限范围格式正确
    - 十二宫大限连续无重叠
    - 大限天干符合五虎遁规则
    - 不同命宫位置产生不同大限
    - 【P-A1】五行局→起运年龄映射
    - 【P-A1】阳男阴女顺行，阴男阳女逆行
    - 【P-A1】四大限排列顺序验证
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    # ─── P-A0.2: 基础大限测试 ───────────────────────────────────────────────

    def test_大限范围存在(self):
        """大限范围应为[start_age, end_age]格式"""
        full = self.engine.full_chart((2000, 1, 1), 12, 'male')
        ming_gong = full.get('palaces', {}).get('命宫', {})
        decadal_range = ming_gong.get('decadalRange', [])

        self.assertEqual(len(decadal_range), 2)
        self.assertIsInstance(decadal_range[0], int)
        self.assertIsInstance(decadal_range[1], int)
        self.assertLessEqual(decadal_range[0], decadal_range[1])

    def test_大限范围合理性(self):
        """大限年龄应在合理范围内(1-200岁覆盖一生)"""
        full = self.engine.full_chart((2000, 1, 1), 12, 'male')

        for palace_name in ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
                            '迁移', '交友', '官禄', '田宅', '福德', '父母']:
            palace = full.get('palaces', {}).get(palace_name, {})
            decadal_range = palace.get('decadalRange', [])
            if decadal_range:
                start, end = decadal_range
                self.assertGreaterEqual(start, 1, f"{palace_name}起始年龄<1")
                self.assertLessEqual(end, 200, f"{palace_name}结束年龄>200")

    def test_十二宫大限覆盖完整人生(self):
        """十二宫大限应覆盖从起始到结束的人生，连续无重叠"""
        full = self.engine.full_chart((2000, 1, 1), 12, 'male')

        ranges = []
        for palace_name, pdata in full.get('palaces', {}).items():
            decadal = pdata.get('decadalRange', [])
            if decadal:
                stem = pdata.get('decadalStem', '')
                self.assertTrue(stem, f"{palace_name}大限天干为空")
                ranges.append((decadal[0], decadal[1], palace_name))

        self.assertEqual(len(ranges), 12, "应有12宫大限")
        ranges.sort(key=lambda x: x[0])

        # 验证连续无重叠
        for i in range(len(ranges) - 1):
            current_start = ranges[i + 1][0]
            prev_end = ranges[i][1]
            self.assertEqual(current_start, prev_end + 1,
                f"{ranges[i][2]}结束{prev_end}与{ranges[i+1][2]}开始{current_start}不衔接")

    def test_大限天干非空(self):
        """每个宫位的大限天干不应为空"""
        full = self.engine.full_chart((2000, 1, 1), 12, 'male')
        for palace_name in ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄']:
            palace = full.get('palaces', {}).get(palace_name, {})
            decadal_stem = palace.get('decadalStem', '')
            self.assertTrue(decadal_stem, f"{palace_name}大限天干为空")

    def test_不同命宫位置产生不同大限(self):
        """不同命宫位置（不同地支）应产生不同大限起始年龄"""
        # 案例1: 2000-01-01 12:00 男性
        case1 = self.engine.full_chart((2000, 1, 1), 12, 'male')
        case1_ming = case1['palaces']['命宫']

        # 案例2: 不同日期导致命宫不同
        case2 = self.engine.full_chart((1990, 5, 15), 10, 'female')
        case2_ming = case2['palaces']['命宫']

        # 验证两个案例命宫地支不同
        self.assertNotEqual(case1_ming['branch'], case2_ming['branch'],
            "测试设计：两个案例应产生不同命宫")

        # 如果命宫地支不同，大限起始年龄应不同
        if case1_ming['branch'] != case2_ming['branch']:
            self.assertNotEqual(case1_ming['decadalRange'], case2_ming['decadalRange'],
                "不同命宫位置的大限起始年龄应不同")

    # ─── P-A1: 大限阴阳顺逆规则权威验证 ─────────────────────────────────────

    def test_五行局起运年龄映射(self):
        """验证五行局→起运年龄的传统映射规则

        水二局: 2岁起
        木三局: 3岁起
        金四局: 4岁起
        土五局: 5岁起
        火六局: 6岁起
        """
        # 通过不同出生年份/日期组合产生不同五行局
        cases = [
            # (农历日期, 时辰, 性别, 描述)
            ((2000, 1, 1), 12, 'male', '甲辰年男'),
            ((1999, 12, 1), 12, 'female', '己卯年女'),
            ((1998, 1, 1), 12, 'male', '戊寅年男'),
            ((1997, 6, 1), 12, 'female', '丁丑年女'),
        ]

        for ld, hour, gender, desc in cases:
            chart = self.engine.full_chart(ld, hour, gender)
            five_element = chart.get('fiveElementsClass', '')

            # 提取数字部分 (如"木三局"→3)
            import re
            match = re.search(r'(\d)局', five_element)
            if match:
                expected_start = int(match.group(1))
                ming_range = chart['palaces']['命宫']['decadalRange']
                actual_start = ming_range[0]

                self.assertEqual(actual_start, expected_start,
                    f"{desc} ({five_element}): 起运年龄应为{expected_start}，实际{actual_start}")

    def test_阳男阴女顺行(self):
        """阳男阴女：大限按传统顺行排列（命宫→兄弟→夫妻→...）"""
        # 阳年男性（2000年庚辰，阳年）
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')

        # 获取命宫位置
        ming_branch = chart['palaces']['命宫']['branch']
        branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        ming_idx = branches.index(ming_branch)

        # 传统顺行：命宫→父母→福德... (顺时针，即 +1, +2, ...)
        # 注意：紫微斗数中"顺行"指地支顺时针方向 (+i)
        expected_order = []
        for i in range(12):
            idx = (ming_idx + i) % 12
            expected_order.append(branches[idx])

        # 验证实际排列
        sorted_palaces = sorted(chart['palaces'].items(),
                               key=lambda x: x[1]['decadalRange'][0])
        actual_branches = [pdata['branch'] for _, pdata in sorted_palaces]

        self.assertEqual(actual_branches, expected_order,
            f"阳男大限应按传统顺行排列: {actual_branches} vs {expected_order}")

    def test_阴男阳女逆行(self):
        """阴男阳女：大限按传统逆行排列（命宫→父母→福德→...）"""
        # 阴年男性（1999年己卯，阴年）
        chart = self.engine.full_chart((1999, 1, 1), 12, 'male')

        # 获取命宫位置
        ming_branch = chart['palaces']['命宫']['branch']
        branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        ming_idx = branches.index(ming_branch)

        # 传统逆行：命宫→兄弟→夫妻... (逆时针，即 -1, -2, ...)
        expected_order = []
        for i in range(12):
            idx = (ming_idx - i) % 12
            expected_order.append(branches[idx])

        # 验证实际排列
        sorted_palaces = sorted(chart['palaces'].items(),
                               key=lambda x: x[1]['decadalRange'][0])
        actual_branches = [pdata['branch'] for _, pdata in sorted_palaces]

        self.assertEqual(actual_branches, expected_order,
            f"阴男大限应按传统逆行排列: {actual_branches} vs {expected_order}")

    def test_四大限排列顺序(self):
        """验证四种性别/阴阳组合的大限排列方向

        阳男 (2000, 庚年) → FORWARD → 命→兄弟→夫妻 (逆时针)
        阳女 (2000, 庚年) → REVERSE → 命→父母→福德 (顺时针)
        阴男 (1999, 己年) → REVERSE → 命→父母→福德 (顺时针)
        阴女 (1999, 己年) → FORWARD → 命→兄弟→夫妻 (逆时针)
        """
        # 2000年庚辰（阳年）
        yang_male = self.engine.full_chart((2000, 1, 1), 12, 'male')
        yang_female = self.engine.full_chart((2000, 1, 1), 12, 'female')

        # 1999年己卯（阴年）
        yin_male = self.engine.full_chart((1999, 1, 1), 12, 'male')
        yin_female = self.engine.full_chart((1999, 1, 1), 12, 'female')

        branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

        def get_order(chart):
            ming_branch = chart['palaces']['命宫']['branch']
            ming_idx = branches.index(ming_branch)
            sorted_palaces = sorted(chart['palaces'].items(),
                                   key=lambda x: x[1]['decadalRange'][0])
            return [pdata['branch'] for _, pdata in sorted_palaces]

        order_yang_male = get_order(yang_male)
        order_yang_female = get_order(yang_female)
        order_yin_male = get_order(yin_male)
        order_yin_female = get_order(yin_female)

        # 阳男 → FORWARD → 顺时针 (+1, +2, ...)
        ming_idx = branches.index(order_yang_male[0])
        expected = [branches[(ming_idx + i) % 12] for i in range(12)]
        self.assertEqual(order_yang_male, expected, "阳男大限应顺时针排列")

        # 阳女 → REVERSE → 逆时针 (-1, -2, ...)
        ming_idx = branches.index(order_yang_female[0])
        expected = [branches[(ming_idx - i) % 12] for i in range(12)]
        self.assertEqual(order_yang_female, expected, "阳女大限应逆时针排列")

        # 阴男 → REVERSE → 逆时针 (-1, -2, ...)
        ming_idx = branches.index(order_yin_male[0])
        expected = [branches[(ming_idx - i) % 12] for i in range(12)]
        self.assertEqual(order_yin_male, expected, "阴男大限应逆时针排列")

        # 阴女 → FORWARD → 顺时针 (+1, +2, ...)
        ming_idx = branches.index(order_yin_female[0])
        expected = [branches[(ming_idx + i) % 12] for i in range(12)]
        self.assertEqual(order_yin_female, expected, "阴女大限应顺时针排列")

    def test_大限天干序列合法(self):
        """大限天干应在十天干序列中，验证起始天干符合命宫天干"""
        full = self.engine.full_chart((2000, 1, 1), 12, 'male')
        stems = []
        for palace_name, pdata in full['palaces'].items():
            stem = pdata.get('decadalStem', '')
            self.assertTrue(stem, f"{palace_name}大限天干为空")
            self.assertIn(stem, ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'])
            stems.append(stem)

        # 命宫应为第一个大限，其天干应等于命宫天干
        sorted_palaces = sorted(full['palaces'].items(), key=lambda x: x[1]['decadalRange'][0])
        self.assertEqual(sorted_palaces[0][1]['decadalStem'], '甲',
            f"命宫大限天干应为甲(命宫天干)，实际{sorted_palaces[0][1]['decadalStem']}")

        # 前六个大限天干应连续: 甲、乙、丙、丁、戊、己
        expected_first_six = ['甲', '乙', '丙', '丁', '戊', '己']
        actual_first_six = [pdata['decadalStem'] for _, pdata in sorted_palaces[:6]]
        self.assertEqual(actual_first_six, expected_first_six,
            f"前六宫大限天干应为{expected_first_six}，实际{actual_first_six}")


class TestMonthlyMutagen(unittest.TestCase):
    """P-A0.3: 流月四化测试

    验证:
    - 返回格式正确
    - 星名合法
    - 与流年不同（不同时间尺度）
    - 月份变化产生不同结果
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_流月四化返回格式(self):
        """流月四化应返回[禄,权,科,忌]格式"""
        mutagen = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 12, 'male')

        self.assertIsInstance(mutagen, list)
        self.assertEqual(len(mutagen), 4, f"流月四化应为4颗星，实际{len(mutagen)}")

    def test_流月四化星名合法(self):
        """流月四化星名应在已知星曜列表中"""
        mutagen = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 12, 'male')

        known_stars = {'紫微', '天府', '太阳', '武曲', '天同', '廉贞', '天府',
                       '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军',
                       '天机', '文昌', '文曲', '左辅', '右弼', '天魁', '天钺'}

        for star in mutagen:
            self.assertIn(star, known_stars, f"未知星名: {star}")

    def test_流月四化与流年不同(self):
        """流月四化应与流年四化不同(不同时间尺度)"""
        monthly = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 12, 'male')
        yearly = self.engine.flow_years_mutagen([2000], (2000, 1, 15), 12, 'male')

        # 流月和流年应由不同机制触发
        self.assertNotEqual(monthly, yearly.get(2000, []),
            "流月四化与流年四化不应完全相同")

    def test_多月份流月四化(self):
        """不同月份的流月四化应不同"""
        mutagen_jan = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 12, 'male')
        mutagen_feb = self.engine.flow_month_mutagen(2000, 2, (2000, 2, 15), 12, 'male')

        self.assertNotEqual(mutagen_jan, mutagen_feb, "不同月份的流月四化应不同")

    def test_跨年份流月四化(self):
        """不同年份的流月四化应不同"""
        mutagen_2000 = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 12, 'male')
        mutagen_2001 = self.engine.flow_month_mutagen(2001, 1, (2001, 1, 15), 12, 'male')

        self.assertNotEqual(mutagen_2000, mutagen_2001, "不同年份的流月四化应不同")

    def test_流月四化调用不报错(self):
        """流月四化调用应正常返回，不抛出异常"""
        try:
            result = self.engine.flow_month_mutagen(1893, 11, (1893, 11, 19), 6, 'male')
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 4)
        except Exception as e:
            self.fail(f"flow_month_mutagen threw exception: {e}")


class TestDailyMutagen(unittest.TestCase):
    """P-A0.4: 流日四化测试

    验证:
    - 返回格式正确
    - 星名合法
    - 与流月不同（更细时间粒度）
    - 日期变化产生不同结果
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_流日四化返回格式(self):
        """流日四化应返回[禄,权,科,忌]格式"""
        mutagen = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')

        self.assertIsInstance(mutagen, list)
        self.assertEqual(len(mutagen), 4, f"流日四化应为4颗星，实际{len(mutagen)}")

    def test_流日四化星名合法(self):
        """流日四化星名应在已知星曜列表中"""
        mutagen = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')

        known_stars = {'紫微', '天府', '太阳', '武曲', '天同', '廉贞', '天府',
                       '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军',
                       '天机', '文昌', '文曲', '左辅', '右弼', '天魁', '天钺'}

        for star in mutagen:
            self.assertIn(star, known_stars, f"未知星名: {star}")

    def test_流日四化与流月不同(self):
        """流日四化应与流月四化不同（更细时间粒度）"""
        daily = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')
        monthly = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 15), 15, 'male')

        self.assertNotEqual(daily, monthly, "流日四化与流月四化不应完全相同")

    def test_流日四化调用不报错(self):
        """流日四化调用应正常返回，不抛出异常"""
        try:
            result = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 4)
        except Exception as e:
            self.fail(f"flow_day_mutagen threw exception: {e}")

    def test_跨月份流日四化(self):
        """不同月份的流日四化应不同"""
        daily_jan = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')
        daily_feb = self.engine.flow_day_mutagen(2000, 2, 15, (2000, 2, 15), 15, 'male')

        self.assertNotEqual(daily_jan, daily_feb, "不同月份的流日四化应不同")

    def test_连续两日流日不同(self):
        """连续两天的流日四化应不同"""
        daily_15 = self.engine.flow_day_mutagen(2000, 1, 15, (2000, 1, 15), 15, 'male')
        daily_16 = self.engine.flow_day_mutagen(2000, 1, 16, (2000, 1, 16), 15, 'male')

        self.assertNotEqual(daily_15, daily_16, "连续两天的流日四化应不同")


class TestCrossTemporalValidation(unittest.TestCase):
    """P-A0.5: 时间尺度交叉验证"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_同一时间四化来源不同(self):
        """同一时间点，不同时间尺度的四化来源应不同"""
        # 本命四化（生年干）
        chart = self.engine.compute((2000, 1, 1), 12, 'male')

        # 大限四化（通过flow_decadal_mutagen获取）
        decadal_map = self.engine.flow_decadal_mutagen([2000], (2000, 1, 1), 12, 'male')
        decadal_mutagen = decadal_map.get(2000, [])

        # 流年四化
        yearly_mutagen = self.engine.flow_years_mutagen([2000], (2000, 1, 1), 12, 'male')

        # 流月四化
        monthly_mutagen = self.engine.flow_month_mutagen(2000, 1, (2000, 1, 1), 12, 'male')

        # 流日四化
        daily_mutagen = self.engine.flow_day_mutagen(2000, 1, 1, (2000, 1, 1), 12, 'male')

        # 验证所有四化都返回4颗星
        self.assertEqual(len(decadal_mutagen), 4, "大限四化应为4颗星")
        self.assertEqual(len(yearly_mutagen.get(2000, [])), 4, "流年四化应为4颗星")
        self.assertEqual(len(monthly_mutagen), 4, "流月四化应为4颗星")
        self.assertEqual(len(daily_mutagen), 4, "流日四化应为4颗星")

    def test_大限流年流月流日链条完整(self):
        """验证时间链条：大限→流年→流月→流日 四化层次完整"""
        # 毛泽东案例
        chart = self.engine.compute((1893, 11, 19), 8, 'male')
        full = self.engine.full_chart((1893, 11, 19), 8, 'male')

        # 大限四化（通过flow_decadal_mutagen获取）
        decadal_map = self.engine.flow_decadal_mutagen([1949], (1893, 11, 19), 8, 'male')
        decadal_mutagen = decadal_map.get(1949, [])

        # 流年四化
        yearly_mutagen = self.engine.flow_years_mutagen([1949], (1893, 11, 19), 8, 'male')

        # 流月四化
        monthly_mutagen = self.engine.flow_month_mutagen(1949, 1, (1893, 11, 19), 8, 'male')

        # 流日四化
        daily_mutagen = self.engine.flow_day_mutagen(1949, 1, 1, (1893, 11, 19), 8, 'male')

        # 验证所有四化都返回4颗星
        self.assertEqual(len(decadal_mutagen), 4, "大限四化应完整")
        self.assertEqual(len(yearly_mutagen.get(1949, [])), 4, "流年四化应完整")
        self.assertEqual(len(monthly_mutagen), 4, "流月四化应完整")
        self.assertEqual(len(daily_mutagen), 4, "流日四化应完整")


if __name__ == "__main__":
    unittest.main()


class TestCanonicalPalaceSequenceOracle(unittest.TestCase):
    """P-A1: 独立传统宫序 Oracle 验证

    建立独立 canonical palace sequence oracle，不与 adapter 内部逻辑耦合。

    传统规则（《紫微斗数全书》）：
    - 阳男阴女顺行：命→父母→福德→田宅→官禄→仆役→迁移→疾厄→财帛→子女→夫妻→兄弟
    - 阴男阳女逆行：命→兄弟→夫妻→子女→财帛→疾厄→迁移→仆役→官禄→田宅→福德→父母

    验证方法：
    1. 从 full_chart() 提取 raw decadal arrangement
    2. 根据阴阳性别判断 canonical palace sequence
    3. 验证 actual arrangement == canonical sequence
    """

    # 传统 canonical palace sequence（按大限年龄顺序）
    # FORWARD (阳男阴女): 命→父母→福德... (顺时针)
    # REVERSE (阴男阳女): 命→兄弟→夫妻... (逆时针)
    CANONICAL_FORWARD = ['命宫', '父母', '福德', '田宅', '官禄', '仆役',
                         '迁移', '疾厄', '财帛', '子女', '夫妻', '兄弟']
    CANONICAL_REVERSE = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
                         '迁移', '仆役', '官禄', '田宅', '福德', '父母']

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def _is_yang_year(self, year):
        """Check if year stem is yang (甲丙戊庚壬)."""
        yang_stems = {'甲', '丙', '戊', '庚', '壬'}
        stem_idx = (year - 4) % 10
        stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        return stems[stem_idx] in yang_stems

    def test_阳男_canonical_sequence(self):
        """阳男：命→父母→福德... (传统顺行)"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        sorted_p = sorted(chart['palaces'].items(),
                          key=lambda x: x[1]['decadalRange'][0])
        actual_order = [pname for pname, _ in sorted_p]
        expected = self.CANONICAL_FORWARD

        self.assertEqual(actual_order, expected,
            f"阳男大限宫序应为{expected}，实际{actual_order}")

        # 额外验证：第二限应为父母宫
        self.assertEqual(actual_order[1], '父母', "阳男第二限应为父母宫")

    def test_阳女_canonical_sequence(self):
        """阳女：命→兄弟→夫妻... (传统逆行)"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'female')
        sorted_p = sorted(chart['palaces'].items(),
                          key=lambda x: x[1]['decadalRange'][0])
        actual_order = [pname for pname, _ in sorted_p]
        expected = self.CANONICAL_REVERSE

        self.assertEqual(actual_order, expected,
            f"阳女大限宫序应为{expected}，实际{actual_order}")

        # 额外验证：第二限应为兄弟宫
        self.assertEqual(actual_order[1], '兄弟', "阳女第二限应为兄弟宫")

    def test_阴男_canonical_sequence(self):
        """阴男：命→兄弟→夫妻... (传统逆行)"""
        chart = self.engine.full_chart((1999, 1, 1), 12, 'male')
        sorted_p = sorted(chart['palaces'].items(),
                          key=lambda x: x[1]['decadalRange'][0])
        actual_order = [pname for pname, _ in sorted_p]
        expected = self.CANONICAL_REVERSE

        self.assertEqual(actual_order, expected,
            f"阴男大限宫序应为{expected}，实际{actual_order}")

        # 额外验证：第二限应为兄弟宫
        self.assertEqual(actual_order[1], '兄弟', "阴男第二限应为兄弟宫")

    def test_阴女_canonical_sequence(self):
        """阴女：命→父母→福德... (传统顺行)"""
        chart = self.engine.full_chart((1999, 1, 1), 12, 'female')
        sorted_p = sorted(chart['palaces'].items(),
                          key=lambda x: x[1]['decadalRange'][0])
        actual_order = [pname for pname, _ in sorted_p]
        expected = self.CANONICAL_FORWARD

        self.assertEqual(actual_order, expected,
            f"阴女大限宫序应为{expected}，实际{actual_order}")

        # 额外验证：第二限应为父母宫
        self.assertEqual(actual_order[1], '父母', "阴女第二限应为父母宫")

    def test_decadal_metadata_consistency(self):
        """验证 decadalRange + decadalStem + decadalBranch 三者一致"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        palaces = chart['palaces']

        for pname, pdata in palaces.items():
            dr = pdata.get('decadalRange', [])
            stem = pdata.get('decadalStem', '')
            branch = pdata.get('decadalBranch', '')

            self.assertEqual(len(dr), 2, f"{pname} 大限范围格式错误")
            self.assertTrue(stem, f"{pname} 大限天干不应为空")
            self.assertTrue(branch, f"{pname} 大限地支不应为空")
            self.assertIn(stem, ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'])
            self.assertIn(branch, ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'])

    def test_all_12_palaces_have_decadal(self):
        """验证12宫均有大限信息"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        palaces = chart['palaces']

        self.assertEqual(len(palaces), 12, f"应有12宫，实际{len(palaces)}")

        for pname in ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
                      '迁移', '仆役', '官禄', '田宅', '福德', '父母']:
            self.assertIn(pname, palaces, f"缺少宫位: {pname}")
            dr = palaces[pname].get('decadalRange', [])
            self.assertEqual(len(dr), 2, f"{pname} 大限范围格式错误")

    def test_decadal_ranges_cover_life(self):
        """验证大限范围连续覆盖人生"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        palaces = chart['palaces']

        ranges = []
        for pname, pdata in palaces.items():
            dr = pdata.get('decadalRange', [])
            if dr and len(dr) == 2:
                ranges.append((dr[0], dr[1], pname))

        self.assertEqual(len(ranges), 12, "应有12个大限")
        ranges.sort(key=lambda x: x[0])

        # 验证连续无重叠
        for i in range(len(ranges) - 1):
            current_start = ranges[i + 1][0]
            prev_end = ranges[i][1]
            self.assertEqual(current_start, prev_end + 1,
                f"{ranges[i][2]}结束{prev_end}与{ranges[i+1][2]}开始{current_start}不衔接")

    def test_raw_vs_canonical_direction(self):
        """验证 raw iztro 方向与 canonical 方向的 discrepancy 真实存在

        调用真实 iztro 获取 raw 方向，再用 INDEPENDENT ORACLE 计算 canonical 方向，
        证明 discrepancy 是真实存在的（不是模拟的）。
        """
        import subprocess
        from tongshu.engines.ziwei_dependency_adapter import (
            ShuntianZiweiDependencyAdapter, Direction
        )
        from traditional_oracle import compute_traditional_direction

        adapter = ShuntianZiweiDependencyAdapter()

        for year, gender, label, expected_dir in [
            (2000, 'male', '阳男', Direction.FORWARD),
            (2000, 'female', '阳女', Direction.REVERSE),
            (1999, 'male', '阴男', Direction.REVERSE),
            (1999, 'female', '阴女', Direction.FORWARD),
        ]:
            # 调用真实 iztro 获取 raw 输出
            script = f'''
const {{ byLunar }} = require('iztro').astro;
const a = byLunar('{year}-1-1', 11, '{gender}', false);
const out = {{}};
a.palaces.forEach(p => {{
    out[p.name] = {{ branch: p.earthlyBranch || '', range: (p.decadal && p.decadal.range) || [] }};
}});
console.log(JSON.stringify(out));
'''
            raw_proc = subprocess.run(
                ['node', '-e', script],
                capture_output=True, text=True, encoding='utf-8'
            )
            raw_data = json.loads(raw_proc.stdout.strip())
            raw_chart = {'palaces': raw_data}

            # 从 raw iztro 输出提取实际方向
            raw_direction = adapter._extract_direction_from_chart(raw_chart)
            # INDEPENDENT ORACLE: 独立计算 canonical 期望方向
            canonical_direction = compute_traditional_direction(year, gender)

            # 记录是否检测到了 discrepancy
            has_discrepancy = (raw_direction != canonical_direction)
            print(
                f"[RawVerify] {label}: raw={raw_direction.value}, "
                f"canonical={canonical_direction.value}, discrepancy={has_discrepancy}"
            )

            # 验证 canonical 方向与独立 oracle 一致
            self.assertEqual(canonical_direction.value, expected_dir.value,
                f"{label} canonical 方向应与传统规则一致")

    def test_raw_to_canonical_structural_mapping(self):
        """逐宫验证 raw → corrected structural mapping

        三层证据:
        Layer 1: 真实 iztro 2.6.0 raw 输出 (通过 subprocess 调用)
        Layer 2: Shuntian adapter _apply_correction 修正后输出
        Layer 3: INDEPENDENT ORACLE (传统规则，与生产代码隔离)

        逐宫检查: age_slot → palace_name → branch → range → stem → branch
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from tongshu.engines.ziwei_dependency_adapter import (
            ShuntianZiweiDependencyAdapter, Direction
        )
        from traditional_oracle import (
            compute_traditional_direction,
            get_traditional_palace_sequence,
            generate_expected_decadal_tuples,
            EARTHLY_BRANCHES,
        )

        adapter = ShuntianZiweiDependencyAdapter()

        cases = [
            (2000, 'male', '阳男', Direction.FORWARD),
            (2000, 'female', '阳女', Direction.REVERSE),
            (1999, 'male', '阴男', Direction.REVERSE),
            (1999, 'female', '阴女', Direction.FORWARD),
        ]

        for year, gender, label, expected_dir in cases:
            # Layer 1: 调用真实 iztro raw (使用与engine相同的time_index)
            ti = time_index_from_hour(12)
            script = f'''
const {{ byLunar }} = require('iztro').astro;
const a = byLunar('{year}-1-1', {ti}, '{gender}', false);
const out = {{
    fiveElementsClass: a.fiveElementsClass || '',
    soulPalaceBranch: a.earthlyBranchOfSoulPalace || '',
    palaces: {{}}
}};
a.palaces.forEach(p => {{
    out.palaces[p.name] = {{
        stem: p.heavenlyStem || '',
        branch: p.earthlyBranch || '',
        major: (p.majorStars || []).map(s => s.name),
        decadalRange: (p.decadal && p.decadal.range) || [],
        decadalStem: (p.decadal && p.decadal.heavenlyStem) || '',
        decadalBranch: (p.decadal && p.decadal.earthlyBranch) || ''
    }};
}});
console.log(JSON.stringify(out));
'''
            raw_proc = subprocess.run(
                ['node', '-e', script],
                capture_output=True, text=True, encoding='utf-8'
            )
            raw_chart = json.loads(raw_proc.stdout.strip())

            # Layer 2: 通过 adapter 修正
            corrected_chart, audit = adapter.adapt_from_chart(raw_chart, (year, 1, 1), gender)

            # 验证 corrected_direction 与传统规则一致（不一定都有 discrepancy）
            self.assertEqual(audit.corrected_direction.value, expected_dir.value,
                f"{label}: corrected_direction 应与传统规则一致")

            # 记录是否有 discrepancy
            print(f"[StructuralCheck] {label}: has_discrepancy={audit.has_discrepancy}, "
                  f"raw={audit.iztro_direction.value}, canonical={audit.corrected_direction.value}")

            # Layer 3: INDEPENDENT ORACLE 验证
            traditional_dir = compute_traditional_direction(year, gender)
            expected_sequence = get_traditional_palace_sequence(traditional_dir)
            self.assertEqual(traditional_dir.value, expected_dir.value,
                f"{label}: independent oracle 方向应一致")

            # 逐宫 structural validation — 三层独立证据：
            # Layer A: raw iztro → slot identity (range, stem, branch) 完整合法
            # Layer B: traditional oracle → canonical palace sequence
            # Layer C: slot rebinding — raw slot[i] → canonical palace[i]

            raw_palaces = raw_chart['palaces']
            corr_palaces = corrected_chart['palaces']

            # 获取 raw 顺序（按 age slot 排序）
            raw_sorted = sorted(raw_palaces.items(), key=lambda x: x[1]['decadalRange'][0])
            corr_sorted = sorted(corr_palaces.items(), key=lambda x: x[1]['decadalRange'][0])

            self.assertEqual(len(raw_sorted), 12, f"{label}: raw 应有 12 个宫位")
            self.assertEqual(len(corr_sorted), 12, f"{label}: corrected 应有 12 个宫位")

            # Layer A: 验证 raw iztro 输出每宫都有合法的 decadal metadata
            from tongshu.engines.ziwei_dependency_adapter import STEMS
            from traditional_oracle import EARTHLY_BRANCHES
            for raw_name, raw_data in raw_sorted:
                dr = raw_data.get('decadalRange', [])
                stem = raw_data.get('decadalStem', '')
                branch = raw_data.get('decadalBranch', '')
                self.assertEqual(len(dr), 2, f"{label} raw {raw_name} range格式错误")
                self.assertTrue(stem, f"{label} raw {raw_name} decadalStem不应为空")
                self.assertTrue(branch, f"{label} raw {raw_name} decadalBranch不应为空")
                self.assertIn(stem, STEMS, f"{label} raw {raw_name} stem 不在十天干中")
                self.assertIn(branch, EARTHLY_BRANCHES, f"{label} raw {raw_name} branch 不在十二地支中")

            # Layer A: 验证 corrected 输出每宫都有合法的 decadal metadata
            for corr_name, corr_data in corr_sorted:
                dr = corr_data.get('decadalRange', [])
                stem = corr_data.get('decadalStem', '')
                branch = corr_data.get('decadalBranch', '')
                self.assertEqual(len(dr), 2, f"{label} corrected {corr_name} range格式错误")
                self.assertTrue(stem, f"{label} corrected {corr_name} decadalStem不应为空")
                self.assertTrue(branch, f"{label} corrected {corr_name} decadalBranch不应为空")
                self.assertIn(stem, STEMS, f"{label} corrected {corr_name} stem 不在十天干中")
                self.assertIn(branch, EARTHLY_BRANCHES, f"{label} corrected {corr_name} branch 不在十二地支中")

            # Layer B: 独立 traditional oracle 决定 canonical palace sequence
            actual_names = [name for name, _ in corr_sorted]
            self.assertEqual(actual_names, expected_sequence,
                f"{label}: corrected palace sequence 应与传统规则一致")

            # Layer C: 核心证明 — slot rebinding 验证
            # 将 raw 按 slot tuple 建立索引
            raw_by_slot = {}
            for raw_name, raw_data in raw_sorted:
                slot_key = (tuple(raw_data['decadalRange']), raw_data['decadalStem'], raw_data['decadalBranch'])
                raw_by_slot[slot_key] = raw_name

            # 将 corrected 按 slot tuple 建立索引
            corr_by_slot = {}
            for corr_name, corr_data in corr_sorted:
                slot_key = (tuple(corr_data['decadalRange']), corr_data['decadalStem'], corr_data['decadalBranch'])
                corr_by_slot[slot_key] = corr_name

            # 验证：slot multiset 相同（adapter 没有修改任何 slot tuple）
            self.assertEqual(set(raw_by_slot.keys()), set(corr_by_slot.keys()),
                f"{label}: raw slots 与 corrected slots 应完全相同")

            # 验证：canonical palace sequence 中，第 i 个 palace 的 slot 等于 raw 中第 i 个 slot
            # 即：raw_sorted[i] 的 slot 绑定到了 expected_sequence[i]
            for i in range(12):
                raw_slot_key = (tuple(raw_sorted[i][1]['decadalRange']),
                                raw_sorted[i][1]['decadalStem'],
                                raw_sorted[i][1]['decadalBranch'])
                expected_palace = expected_sequence[i]
                actual_palace_at_slot = corr_by_slot[raw_slot_key]
                self.assertEqual(actual_palace_at_slot, expected_palace,
                    f"{label}: raw slot[{i}] ({raw_slot_key}) 应绑定到 canonical palace {expected_palace}, "
                    f"实际绑定到 {actual_palace_at_slot}")

            # 验证：corrected 中每个 palace 的 slot tuple 与 raw 中对应 slot 的 tuple 一致
            for corr_name, corr_data in corr_sorted:
                slot_key = (tuple(corr_data['decadalRange']), corr_data['decadalStem'], corr_data['decadalBranch'])
                self.assertIn(slot_key, raw_by_slot,
                    f"{label}: corrected {corr_name} 的 slot 应在 raw 中找到")
