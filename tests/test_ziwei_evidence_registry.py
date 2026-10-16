# -*- coding: utf-8 -*-
"""紫微证据引用注册表 + 解层证据回查 单元测试（Z80-H）。

覆盖：
  - ZW-* 注册表覆盖度（模板可生成全集 == 已登记全集）
  - 4 族（SIHUA/STAR/PATTERN/PALACE）回查命中与未命中 fail-closed
  - 解层加载器 SANHE 四化/宫位/星曜证据可解析（消除悬空）
  - 解层加载器 resolve_zw_ref 回查
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei.rules.evidence_registry import (
    ZWEvidenceRecord,
    resolve_zw_evidence_ref,
    registry_ids,
    template_generated_ids,
    completeness_report,
)
from tongshu.engines.ziwei.rules.interpretation import ZiweiEvidenceLoader


class TestZWEvidenceRegistry(unittest.TestCase):
    """ZW-* 证据注册表."""

    def test_completeness(self):
        """模板可生成的全部 ZW-* ref_id 均已在册（无缺失/多余）。"""
        rep = completeness_report()
        self.assertEqual(rep["missing"], [], f"missing: {rep['missing']}")
        self.assertEqual(rep["extra"], [], f"extra: {rep['extra']}")
        self.assertTrue(rep["complete"])

    def test_four_families_present(self):
        """4 族均已登记：SIHUA(10) / STAR(14) / PATTERN(38) / PALACE(12)。"""
        fams = {}
        for rid in registry_ids():
            rec = resolve_zw_evidence_ref(rid)
            fams[rec.family] = fams.get(rec.family, 0) + 1
        self.assertEqual(fams.get("SIHUA"), 10)
        self.assertEqual(fams.get("STAR"), 14)
        self.assertEqual(fams.get("PATTERN"), 38)
        self.assertEqual(fams.get("PALACE"), 12)

    def test_resolve_hit_and_miss(self):
        """已登记命中、未登记 fail-closed 返回 None。"""
        self.assertIsInstance(resolve_zw_evidence_ref("ZW-STAR-紫微"), ZWEvidenceRecord)
        self.assertIsInstance(resolve_zw_evidence_ref("ZW-SIHUA-甲"), ZWEvidenceRecord)
        self.assertIsInstance(resolve_zw_evidence_ref("ZW-PATTERN-紫微独坐"), ZWEvidenceRecord)
        self.assertIsInstance(resolve_zw_evidence_ref("ZW-PALACE-命宫"), ZWEvidenceRecord)
        self.assertIsNone(resolve_zw_evidence_ref("ZW-UNKNOWN-xxx"))

    def test_template_and_registry_agree(self):
        """模板全集与注册表全集一致。"""
        self.assertEqual(template_generated_ids(), registry_ids())


class TestEvidenceLoaderSanheFamilies(unittest.TestCase):
    """解层加载器：SANHE 四化/宫位/星曜证据可解析（Z80-H 消除悬空）。"""

    def setUp(self):
        self.loader = ZiweiEvidenceLoader()

    def test_pattern_still_resolves(self):
        ref = self.loader.get_evidence_ref("SANHE", "SANHE-PATTERN-杀破狼")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.classic, "紫微斗数全书")

    def test_sihua_resolves(self):
        ref = self.loader.get_evidence_ref("SANHE", "SANHE-SIHUA-甲")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.source, "四化篇")

    def test_sihua_variant_resolves(self):
        ref = self.loader.get_evidence_ref("SANHE", "SANHE-SIHUA-癸-化忌")
        self.assertIsNotNone(ref)
        self.assertIn("贪狼", ref.text_preview)

    def test_palace_resolves(self):
        ref = self.loader.get_evidence_ref("SANHE", "SANHE-PALACE-命宫")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.source, "十二宫")

    def test_star_judgment_resolves(self):
        ref = self.loader.get_evidence_ref("SANHE", "SANHE-JUDG-紫微")
        self.assertIsNotNone(ref)
        self.assertIn("紫微", ref.source)

    def test_resolve_zw_ref(self):
        ref = self.loader.resolve_zw_ref("ZW-STAR-紫微")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.classic, "紫微斗数全书")
        self.assertIsNone(self.loader.resolve_zw_ref("ZW-NOPE-1"))


if __name__ == "__main__":
    unittest.main()
