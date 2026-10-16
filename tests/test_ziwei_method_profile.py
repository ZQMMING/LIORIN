# -*- coding: utf-8 -*-
"""ZiweiMethodProfile 测试（Z10 / Z17 两派收敛）。

覆盖：
- MethodId / RuleType / ConfidenceLevel 枚举值
- EvidenceRef / RuleSpec 数据结构
- 四化表（经典表，南派/北派共用）
- 两派特征（自化/立极/空宫/小限）
- 流派注册表（get_profile / list_available_methods）
- 抽象基类不可直接实例化
- sihua_differs 检测
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.ziwei_method_profile import (
    MethodId,
    RuleType,
    ConfidenceLevel,
    EvidenceRef,
    RuleSpec,
    ZiweiMethodProfile,
    SanheProfile,
    QintianProfile,
    get_profile,
    list_available_methods,
    sihua_differs,
    SIHUA_TABLE_CLASSIC,
)


class TestEnumValues(unittest.TestCase):
    """枚举值完整性测试。"""

    def test_method_id_values(self):
        """两派全部定义（Z17 收敛）。"""
        ids = [m.value for m in MethodId]
        self.assertIn("sanhe", ids)
        self.assertIn("qintian", ids)
        self.assertEqual(len(ids), 2)

    def test_method_id_labels_zh(self):
        """每个 MethodId 有中文字符标签。"""
        for mid in MethodId:
            self.assertTrue(isinstance(mid.label_zh, str))
            self.assertNotEqual(mid.label_zh, "")

    def test_rule_type_values(self):
        """五种规则类型全部定义。"""
        types = [t.value for t in RuleType]
        expected = {"pattern", "sihua", "palace", "interaction", "cycle"}
        self.assertEqual(set(types), expected)

    def test_confidence_level_values(self):
        """四种置信度全部定义。"""
        levels = [l.value for l in ConfidenceLevel]
        expected = {"high", "medium", "low", "unknown"}
        self.assertEqual(set(levels), expected)


class TestDataStructures(unittest.TestCase):
    """数据结构测试。"""

    def test_evidence_ref_creation(self):
        """EvidenceRef 可正确创建。"""
        ref = EvidenceRef(
            rule_id="ZW-TEST-001",
            source_work="紫微斗数全书",
            source_chapter="紫微星",
            verification_status="canonical",
        )
        self.assertEqual(ref.rule_id, "ZW-TEST-001")
        self.assertEqual(ref.verification_status, "canonical")

    def test_rule_spec_creation(self):
        """RuleSpec 可正确创建。"""
        spec = RuleSpec(
            rule_id="SANHE-PATTERN-001",
            method_id=MethodId.SANHE,
            rule_type=RuleType.PATTERN,
            condition={"star_combo": ["武曲", "贪狼"]},
            operation={"action": "recognize"},
            confidence=ConfidenceLevel.MEDIUM,
        )
        self.assertEqual(spec.method_id, MethodId.SANHE)
        self.assertTrue(spec.matches({"star_combo": ["武曲", "贪狼"]}))
        self.assertFalse(spec.matches({"star_combo": ["紫微", "天府"]}))


class TestSiHuaTables(unittest.TestCase):
    """四化表测试（经典通行本，两派共用）。"""

    def test_classic_wu_stem_ke(self):
        """戊干科星=右弼（通行本）。"""
        _, _, ke, _ = SIHUA_TABLE_CLASSIC["戊"]
        self.assertEqual(ke, "右弼")

    def test_classic_ten_stems_complete(self):
        """十天干四化表完整。"""
        self.assertEqual(len(SIHUA_TABLE_CLASSIC), 10)
        for stem in "甲乙丙丁戊己庚辛壬癸":
            self.assertIn(stem, SIHUA_TABLE_CLASSIC)


class TestProfileFeatures(unittest.TestCase):
    """两派特征对比测试。"""

    def _profiles(self):
        return {
            MethodId.SANHE: SanheProfile(),
            MethodId.QINTIAN: QintianProfile(),
        }

    def test_sihua_table_assignment(self):
        """两派使用经典四化表。"""
        p = self._profiles()
        self.assertEqual(p[MethodId.SANHE].SIHUA_TABLE, SIHUA_TABLE_CLASSIC)
        self.assertEqual(p[MethodId.QINTIAN].SIHUA_TABLE, SIHUA_TABLE_CLASSIC)

    def test_self_mutagen_feature(self):
        """南派（三合）不支持自化；北派（钦天）支持。"""
        p = self._profiles()
        self.assertFalse(p[MethodId.SANHE].supports_self_mutagen())
        self.assertTrue(p[MethodId.QINTIAN].supports_self_mutagen())

    def test_liji_feature(self):
        """仅北派（钦天）支持立极宫。"""
        p = self._profiles()
        self.assertFalse(p[MethodId.SANHE].supports_liji())
        self.assertTrue(p[MethodId.QINTIAN].supports_liji())

    def test_xiao_xian_feature(self):
        """南派（三合）支持小限；北派（钦天）部分支持。"""
        p = self._profiles()
        self.assertTrue(p[MethodId.SANHE].supports_xiao_xian())
        self.assertTrue(p[MethodId.QINTIAN].supports_xiao_xian())

    def test_empty_palace_policy(self):
        """两派空宫策略均为 partial。"""
        p = self._profiles()
        self.assertEqual(p[MethodId.SANHE].get_empty_palace_policy(), "partial")
        self.assertEqual(p[MethodId.QINTIAN].get_empty_palace_policy(), "partial")


class TestRegistry(unittest.TestCase):
    """流派注册表测试。"""

    def test_get_profile(self):
        """get_profile 返回正确类型的实例。"""
        for mid in MethodId:
            profile = get_profile(mid)
            self.assertIsInstance(profile, ZiweiMethodProfile)
            self.assertEqual(profile.METHOD_ID, mid)

    def test_list_available_methods(self):
        """list_available_methods 返回两派的描述。"""
        methods = list_available_methods()
        self.assertEqual(len(methods), 2)
        ids = {m["method_id"] for m in methods}
        self.assertEqual(ids, {"sanhe", "qintian"})

    def test_unknown_method_raises(self):
        """未知 MethodId 抛出 ValueError。"""
        import enum
        fake_id = enum.Enum("FakeMethod", {"FAKE": "fake"})
        with self.assertRaises(ValueError):
            get_profile(fake_id("fake"))


class TestAbstractBase(unittest.TestCase):
    """抽象基类测试。"""

    def test_cannot_instantiate_base(self):
        """ZiweiMethodProfile 不能直接实例化。"""
        with self.assertRaises(TypeError):
            ZiweiMethodProfile()


class TestSihuaDiffers(unittest.TestCase):
    """sihua_differs 函数测试。"""

    def test_same_method_no_diff(self):
        """同一派别无差异。"""
        self.assertFalse(sihua_differs(MethodId.SANHE, MethodId.SANHE))

    def test_sanhe_vs_qintian_no_diff(self):
        """两派共用经典四化表，无差异。"""
        self.assertFalse(sihua_differs(MethodId.SANHE, MethodId.QINTIAN))


if __name__ == "__main__":
    unittest.main()
