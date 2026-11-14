"""C9P2A 审计 P1 修复回归测试 — audit final_output 必须与交付一致。

P1（CONDITIONAL 阻塞项）:
  Phase 2 重构后,渲染成功但校验失败 → 模板回退交付时,audit entry 的
  final_output 仍记录**降级前**的 LLM 文本与 source=llm_renderer
  （audit_composer 误用 render.rendered_text / render.source——
  RenderStageResult 快照不经回退更新）。修复后 final_output 必须与
  PipelineResult（实际交付物）逐字一致: AUDIT == DELIVERED。

P2（一并恢复的契约）:
  enable_validation=False 时基线语义 = 保留 LLM 文本、**不**触发模板回退。
  Phase 2 重构把 ValidationStage 在"校验被禁用"时返回的 passed=False
  误当作校验失败 → 错误降级。恢复: 仅当 _enable_validation 时才走回退分支。

策略与 tests/test_audit_gates.py::TestPipelineWiring 一致:
  _env_without 剥离 LLM 键 → 确定性 StubLLMClient;poisoned renderer 注入
  G3 safety gate 违禁文本强制校验失败（复用其验证过的模式）。
"""

from __future__ import annotations
import json
import os
import unittest
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from tongshu.pipeline import TONGSHUPipeline
from tongshu.reasoning.knowledge_base import KbLoader
from tongshu.reasoning.mapping_registry import MappingRegistry
from tongshu.reasoning.matcher import RuleMatcher
from tongshu.reasoning.rule_loader import RuleLoader
from tongshu.render.renderer import RenderResult

_LLM_ENV_VARS = ("TONGSHU_LLM_API_KEY", "TONGSHU_LLM_BASE_URL", "TONGSHU_LLM_MODEL", "DEEPSEEK_API_KEY")
_ROOT = Path(__file__).resolve().parents[1]

_POISONED_TEXT = "此局稳赚不赔,务必今朝行动。"  # G3 safety gate 必命中


@contextmanager
def _env_without(*names: str):
    saved = {n: os.environ.pop(n, None) for n in names}
    try:
        yield
    finally:
        for n, v in saved.items():
            if v is not None:
                os.environ[n] = v


def _make_pipeline(enable_validation: bool = True) -> TONGSHUPipeline:
    """复制 for_demo 的装配,但允许注入 enable_validation（P2 场景）。"""
    data_dir = TONGSHUPipeline.resolve_data_dir(_ROOT)
    loader = RuleLoader(data_dir, _ROOT / "docs")
    KbLoader(data_dir, _ROOT / "docs")  # 装配即校验数据可达性
    matcher = RuleMatcher(loader.rules)
    registry = MappingRegistry(data_dir, _ROOT / "docs")
    return TONGSHUPipeline(
        schema_dir=_ROOT / "docs",
        mapping_path=_ROOT / "docs" / "theme_mapping.yaml",
        audit_dir=_ROOT / "backend" / "audit",
        matcher=matcher,
        mapping_registry=registry,
        evidence_ids=loader.evidence_ids,
        enable_validation=enable_validation,
    )


def _poison(pipeline: TONGSHUPipeline, text: str):
    """替换 renderer.render 输出为 text,返回 (原始 render, poisoned render)。"""
    original = pipeline.renderer.render

    def poisoned(sir, render_request):
        res = original(sir, render_request)
        return RenderResult(
            text=text,
            covered_claim_ids=res.covered_claim_ids,
            honored_exclusion_ids=res.honored_exclusion_ids,
            self_check=res.self_check,
            raw_output=res.raw_output,
        )

    return original, poisoned


def _read_entry(pipeline: TONGSHUPipeline, entry_id: str) -> dict:
    with open(pipeline.audit_writer.log_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry["entry_id"] == entry_id:
                return entry
    raise AssertionError(f"audit entry {entry_id} not found")


class TestAuditFinalOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with _env_without(*_LLM_ENV_VARS):
            cls.pipeline = TONGSHUPipeline.for_demo(_ROOT)

    def _run(self, **kw):
        defaults = dict(
            analysis_date=date(2026, 8, 17),
            birth_date=(1984, 12, 7, 16),
            gender="male",
            theme="WORK",
        )
        defaults.update(kw)
        return self.pipeline.run(**defaults)

    def test_fallback_audit_matches_delivered(self):
        """P1:模板回退交付时,audit final_output 必须等于实际交付(非 LLM 快照)。"""
        original, poisoned = _poison(self.pipeline, _POISONED_TEXT)
        self.pipeline.renderer.render = poisoned
        try:
            r = self._run()
        finally:
            self.pipeline.renderer.render = original

        self.assertEqual(r.source, "template_fallback")  # 前提:确实走了回退
        entry = _read_entry(self.pipeline, r.audit_entry_id)
        fo = entry["final_output"]
        self.assertEqual(fo["text"], r.rendered_text)    # AUDIT == DELIVERED
        self.assertEqual(fo["source"], r.source)
        self.assertEqual(fo["source"], "template_fallback")
        self.assertNotEqual(fo["text"], _POISONED_TEXT)  # 绝不能记录降级前的 LLM 文本

    def test_validation_disabled_keeps_llm_text(self):
        """P2:enable_validation=False → 保留 LLM 文本、不触发模板回退。"""
        with _env_without(*_LLM_ENV_VARS):
            p = _make_pipeline(enable_validation=False)
        original, poisoned = _poison(p, _POISONED_TEXT)
        p.renderer.render = poisoned
        try:
            r = p.run(
                analysis_date=date(2026, 8, 17),
                birth_date=(1984, 12, 7, 16),
                gender="male",
                theme="WORK",
            )
        finally:
            p.renderer.render = original

        self.assertEqual(r.source, "llm_renderer")          # 不降级
        self.assertEqual(r.rendered_text, _POISONED_TEXT)   # LLM 文本原样交付
        fo = _read_entry(p, r.audit_entry_id)["final_output"]
        self.assertEqual(fo["text"], _POISONED_TEXT)
        self.assertEqual(fo["source"], "llm_renderer")

    def test_compute_only_final_output(self):
        """防御:compute_only 模式 audit 也用本地变量(空文本 + computed)。"""
        r = self._run(compute_only=True)
        self.assertEqual(r.source, "computed")
        self.assertEqual(r.rendered_text, "")
        fo = _read_entry(self.pipeline, r.audit_entry_id)["final_output"]
        self.assertEqual(fo["text"], "")
        self.assertEqual(fo["source"], "computed")


if __name__ == "__main__":
    unittest.main()
