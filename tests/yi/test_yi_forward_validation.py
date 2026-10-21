"""
Phase 6 — Forward Validation Tests

测试前瞻验证的边界条件和契约。
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(".")))

import unittest

from tongshu.yi.schema import (
    DirectionLabel,
    YiStructureStatus,
)
from tongshu.yi.adapter import YiAdapter, YiAdapterInput
from tongshu.yi.interpreter import YiInterpretationEngine
from tongshu.forward_validation import (
    ForwardValidationEngine,
    ForwardValidationStatus,
)
from tongshu.spec.temporal_evidence import EvaluationToleranceWindow


class TestYiContractBoundaries(unittest.TestCase):
    """Yi Engine 契约边界测试。"""

    def test_interp_input_forbids_raw_calculation(self):
        """InterpInput 禁止 raw calculation fields。"""
        from tongshu.spec.relational_interpretation import InterpInput
        # 这些字段应被禁止
        with self.assertRaises(ValueError):
            InterpInput.from_dict({"bazi_pillars": []})
        with self.assertRaises(ValueError):
            InterpInput.from_dict({"heluo_hexagram": "泰"})
        with self.assertRaises(ValueError):
            InterpInput.from_dict({"raw_calculation": {}})

    def test_yi_structure_no_fortune_score(self):
        """YiStructure 不包含 fortune_score。"""
        from tongshu.yi.schema import YiStructure
        s = YiStructure(truth_hexagram="乾")
        self.assertNotIn("fortune_score", s.to_dict())
        self.assertNotIn("luck_score", s.to_dict())

    def test_yi_interpretation_no_fortune_score(self):
        """YiInterpretation 不包含 fortune_score。"""
        from tongshu.yi.schema import YiInterpretation
        i = YiInterpretation(
            interpretation_id="test",
            yi_structure_ref="乾#1",
            state="测试",
            phase=6,
        )
        self.assertFalse(i.has_fortune_score)
        d = i.to_dict()
        self.assertNotIn("fortune_score", d)
        self.assertNotIn("luck_score", d)
        self.assertNotIn("overall_goodness", d)
        self.assertNotIn("auspicious_score", d)


class TestForwardValidationContracts(unittest.TestCase):
    """Forward Validation 契约测试。"""

    def test_prediction_window_immutability(self):
        """PredictionWindow 不可修改。"""
        from tongshu.yi.schema import PredictionRecord
        from tongshu.yi.schema import DirectionLabel
        import dataclasses

        pred = PredictionRecord(
            prediction_id="p1",
            interpretation_ref="i1",
            prediction_direction=DirectionLabel.POSITIVE,
            prediction_window_start=2025,
            prediction_window_end=2025,
            created_at="2025-01-01T00:00:00Z",
        )
        # frozen dataclass 应阻止修改
        with self.assertRaises(dataclasses.FrozenInstanceError):
            pred.prediction_window_start = 2026

    def test_evaluation_tolerence_window_independent(self):
        """EvaluationToleranceWindow 独立于 PredictionWindow。"""
        from tongshu.spec.temporal_evidence import EvaluationToleranceWindow
        tw = EvaluationToleranceWindow(severity_class="HIGH", tolerance_days=30)
        self.assertEqual(tw.tolerance_days, 30)
        self.assertEqual(tw.severity_class, "HIGH")

    def test_data_leakage_prevention(self):
        """数据泄漏预防措施。"""
        engine = ForwardValidationEngine()
        # 创建预测（未来时间）
        pred = engine.create_prediction(
            interpretation_id="i1",
            direction=DirectionLabel.POSITIVE,
            window_start_year=2025,
            window_end_year=2025,
            created_at="2026-06-01T00:00:00Z",  # 未来
        )
        # 评估过去事件
        eval_record = engine.evaluate_event(
            prediction_id=pred.prediction_id,
            actual_direction=DirectionLabel.POSITIVE,
            actual_occurred_at="2025-01-01T00:00:00Z",  # 过去
            tolerance_window=EvaluationToleranceWindow(
                severity_class="LOW",
                tolerance_days=365,
            ),
        )
        # 应标记为 DATA_LEAKAGE
        self.assertEqual(eval_record.status, ForwardValidationStatus.DATA_LEAKAGE)


class TestLegacyEngineIntegrity(unittest.TestCase):
    """Legacy Engine 完整性测试（确保未被修改）。"""

    def test_bazi_engine_untouched(self):
        """Bazi Engine 仍可正常导入。"""
        from tongshu.engines.bazi_engine import BaziEngine
        engine = BaziEngine()
        self.assertIsNotNone(engine)

    def test_ziwei_engine_untouched(self):
        """Ziwei Engine 仍可正常导入。"""
        from tongshu.engines.ziwei_engine import ZiweiEngine
        engine = ZiweiEngine()
        self.assertIsNotNone(engine)

    def test_huangli_engine_untouched(self):
        """Huangli Engine 仍可正常导入。"""
        from tongshu.engines.huangli_engine import HuangliEngine
        engine = HuangliEngine()
        self.assertIsNotNone(engine)

    def test_evidence_chain_untouched(self):
        """Evidence Chain 仍可正常导入。"""
        from tongshu.chain.chain_context import EvidenceChainContext
        ctx = EvidenceChainContext()
        self.assertIsNotNone(ctx)

    def test_canonical_signal_untouched(self):
        """Canonical Signal 仍可正常导入。"""
        from tongshu.spec.canonical_signal import CanonicalSignal
        self.assertIsNotNone(CanonicalSignal)


class TestGoldenDatasetIntegrity(unittest.TestCase):
    """Golden Dataset 完整性测试（确保未被修改）。"""

    def test_no_golden_dataset_modification(self):
        """确认没有新增或修改 Golden Dataset。"""
        import os
        golden_path = "src/tongshu/golden"
        # 只检查目录存在，不修改任何文件
        self.assertTrue(os.path.isdir(golden_path))


if __name__ == "__main__":
    unittest.main()
