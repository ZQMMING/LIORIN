"""B-01: 河洛/易经结果从 ComputeStage 透传至 PipelineResult 和 API 响应。

验证：
- PipelineResult 携带 heluo_result / yi_structure / yi_interpretation。
- yi 块序列化正确（heluo asdict / yi_structure.to_dict / yi_interpretation.to_dict）。
- None 时省略键而非输出 null。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Ziwei stub fallback for environments without iztro (must be set before engine init)
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

import dataclasses
import unittest
from datetime import date

from tongshu.pipeline import TONGSHUPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]  # .
if not (_REPO_ROOT / "backend" / "data").is_dir():
    _REPO_ROOT = Path(__file__).resolve().parents[1]


def _serialize_yi_block(result) -> dict | None:
    """Mirror of api.app._yi_block logic for test verification."""
    block: dict = {}
    if result.heluo_result is not None:
        block["heluo"] = dataclasses.asdict(result.heluo_result)
    if result.yi_structure is not None:
        block["yi_structure"] = result.yi_structure.to_dict()
    if result.yi_interpretation is not None:
        block["yi_interpretation"] = result.yi_interpretation.to_dict()
    return block or None


class TestPipelineResultCarriesHeluoYi(unittest.TestCase):
    """PipelineResult 必须携带 ComputeStage 产出的 heluo/yi 三字段。"""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)

    def test_compute_only_carries_heluo_yi(self):
        result = self.pipeline.run(
            analysis_date=date(2026, 8, 17),
            birth_date=(1984, 12, 7, 16),
            gender="male",
            theme="WORK",
            compute_only=True,
        )
        self.assertIsNotNone(result.heluo_result)
        self.assertIsNotNone(result.yi_structure)
        self.assertIsNotNone(result.yi_interpretation)
        self.assertTrue(result.heluo_result.prenatal.hexagram_name)
        self.assertTrue(result.yi_structure.truth_hexagram)
        self.assertTrue(result.yi_interpretation.state)
        self.assertEqual(result.yi_interpretation.phase, 6)

    def test_yi_block_serialization(self):
        """yi 块可正确序列化为 JSON-safe dict。"""
        result = self.pipeline.run(
            analysis_date=date(2026, 8, 17),
            birth_date=(1984, 12, 7, 16),
            gender="male",
            theme="WORK",
            compute_only=True,
        )
        block = _serialize_yi_block(result)
        self.assertIsNotNone(block)
        self.assertIn("heluo", block)
        self.assertIn("yi_structure", block)
        self.assertIn("yi_interpretation", block)
        self.assertTrue(block["yi_structure"]["truth_hexagram"])
        self.assertTrue(block["yi_interpretation"]["state"])
        # Verify JSON-serializable (no nested dataclasses/enums leaked)
        import json
        json.dumps(block)

    def test_yi_block_none_when_all_none(self):
        """全 None 时返回 None（省略键而非输出 null）。"""
        class FakeResult:
            heluo_result = None
            yi_structure = None
            yi_interpretation = None
        self.assertIsNone(_serialize_yi_block(FakeResult()))


if __name__ == "__main__":
    unittest.main()
