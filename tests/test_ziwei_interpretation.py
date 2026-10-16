# -*- coding: utf-8 -*-
"""Ziwei 解层 (interpretation.py) 单元测试 (Z17 两派收敛)."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ['TONGSHU_ALLOW_ZIWEI_STUB'] = '1'

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.multi_method import (
    MultiMethodSignal, MethodBundle, MethodMatch,
    compute_multi_method_signals,
)
from tongshu.engines.ziwei.rules.interpretation import (
    ZiweiInterpretationOutput,
    ZiweiInterpretation,
    EvidenceRef,
    ZiweiEvidenceLoader,
    ZiweiInterpretationResolver,
    interpret_signal,
)


class TestZiweiEvidenceLoader(unittest.TestCase):
    """证据加载器单元测试."""

    def test_load_sanhe_evidence(self):
        """南派（三合）证据可加载."""
        loader = ZiweiEvidenceLoader()
        ref = loader.get_evidence_ref("SANHE", "SANHE-PATTERN-杀破狼")
        self.assertIsNotNone(ref)
        self.assertEqual(ref.classic, "紫微斗数全书")
        self.assertTrue(len(ref.text_preview) > 0)

    def test_load_qintian_evidence(self):
        """钦天门证据可加载."""
        loader = ZiweiEvidenceLoader()
        ref = loader.get_evidence_ref("QINTIAN", "QTN-CMB-001")
        self.assertIsNotNone(ref)
        self.assertIn("来因宫", ref.text_preview)

    def test_unknown_rule_returns_none(self):
        """未知规则返回 None."""
        loader = ZiweiEvidenceLoader()
        ref = loader.get_evidence_ref("SANHE", "NONEXISTENT")
        self.assertIsNone(ref)

    def test_unknown_method_returns_none(self):
        """未知方法返回 None."""
        loader = ZiweiEvidenceLoader()
        ref = loader.get_evidence_ref("UNKNOWN", "SOME-RULE")
        self.assertIsNone(ref)


class TestZiweiInterpretationResolver(unittest.TestCase):
    """解层解析器单元测试."""

    def _make_chart(self):
        engine = ZiweiEngine()
        return engine.full_chart((2000, 1, 1), 12, 'male')

    def test_resolve_produces_output(self):
        """解层可正常产出输出."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        resolver = ZiweiInterpretationResolver()
        output = resolver.resolve(signal)
        self.assertIsInstance(output, ZiweiInterpretationOutput)

    def test_sanhe_interpretations_have_classical_conclusion(self):
        """南派解读结论为古典中文."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        output = interpret_signal(signal)
        for interp in output.sanhe:
            self.assertTrue(len(interp.conclusion) > 0)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in interp.conclusion)
            self.assertTrue(has_chinese,
                f"结论应含中文: {interp.conclusion[:50]}")

    def test_qintian_interpretations_have_classical_conclusion(self):
        """北派解读结论为古典中文."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        output = interpret_signal(signal)
        for interp in output.qintian:
            self.assertTrue(len(interp.conclusion) > 0)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in interp.conclusion)
            self.assertTrue(has_chinese,
                f"结论应含中文: {interp.conclusion[:50]}")

    def test_all_interpretations_have_evidence_ref_or_undetermined(self):
        """所有解读要么有 evidence_ref，要么 quality=UNCLEAR."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        output = interpret_signal(signal)
        for interp in output.sanhe + output.qintian:
            if interp.evidence_ref is None:
                self.assertEqual(interp.quality, "UNCLEAR")
            else:
                self.assertEqual(interp.quality, "PRINCIPLE")

    def test_evidence_ref_structure(self):
        """EvidenceRef 包含必要字段."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        output = interpret_signal(signal)
        for interp in output.sanhe[:1] + output.qintian[:1]:
            ref = interp.evidence_ref
            self.assertIsNotNone(ref)
            self.assertTrue(len(ref.classic) > 0)
            self.assertTrue(len(ref.source) > 0)
            self.assertTrue(len(ref.text_preview) > 0)
            self.assertLessEqual(len(ref.text_preview), 60)

    def test_to_dict_serializable(self):
        """to_dict 输出可序列化."""
        chart = self._make_chart()
        signal = compute_multi_method_signals(chart)
        output = interpret_signal(signal)
        d = output.to_dict()
        self.assertIn("sanhe", d)
        self.assertIn("qintian", d)
        self.assertIn("undetermined_rules", d)
        self.assertIn("total_matched", d)
        self.assertEqual(d["total_matched"],
            len(d["sanhe"]) + len(d["qintian"]))

    def test_different_charts_different_interpretations(self):
        """不同命盘解层输出结构正确（至少非空）."""
        engine = ZiweiEngine()
        chart1 = engine.full_chart((2000, 1, 1), 12, 'male')
        chart2 = engine.full_chart((1990, 5, 15), 10, 'female')
        signal1 = compute_multi_method_signals(chart1)
        signal2 = compute_multi_method_signals(chart2)
        output1 = interpret_signal(signal1)
        output2 = interpret_signal(signal2)
        # 两个命盘都必须产出非空解读
        self.assertGreater(output1.total_matched, 0)
        self.assertGreater(output2.total_matched, 0)
        # to_dict 可序列化
        d1 = output1.to_dict()
        d2 = output2.to_dict()
        self.assertIn("sanhe", d1)
        self.assertIn("qintian", d1)


class TestZiweiInterpretationDataModel(unittest.TestCase):
    """解层数据模型单元测试."""

    def test_evidence_ref_to_dict(self):
        ref = EvidenceRef(classic="紫微斗数全书", source="格局篇", text_preview="杀破狼格")
        d = ref.to_dict()
        self.assertEqual(d["classic"], "紫微斗数全书")
        self.assertEqual(d["source"], "格局篇")
        self.assertEqual(d["text_preview"], "杀破狼格")

    def test_ziwei_interpretation_frozen(self):
        interp = ZiweiInterpretation(
            rule_id="SANHE-PATTERN-杀破狼",
            method_id="SANHE",
            strength="moderate",
            direction="neutral",
            conclusion="杀破狼格：大起大落",
            evidence_ref=EvidenceRef("紫微斗数全书", "格局篇", "杀破狼格"),
            quality="PRINCIPLE",
        )
        self.assertEqual(interp.rule_id, "SANHE-PATTERN-杀破狼")
        # frozen dataclass 不可修改
        with self.assertRaises(Exception):
            interp.rule_id = "foo"  # type: ignore[misc]

    def test_ziwei_interpretation_to_dict(self):
        interp = ZiweiInterpretation(
            rule_id="QTN-CMB-001",
            method_id="QINTIAN",
            strength="strong",
            direction="auspicious",
            conclusion="来因宫落疾厄",
            evidence_ref=None,
            quality="UNCLEAR",
        )
        d = interp.to_dict()
        self.assertEqual(d["rule_id"], "QTN-CMB-001")
        self.assertIsNone(d["evidence_ref"])
        self.assertEqual(d["quality"], "UNCLEAR")

    def test_output_empty_default(self):
        output = ZiweiInterpretationOutput()
        self.assertEqual(output.total_matched, 0)
        self.assertEqual(output.total_undetermined, 0)
        self.assertEqual(len(output.sanhe), 0)
        self.assertEqual(len(output.qintian), 0)


if __name__ == '__main__':
    unittest.main()
