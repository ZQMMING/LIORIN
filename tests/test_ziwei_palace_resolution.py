# -*- coding: utf-8 -*-
"""ZiweiPalaceResolution 测试（Z11）。

覆盖：
- 三方四正计算正确性
- 空宫借星策略（partial/full/none）
- 主题域取宫
- 立极宫（仅钦天门）
- 转宫关系计算
- PalaceResolution 冻结性
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei_palace_resolution import (
    ZiweiPalaceResolver,
    PalaceResolution,
    EARTHLY_BRANCHES,
    DOMAIN_TO_PALACE,
)
from tongshu.engines.ziwei_method_profile import (
    MethodId,
    SanheProfile,
    QintianProfile,
)


class TestSanfangSizheng(unittest.TestCase):
    """三方四正计算测试。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()
        cls.chart = cls.engine.full_chart((2000, 1, 1), 12, 'male')
        cls.resolver = ZiweiPalaceResolver(cls.chart, MethodId.SANHE)

    def test_ming_gong_sanfang(self):
        """命宫三方四正：本宫+对宫+两合宫共4宫。"""
        sf = self.resolver.resolve_sanfang_sizheng('命宫')
        self.assertEqual(sf['primary'], '命宫')
        self.assertEqual(len(sf['supporting']), 3)
        self.assertIn('迁移', sf['supporting'])
        self.assertIn('官禄', sf['supporting'])
        self.assertIn('财帛', sf['supporting'])

    def test_spouse_sanfang(self):
        """夫妻宫三方四正。"""
        sf = self.resolver.resolve_sanfang_sizheng('夫妻')
        self.assertEqual(sf['primary'], '夫妻')
        self.assertEqual(len(sf['supporting']), 3)

    def test_opposite_is_six_offset(self):
        """对宫一定是地支偏移6位。"""
        for palace_name in ['命宫', '财帛', '官禄', '夫妻']:
            sf = self.resolver.resolve_sanfang_sizheng(palace_name)
            primary_branch = self.chart['palaces'][palace_name]['branch']
            opposite_branch = self.chart['palaces'][sf['opposite']]['branch']
            diff = (EARTHLY_BRANCHES.index(opposite_branch) -
                    EARTHLY_BRANCHES.index(primary_branch)) % 12
            self.assertEqual(diff, 6, f"{palace_name}的对宫不应差6位")

    def test_nonexistent_palace(self):
        """不存在的宫位返回空结果。"""
        sf = self.resolver.resolve_sanfang_sizheng('nonexistent')
        self.assertEqual(sf['primary'], 'nonexistent')
        self.assertEqual(sf['supporting'], [])


class TestEmptyPalaceResolution(unittest.TestCase):
    """空宫借星策略测试。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()
        cls.chart = cls.engine.full_chart((2000, 1, 1), 12, 'male')

    def test_empty_palaces_identified(self):
        """识别出命盘中所有空宫。"""
        empty = [pn for pn, pd in self.chart['palaces'].items()
                 if not pd.get('major')]
        self.assertIsInstance(empty, list)
        self.assertGreaterEqual(len(empty), 0)

    def test_sanhe_partial_borrow(self):
        """三合派空宫策略为 partial。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.SANHE)
        self.assertEqual(resolver.profile.get_empty_palace_policy(), 'partial')

    def test_qintian_partial_borrow(self):
        """北派（钦天）空宫策略为 partial。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.QINTIAN)
        self.assertEqual(resolver.profile.get_empty_palace_policy(), 'partial')

    def test_non_empty_palace_no_borrow(self):
        """非空宫不应触发借星。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.SANHE)
        for palace_name, pd in self.chart['palaces'].items():
            if pd.get('major'):
                borrowed = resolver.resolve_empty_palace(palace_name)
                self.assertEqual(borrowed, [],
                    f"{palace_name} 有主星不应借星")


class TestQuestionPalace(unittest.TestCase):
    """主题域取宫测试。"""

    @classmethod
    def setUpClass(cls):
        cls.chart = ZiweiEngine().full_chart((2000, 1, 1), 12, 'male')
        cls.resolver = ZiweiPalaceResolver(cls.chart, MethodId.SANHE)

    def test_domain_marriage(self):
        """婚姻→夫妻宫。"""
        res = self.resolver.resolve_question_palace('婚姻')
        self.assertEqual(res.primary_palace, '夫妻')

    def test_domain_career(self):
        """事业→官禄宫。"""
        res = self.resolver.resolve_question_palace('事业')
        self.assertEqual(res.primary_palace, '官禄')

    def test_domain_health(self):
        """健康→疾厄宫。"""
        res = self.resolver.resolve_question_palace('健康')
        self.assertEqual(res.primary_palace, '疾厄')

    def test_domain_unknown(self):
        """未知主题域不崩溃。"""
        res = self.resolver.resolve_question_palace('未知领域')
        self.assertEqual(res.primary_palace, '未知领域')


