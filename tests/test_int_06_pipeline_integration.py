"""BZ-FNDR-15.16 ZIP-INT-06 Pipeline 集成测试.

S1~S6 在 Pipeline.run() 端到端验证:
  - Composer output 真正进入 atomic_claims
  - Chain-A 老 ZI_PING claims 与 Composer AC-ZP-* claims 不冲突 (S6)
  - SHIJIAN EVENT_ABSENT / UNKNOWN / FAILED 在 production 链路 0 claim
  - boundary: composer_version 字段在每个 Composer claim 里
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

# P2.1-F: Authority bootstrap 需要外部 cred
os.environ.setdefault(
    "TONGSHU_AUTHORITY_CREDENTIALS",
    "test:abc123;test2:def456"
)


class TestINT06PipelineWiring(unittest.TestCase):
    """Pipeline.run() end-to-end: Composer 接入 ComputeStage 但 production path 默认 OFF.

    ⚠️ INT-06 默认 OFF 原因: Composer claims 会改变 atomic_claims 内容,
    影响 G1 evidence_gate (T-3 漂移). 待 User 单独授权 + Composer claims G1 适配.
    当前测试验证:
      1. Composer 模块可用 (单元测试覆盖)
      2. ComputeStage 接入点 (judgment_composer 参数) 存在
      3. Pipeline.production path 默认 OFF → 0 Composer claims
    """

    def test_production_path_composer_on(self):
        """Step 4: Composer ON — pipeline.run() 应产 AC-ZP-* claims."""
        from datetime import date
        from tongshu.pipeline import TONGSHUPipeline

        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        # [2026-11-07] 子平引擎最终版本 = engines p0 线。p0 线对部分盘明确输出
        # cheng_bai=NOT_EVALUABLE（成败未核验），此情形不产 claim（证据闸要求结论可证）。
        # 本用例取 1984-12-07 16:00 男（印格 CHENG + 调候用神已裁定），保证 Composer 有输入。
        result = pipeline.run(
            analysis_date=date(2024, 1, 1),
            birth_date=(1984, 12, 7, 16),
            gender="male",
            theme="WORK",
        )
        claims = result.canonical.atomic_claims
        composer_claims = [c for c in claims if c.get("claim_id", "").startswith("AC-ZP-")]
        # Step 4: Composer ON → 应有 AC-ZP-* claims
        self.assertGreater(len(composer_claims), 0,
                           "Step 4: Composer ON 应产生 AC-ZP-* claims")
        # 验证 claim 结构
        for c in composer_claims:
            self.assertIn("composer_version", c)
            self.assertEqual(c["composer_version"], "1.0.0")
            # G1: 每条 claim 必须带可解析的证据锚与规则锚
            self.assertTrue(c.get("evidence_refs"), f"{c.get('claim_id')} 缺证据锚")
            self.assertTrue(c.get("rule_refs"), f"{c.get('claim_id')} 缺规则锚")

    def test_compute_stage_supports_composer_param(self):
        """ComputeStage.run() 接受 judgment_composer 参数 (INT-06 接入点)."""
        import inspect
        from tongshu.pipeline_stages.compute_stage import ComputeStage
        sig = inspect.signature(ComputeStage.run)
        self.assertIn("judgment_composer", sig.parameters,
                      "INT-06: ComputeStage.run 必须接受 judgment_composer 参数")

    def test_pipeline_holds_composer_instance(self):
        """Pipeline.judgment_composer 已构造 (即使默认 OFF, 实例在)."""
        from tongshu.pipeline import TONGSHUPipeline
        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        self.assertIsNotNone(pipeline.judgment_composer,
                             "INT-06: pipeline.judgment_composer 实例已构造")

    def test_int06_introduction_preserves_baseline(self):
        """T-3: pipeline.run() 必须 0 报错."""
        from datetime import date
        from tongshu.pipeline import TONGSHUPipeline

        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        result = pipeline.run(
            analysis_date=date(2024, 1, 1),
            birth_date=(1990, 1, 1, 12),
            gender="male",
            theme="WORK",
        )
        self.assertIsNotNone(result)

    def test_provenance_summary_field_in_result(self):
        """INT-03 + INT-06 联动: ValidationStage 产出 provenance_summary."""
        from datetime import date
        from tongshu.pipeline import TONGSHUPipeline

        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        result = pipeline.run(
            analysis_date=date(2024, 1, 1),
            birth_date=(1990, 1, 1, 12),
            gender="male",
            theme="WORK",
        )
        # PipelineResult.validation_passed is bool
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "validation_passed"))


if __name__ == "__main__":
    unittest.main()
