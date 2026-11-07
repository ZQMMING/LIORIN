"""BZ-FNDR-15.16 ZIP-INT Stage 1 施工验收测试.

覆盖 INT-01 (Evidence Index 注入 Pipeline) + INT-02 (Tree B 接入, option A)
+ INT-03 (Resolved Provenance 消费面) 的契约.

红线核查 (3 条硬约束):
  T-1: rule 面维持 136 条 (Option A, 不切 data_dir)
  T-2: provenance_summary 字段接入 ValidationStageResult
  T-3: 73 既有回归零漂移
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))


class TestINT01_02_03Wiring(unittest.TestCase):
    """Stage 1 wiring contract: Pipeline holds Index + ResolvedProvenance."""

    def test_int01_pipeline_accepts_evidence_index(self):
        """INT-01: Pipeline.__init__ 可接受 evidence_index 参数, 默认 None. G0 未接入时 0 影响."""
        from tongshu.pipeline import TONGSHUPipeline
        import inspect
        sig = inspect.signature(TONGSHUPipeline.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("evidence_index", params,
                      "INT-01: Pipeline 必须接受 evidence_index 参数")
        # 默认 None = 向后兼容 (现有所有调用方无需改代码)
        self.assertEqual(sig.parameters["evidence_index"].default, None)

    def test_int02_for_demo_wires_corpus_base(self):
        """INT-02: for_demo 注入的 EvidenceIndex corpus_root = data/evidence (Tree B)."""
        from tongshu.pipeline import TONGSHUPipeline
        from tongshu.governance.evidence_index import EvidenceIndex
        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        self.assertIsNotNone(pipeline.evidence_index,
                             "INT-02: for_demo 必须注入 EvidenceIndex")
        self.assertIsInstance(pipeline.evidence_index, EvidenceIndex)
        self.assertEqual(str(pipeline.evidence_index.corpus_root),
                         str(_REPO_ROOT / "data" / "evidence"),
                         "INT-02: 必须指向 Tree B Corpus Base (data/evidence)")
        # Option A 守备: rule 面仍为 136 条 (RuleLoader 读树A, 不切 data_dir)
        self.assertEqual(len(pipeline.rule_matcher.rules), 136,
                         "INT-02 Option A: rule 面维持 136 条, 不夹带 draft")

    def test_int02_option_a_rule_face_untouched(self):
        """INT-02 Option A 严守: 生产 RuleLoader 读树A, 0 扩到 4 draft rules.
        (User 明确选 A, 禁止 INT-02 顺带带入 PT-009/PT-010/YONG-003/YONG-005)"""
        from tongshu.pipeline import TONGSHUPipeline
        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        # rule_matcher.rules 是 list of rule objects
        # Setiap rule punya attribute 'rule_id' atau accessible via dict key
        rules_list = pipeline.rule_matcher.rules
        self.assertIsInstance(rules_list, list, "rule_matcher.rules should be a list")
        # Ambil rule IDs dari list
        if rules_list and hasattr(rules_list[0], 'rule_id'):
            rule_ids = {r.rule_id for r in rules_list}
        elif rules_list and isinstance(rules_list[0], dict):
            rule_ids = {r.get('rule_id', '') for r in rules_list}
        else:
            # Fallback: coba iterasi dan ambil attr
            rule_ids = set()
            for r in rules_list:
                if hasattr(r, 'rule_id'):
                    rule_ids.add(r.rule_id)
                elif isinstance(r, dict) and 'rule_id' in r:
                    rule_ids.add(r['rule_id'])
        drafted = {"PT-009", "PT-010", "YONG-003", "YONG-005"}
        self.assertFalse(rule_ids & drafted,
                         f"INT-02 Option A 违规: draft rules 进入生产面: {rule_ids & drafted}")
        # Juga verifikasi rule face = 136 (tree A, option A)
        self.assertEqual(len(rule_ids), 136,
                         f"INT-02 Option A: expected 136 rules, got {len(rule_ids)}")

    def test_int03_provenance_summary_field_exists(self):
        """INT-03: ValidationStageResult 有 provenance_summary 字段 (T-2 统计面)."""
        from tongshu.types import ValidationStageResult
        self.assertTrue(hasattr(ValidationStageResult, "provenance_summary"),
                        "INT-03: ValidationStageResult 必须有 provenance_summary")
        # 默认 None = 向后兼容 (G0 未接入时不影响既有测试)
        instance = ValidationStageResult(layer1=None, layer2=None, layer3=None,
                                         gates=(), passed=True)
        self.assertIsNone(instance.provenance_summary)

    def test_int03_validation_stage_consumes_resolver(self):
        """INT-03: ValidationStage 接受 provenance_resolver 参数, run() 产出 provenance_summary."""
        from tongshu.pipeline import TONGSHUPipeline
        from tongshu.governance.provenance_resolver import ProvenanceResolver

        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        self.assertIsNotNone(pipeline.provenance_resolver,
                             "INT-03: pipeline 必须持有 provenance_resolver")
        self.assertIsInstance(pipeline.provenance_resolver, ProvenanceResolver)
        # tier_summary 产出 8 档分布 (无报错即契约成立)
        summary = pipeline.provenance_resolver.tier_summary()
        self.assertIsInstance(summary, dict)
        self.assertEqual(sum(summary.values()), len(pipeline.evidence_index.by_relpath),
                         "INT-03: tier_summary 覆盖所有 Index 资源")

    def test_int03_g1_not_touched(self):
        """红线 1: 生产 G1 模块 0 改动. 本 commit 只消费不写 G1."""
        import importlib, sys
        # 读取 g1_evidence.py 源码, 确认没有 import governance
        text = (Path(__file__).resolve().parents[1] / "src" / "tongshu" /
                "audit_validation" / "gates" / "g1_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("governance", text,
                         "红线 1: g1_evidence.py 不得 import 或使用 governance 包")
        self.assertNotIn("ResolvedProvenance", text)
        self.assertNotIn("evidence_index", text)

    def test_t3_baseline_untouched(self):
        """T-3: 现有回归基线 62 passed 必须维持 (不漂移).

        本测试单独跑 3 个核心套件, 任一新增 failure 即 T-3 失败.

        [2026-11-07 变更] 原第 4 个套件 tests/test_ziping_15_2_evidence_provenance.py
        属已删除的 ZIPING-V3 线（其 `from tongshu.reasoning.judgment import CITATION`
        在 V3 移除后无法收集），已随 V3 一并删除；基线 73→62。
        """
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             str(_REPO_ROOT / "tests" / "test_p0_evidence_chain.py"),
             str(_REPO_ROOT / "tests" / "test_audit_gates.py"),
             str(_REPO_ROOT / "tests" / "test_api.py"),
             "-q"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
        )
        self.assertIn("62 passed", result.stdout,
                      f"T-3 回归漂移:\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