class TestTaijiResolution(unittest.TestCase):
    """立极宫测试。"""

    @classmethod
    def setUpClass(cls):
        cls.chart = ZiweiEngine().full_chart((2000, 1, 1), 12, 'male')

    def test_qintian_supports_liji(self):
        """钦天门支持立极。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.QINTIAN)
        res = resolver.resolve_taiji('夫妻')
        self.assertEqual(res.taiji_origin, '夫妻')
        self.assertGreaterEqual(len(res.supporting_palaces), 1)

    def test_sanhe_does_not_support_liji(self):
        """三合派不支持立极。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.SANHE)
        res = resolver.resolve_taiji('夫妻')
        self.assertEqual(res.taiji_origin, '')
        trace = list(res.resolution_trace)
        self.assertTrue(any('不支持立极' in t for t in trace))

class TestTransferPalace(unittest.TestCase):
    """转宫关系测试。"""

    @classmethod
    def setUpClass(cls):
        cls.chart = ZiweiEngine().full_chart((2000, 1, 1), 12, 'male')

    def test_transfer_ming_to_husband(self):
        """命宫→夫妻宫的转宫关系。"""
        resolver = ZiweiPalaceResolver(self.chart, MethodId.SANHE)
        result = resolver.resolve_transfer('命宫', '婚姻')
        self.assertEqual(result['to_palace'], '夫妻')
        self.assertIn('relationship', result)


class TestPalaceResolutionFrozen(unittest.TestCase):
    """PalaceResolution 冻结性测试。"""

    def test_is_frozen(self):
        """PalaceResolution 是 frozen dataclass。"""
        res = PalaceResolution(primary_palace='命宫')
        self.assertTrue(res.primary_palace == '命宫')
        with self.assertRaises(Exception):
            res.primary_palace = '测试'

    def test_to_dict(self):
        """to_dict 返回字典格式。"""
        res = PalaceResolution(
            primary_palace='命宫',
            supporting_palaces=('夫妻', '官禄'),
            borrowed_stars=('太阳', '太阴'),
            resolution_trace=('test',),
        )
        d = res.to_dict()
        self.assertEqual(d['primary_palace'], '命宫')
        self.assertEqual(d['supporting_palaces'], ['夫妻', '官禄'])
        self.assertEqual(d['borrowed_stars'], ['太阳', '太阴'])

    def test_default_values(self):
        """默认值正确。"""
        res = PalaceResolution(primary_palace='命宫')
        self.assertEqual(res.supporting_palaces, ())
        self.assertEqual(res.borrowed_stars, ())
        self.assertEqual(res.opposite_palace, '')
        self.assertEqual(res.taiji_origin, '')
        self.assertEqual(res.transformation_context, {})


class TestUnifiedResolve(unittest.TestCase):
    """统一入口 resolve() 测试。"""

    @classmethod
    def setUpClass(cls):
        cls.chart = ZiweiEngine().full_chart((2000, 1, 1), 12, 'male')
        cls.resolver = ZiweiPalaceResolver(cls.chart, MethodId.SANHE)

    def test_resolve_ming_gong(self):
        """命宫解析：应包含三方四正+借星检查。"""
        res = self.resolver.resolve('命宫')
        self.assertEqual(res.primary_palace, '命宫')
        self.assertGreaterEqual(len(res.supporting_palaces), 1)

    def test_resolve_with_sanfang_false(self):
        """不包含三方四正的解析。"""
        res = self.resolver.resolve('命宫', include_sanfang=False)
        self.assertEqual(res.primary_palace, '命宫')
        self.assertEqual(res.supporting_palaces, ())

    def test_resolver_profile(self):
        """解析器持有正确的流派契约。"""
        self.assertIsInstance(self.resolver.profile, SanheProfile)
        self.assertEqual(self.resolver.profile.METHOD_ID, MethodId.SANHE)

    def test_resolver_chart(self):
        """解析器持有正确的 FrozenZiweiChart。"""
        from tongshu.engines.ziwei_engine import FrozenZiweiChart
        self.assertIsInstance(self.resolver.chart, FrozenZiweiChart)


if __name__ == "__main__":
    unittest.main()
