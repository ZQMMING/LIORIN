"""Pipeline orchestrator — wires engines + reasoning + canonical + render + validation + audit.

This is the end-to-end TONGSHU reasoning pipeline.

V3.6 Phase 2 / Step 3 (2026-08-20):
  - C2 (2026-08-20):区隔 1-6 阶段（计算 + SIR 构造）→ ComputeStage
  - C3 (2026-08-20):区隔 7-8 阶段（渲染 + fallback）→ RenderStage

run() 仍保留阶段 9-10（在线校验 + 审计写入），
下步 C4-C5 迁出。
"""

from __future__ import annotations
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .canonical.composer import CanonicalComposer, CanonicalContent
from .engines.bazi_engine import BaziEngine
from .engines.time.resolver import TimeResolver
from .engines.ziwei_engine import ZiweiEngine
from .engines.huangli_engine import HuangliEngine
from .reasoning.signal_engine import SignalEngine
from .reasoning.theme_engine import ThemeEngine
from .reasoning.matcher import RuleMatcher
from .reasoning.mapping_registry import MappingRegistry, MappingLoadError
from .reasoning.rule_loader import RuleLoader
from .reasoning.knowledge_base import KbLoader
from .render.renderer import Renderer
from .render.template_fallback import TemplateFallback
from .audit.writer import AuditWriter
from .pipeline_stages.compute_stage import ComputeStage
from .pipeline_stages.render_stage import RenderStage
from .pipeline_stages.validation_stage import ValidationStage
from .pipeline_stages.audit_composer import AuditComposer
from .temporal.convergence import TemporalConvergenceEngine
from .assertion.assertion_rule_library import ProductionRuleLoader
from .governance.evidence_index import EvidenceIndex
from .governance.provenance_resolver import ProvenanceResolver

log = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Final pipeline output."""
    canonical: CanonicalContent
    rendered_text: str
    validation_passed: bool
    source: str
    audit_entry_id: str
    render_elapsed_ms: float | None = None
    # Step 6: 当 pipeline.run() 提供 dao_conn 时为运行时计算记录的 DB 主键 ID
    # (仅在 DAO 接线时设置；None = 未接线)
    db_run_id: str | None = None
    db_audit_id: str | None = None
    # B-01: 河洛/易经透传（None = 降级未产出）
    heluo_result: Any = None
    yi_structure: Any = None
    yi_interpretation: Any = None
    # P1.3 dual-track: CanonicalSignal by layer (empty dict = not enabled)
    canonical_signals: dict[str, list] = None
    # P1.7: 时序收敛结果（None = 未启用或无信号）
    temporal_convergence: Any = None
    # E7: 梅花易数引擎输出（None = 未启用）
    meihua_result: Any = None


class TONGSHUPipeline:
    """End-to-end pipeline (单类包含 ComputeStage + RenderStage，阶段 9-10 仍在 run() 内联)。"""

    def __init__(
        self,
        schema_dir: Path,
        mapping_path: Path,
        audit_dir: Path,
        matcher: RuleMatcher = None,
        renderer: Renderer = None,
        enable_validation: bool = True,
        mapping_registry: MappingRegistry = None,
        evidence_ids: set[str] = None,
        temporal_convergence_year: int | None = None,  # P1.7
        assertion_library=None,  # P1.6: ProductionRuleLibrary | None
        evidence_index: "EvidenceIndex | None" = None,  # G0-1: Evidence Corpus Index (树B Corpus Base)
        provenance_resolver: "ProvenanceResolver | None" = None,  # G0-2: Resolved Provenance
        judgment_composer=None,  # BZ-FNDR-15.16 INT-06: Composer
    ):
        self.schema_dir = Path(schema_dir)
        self.mapping_path = Path(mapping_path)
        self.audit_dir = Path(audit_dir)
        # G0: 基础设施注入 (INT-01/02/03 生产接线)
        self.evidence_index = evidence_index  # 树B Corpus Base Index (None = 未接入)
        self.provenance_resolver = provenance_resolver  # Resolved Provenance (None = 未接入)
        # BZ-FNDR-15.16 INT-06: JudgmentClaimComposer 由 for_demo 显式注入, 默认 None
        self.judgment_composer = judgment_composer  # Composer (None = 未接入)

        from .engines.bazi_engine import canonical_bazi_engine
        self.bazi_engine = canonical_bazi_engine
        # node_modules located at repo_root/node_modules (schema_dir = <repo>/docs)
        self.ziwei_engine = ZiweiEngine(node_modules_dir=self.schema_dir.parent / "node_modules")
        self.huangli_engine = HuangliEngine()
        self.rule_matcher = matcher or RuleMatcher([])
        self.signal_engine = SignalEngine(self.rule_matcher)
        self.time_resolver = TimeResolver()
        self.theme_engine = ThemeEngine(self.mapping_path)
        self.renderer = renderer or Renderer()
        self.template_fallback = TemplateFallback()
        self.audit_writer = AuditWriter(self.audit_dir)
        self.mapping_registry = mapping_registry
        self._evidence_ids = evidence_ids or set()
        self._enable_validation = enable_validation

        # P1.7: TemporalConvergenceEngine (optional, None = no convergence)
        self._temporal_convergence_engine = None
        if temporal_convergence_year is not None:
            self._temporal_convergence_engine = TemporalConvergenceEngine(
                target_year=temporal_convergence_year
            )

        # 阶段 1-6 ：ComputeStage
        self.compute_stage = ComputeStage(
            bazi_engine=self.bazi_engine,
            ziwei_engine=self.ziwei_engine,
            huangli_engine=self.huangli_engine,
            signal_engine=self.signal_engine,
            theme_engine=self.theme_engine,
            mapping_registry=self.mapping_registry,
            composer=None,  # 每次 run() 重建（需要 theme 参数）
            schema_dir=self.schema_dir,
            matcher=self.rule_matcher,
            renderer_model_id=self.renderer.model_id,
            temporal_convergence_engine=self._temporal_convergence_engine,
            assertion_library=assertion_library,  # P1.6: 生产断言库
        )

        # 阶段 7-8 ：RenderStage
        self.render_stage = RenderStage(
            renderer=self.renderer,
            template_fallback=self.template_fallback,
        )

        # 阶段 9 ：ValidationStage
        self.validation_stage = ValidationStage(
            evidence_ids=self._evidence_ids,
            mapping_registry=self.mapping_registry,
            enable_validation=self._enable_validation,
            provenance_resolver=self.provenance_resolver,  # G0-2 接入
        )

        # 阶段 10 ：AuditComposer
        self.audit_composer = AuditComposer(audit_writer=self.audit_writer)

    @classmethod
    def for_demo(cls, repo_root: Path) -> "TONGSHUPipeline":
        data_dir = repo_root / "backend" / "data"
        loader = RuleLoader(data_dir, repo_root / "docs")
        missing = loader.verify_evidence_refs()
        if missing:
            log.warning("rules reference missing evidence records (DoD #4): %s", missing)
        kb = KbLoader(data_dir, repo_root / "docs")
        kb_violations = kb.verify_link_closure(loader.rules)
        if kb_violations:
            log.warning("Knowledge Base link closure violations: %s", kb_violations)
        matcher = RuleMatcher(loader.rules)
        mapping_registry = None
        try:
            mapping_registry = MappingRegistry(data_dir, repo_root / "docs")
        except MappingLoadError as e:
            log.warning("Mapping Registry load failed (degraded, no 词库标签): %s", e)

        # P1.6: 加载生产断言库（ProductionRuleLibrary）
        # Fail-closed: 加载失败必须阻断生产启动，不得降级为 None
        assertion_rules_path = repo_root / "data" / "assertion_rules" / "production_assertion_rules.json"
        if not assertion_rules_path.exists():
            raise RuntimeError(
                f"P1.6: Production assertion rules not found at {assertion_rules_path}. "
                "Production pipeline requires production_assertion_rules.json to exist."
            )

        # P2.1-F: Bootstrap authority from TONGSHU_AUTHORITY_CREDENTIALS env var.
        # Authority credential MUST come from outside the repository (env var /
        # deployment config), NOT from any file in the same git repo as production
        # rules. This prevents an attacker who can modify repo files from
        # simultaneously tampering both manifest and rules to pass bootstrap.
        #
        # F2: Fail-closed — any missing credential or declared hash → RuntimeError.
        from .assertion.admission_registry import (
            load_trust_root,
            verify_authority_credential,
            register_authority_credential,
            lock_authority_registry,
            _AUTHORITY_LOCKED,
        )
        try:
            trust_root = load_trust_root()
        except RuntimeError as _e:
            raise RuntimeError(f"P2.1-F bootstrap failed: {_e}") from _e

        # Read rules _meta.declared_credential_hash for integrity check
        with open(assertion_rules_path, encoding="utf-8") as _rf:
            _rules_meta = __import__("json").load(_rf).get("_meta", {})
        _declared_hash = _rules_meta.get("declared_credential_hash", "")
        if not _declared_hash:
            raise RuntimeError(
                "P2.1-F: production_assertion_rules.json missing _meta.declared_credential_hash. "
                "Production rules must declare an authority fingerprint for trust root verification."
            )
        # At least one env var credential must match the rules' declared hash
        _cred_match_found = any(
            verify_authority_credential(_cred, _declared_hash)
            for _cred in trust_root.values()
        )
        if not _cred_match_found:
            raise RuntimeError(
                "P2.1-F: No credential in TONGSHU_AUTHORITY_CREDENTIALS matches "
                "production assertion rules _meta.declared_credential_hash. Bootstrap rejected."
            )

        # Register and lock
        if _AUTHORITY_LOCKED:
            log.info("P2.1-F: Authority registry already locked, skipping bootstrap.")
        else:
            for _src, _cred in trust_root.items():
                register_authority_credential(_src, _cred)
            lock_authority_registry()
            log.info(
                "P2.1-F: Authority registry bootstrapped from env var "
                "(sources=%s).",
                ", ".join(trust_root.keys()),
            )
        try:
            assertion_library = ProductionRuleLoader.load(str(assertion_rules_path))
            log.info("P1.6: Loaded %d production assertion rules from %s",
                    len(assertion_library._rules if hasattr(assertion_library, '_rules') else 0),
                    assertion_rules_path)
        except Exception as e:
            raise RuntimeError(
                f"P1.6: Failed to load production assertion rules from {assertion_rules_path}: {e}"
            ) from e

        # G0-1/02 (INT-02): Evidence Index = Tree B Corpus Base (data/evidence)
        # Option A: 保持 RuleLoader 读树A (backend/data), 规则面 136 维持不变
        #          evidence 可见性切到树B (5701 files, 5614 子目录 + 86 根级)
        corpus_root = repo_root / "data" / "evidence"
        evidence_index = EvidenceIndex.build(corpus_root, tree="corpus_base")
        provenance_resolver = ProvenanceResolver(evidence_index)  # G0-2 / INT-03

        # BZ-FNDR-15.16 INT-06: JudgmentClaimComposer (S1~S6 全部应用)
        # Composer 在 ComputeStage 内部编排, 不在 Pipeline.run() 重复调度 (避免 T-3 漂移)
        # ⚠️ INT-06 默认 OFF: Composer 模块就绪但 production path 不打开,
        # 避免 Composer claims 影响 G1 evidence_gate (T-3 漂移 4 tests).
        # 打开 Composer 需要 User 单独授权 + 进一步处理 Composer claims G1 适配.
        from .governance.judgment_claim_composer import JudgmentClaimComposer
        judgment_composer = JudgmentClaimComposer(
            provenance_resolver=provenance_resolver,
        )

        return cls(

            schema_dir=repo_root / "docs",
            mapping_path=repo_root / "docs" / "theme_mapping.yaml",
            audit_dir=repo_root / "backend" / "audit",
            matcher=matcher,
            mapping_registry=mapping_registry,
            evidence_ids=loader.evidence_ids | {
                # Synthetic BAZI ten-god evidence IDs produced at runtime by compute_stage.
                # These MUST be in the registered set so G1 evidence_gate accepts them
                # (the runtime engine emits them; they are NOT in static evidence files).
                "BZI-TG-year", "BZI-TG-month", "BZI-TG-day", "BZI-TG-hour",
            },
            temporal_convergence_year=None,  # for_demo: no analysis_date context
            assertion_library=assertion_library,  # P1.6: 生产断言库
            evidence_index=evidence_index,  # G0-1: 树B证据索引（Corpus Base）
            provenance_resolver=provenance_resolver,  # G0-2: Resolved Provenance
            judgment_composer=judgment_composer,  # INT-06: Composer 编排
        )



    @staticmethod
    def _derive_cross_status(cross_result) -> str:
        """M2 cross_status 派生（M2 架构禁止方向/极性字段，由 coverage 形态推导）。

        Returns: "ALIGNED" | "PARTIAL" | "INSUFFICIENT"
        """
        if cross_result is None:
            return "INSUFFICIENT"
        # Count engines with non-empty evidence
        engines_with_evidence = sum(
            1 for eng_set in cross_result.by_engine.values()
            if eng_set.evidence_ids
        )
        engines_total = len(cross_result.by_engine)
        if engines_with_evidence == 0:
            return "INSUFFICIENT"
        if engines_with_evidence < engines_total:
            return "PARTIAL"
        # All engines have evidence → ALIGNED
        if cross_result.coverage.total_assertions == 0:
            return "INSUFFICIENT"
        return "ALIGNED"

    def run(
        self,
        analysis_date: date,
        birth_date: tuple[int, int, int, int],
        gender: str = "male",
        theme: str = "WORK",
        forbidden_inferences: list = None,
        compute_only: bool = False,
        trace_id: str | None = None,
        dao_conn = None,
        *,
        timezone: str | None = None,
        location: str | None = None,
        birth_minute: int | None = None,
    ) -> PipelineResult:
        """执行完整管道。

        参数：
            ...（同上）
            dao_conn: 可选的 DB 连接。提供时，
                除文件 audit_log.jsonl 外，还会调用 tongshu.db.dao
                将 calculation_runs / audit_runs / api_requests 落入指定连接。
                None (默认) = 仅文件 audit （与原行为一致）。
                调用方负责事务管理（commit/rollback）与连接关闭。
            timezone/location/birth_minute: B-02 时间政策输入。
                提供时构建 CalculationContext，引擎经 BaziAdapter/ZiweiAdapter
                调用以生效 23:00 日界政策；均为 None 时保留旧直调路径。
        """
        request_id = f"RR-{uuid.uuid4().hex[:8].upper()}"
        trace_id = trace_id or f"TRACE-{uuid.uuid4().hex[:8].upper()}"

        # B-02: 构建时间事实层（仅在 timezone + location 均提供时）
        calc_context = None
        if timezone is not None and location is not None:
            by, bm, bd, bh = birth_date
            calc_context = self.time_resolver.resolve_context(
                birth_date=date(by, bm, bd),
                hour=bh,
                minute=birth_minute,
                timezone=timezone,
                location=location,
                gender=gender,
            )

        # 阶段 1-6 ：ComputeStage (计算 + SIR 构造)
        # 需要在每次 run() 重建 composer（theme 依赖）
        self.compute_stage.composer = CanonicalComposer(
            theme=theme,
            engine_versions={
                "bazi": "1.0.0",
                "ziwei": "1.0.0",
                "rules": "1.0.0",
                "reasoning": "1.0.0",
            },
        )
        # BZ-FNDR-15.20 Step 4: Composer ON — judgment_composer 从 None 切换为生产实例
        compute = self.compute_stage.run(
            analysis_date=analysis_date,
            birth_date=birth_date,
            gender=gender,
            theme=theme,
            request_id=request_id,
            trace_id=trace_id,
            calc_context=calc_context,
            judgment_claims=[],
            judgment_composer=self.judgment_composer,  # Step 4: ON (S1~S6 fail-closed)
        )
        canonical = compute.canonical
        signals = compute.signals
        cross_result = compute.cross_result
        atomic_claims = compute.atomic_claims
        is_valid = compute.canonical_schema_valid
        errs = list(compute.canonical_schema_errors)

        # 阶段 7-8 ：RenderStage (渲染 + fallback)
        if compute_only:
            render = RenderStage.make_computed()
        else:
            render = self.render_stage.run(compute, request_id, theme)
        render_request_dict: dict[str, Any] = render.render_request_dict
        rendered = render.rendered
        render_elapsed_ms = render.render_elapsed_ms
        rendered_text = render.rendered_text
        source = render.source

        # 阶段 9 ：ValidationStage (以下为调用、它返回 ValidationStageResult)
        if compute_only or rendered is None:
            validation = ValidationStage.make_skip()
            validation_passed = False
        else:
            validation = self.validation_stage.run(compute, render, forbidden_inferences)
            validation_passed = validation.passed
            source = "llm_renderer"
            if not validation_passed and self._enable_validation:
                # template fallback（校验启用且不通过 → 降级到模板；基线契约：
                # enable_validation=False 时保留 LLM 文本、不降级）
                # cross_status 派生：M2 架构下 CrossDomainResult 无 status 字段。
                # 派生规则：所有 ZI 引擎 evidence_ids 都为空 → INSUFFICIENT；只有部分 → PARTIAL；多引擎 → ALIGNED。
                cross_status = self._derive_cross_status(compute.cross_result)
                fallback = self.template_fallback.render(theme, cross_status)
                if fallback:
                    rendered_text = fallback
                    source = "template_fallback"
        # 以下字段仅供 audit 使用（后续 C5 迁出）

        # 阶段 10 ：AuditComposer 写入审计日志
        entry_id = self.audit_composer.compose_and_write(
            request_id=request_id,
            trace_id=trace_id,
            spec_version="1.0",
            document_id=canonical.canonical_id,
            compute=compute,
            render=render,
            validation=validation,
            theme=theme,
            model_id=self.renderer.model_id,
            final_text=rendered_text,
            final_source=source,
            compute_only=compute_only,
        )

        # Step 6: DAO 写路径接线（可选）。仅在 dao_conn 提供时生效，
        # 调用方责责事务管理（commit/rollback）与连接关闭；成功/失败均不影响 pipeline 返回。
        db_run_id: str | None = None
        db_audit_id: str | None = None
        if dao_conn is not None:
            db_run_id, db_audit_id = self._write_to_dao(
                dao_conn=dao_conn,
                request_id=request_id,
                trace_id=trace_id,
                analysis_date=analysis_date,
                theme=theme,
                canonical_id=canonical.canonical_id,
                source=source,
                validation=validation,
                atomic_claims=atomic_claims,
                rendered_text=rendered_text,
            )

        return PipelineResult(
            canonical=canonical,
            rendered_text=rendered_text,
            validation_passed=validation_passed,
            source=source,
            audit_entry_id=entry_id,
            render_elapsed_ms=render_elapsed_ms,
            db_run_id=db_run_id,
            db_audit_id=db_audit_id,
            heluo_result=compute.heluo_result,
            yi_structure=compute.yi_structure,
            yi_interpretation=compute.yi_interpretation,
            canonical_signals=compute.canonical_signals,
            temporal_convergence=compute.temporal_convergence,
            meihua_result=compute.meihua_result,
        )

    def _write_to_dao(
        self,
        *,
        dao_conn,
        request_id: str,
        trace_id: str,
        analysis_date,
        theme: str,
        canonical_id: str,
        source: str,
        validation,
        atomic_claims: list,
        rendered_text: str,
    ) -> tuple[str | None, str | None]:
        """DAO 写路径接线中间函数（仅在 dao_conn 提供时调用）。

        调用顺序（与 test_db_roundtrip 一致）：
            1. record_calculation_run → run_id
            2. record_rule_results （逐条 claim 为一条，matched=True）
            3. record_expression （source + text）
            4. record_audit → audit_id（含 gate findings）
            5. record_api_request （latency_ms=0，具体由调用方负责）

        返回：(run_id, audit_id) 二元组。任何错误都会被打日志并返回 (None, None)，
        不影响主管道。
        """
        from .db import dao
        run_id: str | None = None
        audit_id: str | None = None
        try:
            # DB schema 约束映射（otcg 库的 status/source 取值）：
            #   status: ok | fallback | error (不含 compute_only)
            #   source: llm | template (不含 llm_renderer/template_fallback/computed)
            db_status = "ok" if validation.passed else "fallback"
            db_source = "llm" if source == "llm_renderer" else "template"
            run_id = dao.record_calculation_run(
                dao_conn,
                birth_profile_id=None,
                analysis_date=analysis_date,
                theme=theme,
                request_id=request_id,
                trace_id=trace_id,
                canonical_id=canonical_id,
                status=db_status,
                source=db_source,
                model_id=self.renderer.model_id,
                prompt_version="prompt.1.0.0",
                versions={
                    "calculation": "1.0.0",
                    "knowledge": "1.0.0",
                    "mapping": "0.1.0",
                    "translation": "0.1.0",
                },
            )
            # record_rule_results：以 atomic_claims 为底生成 rule_results
            rule_results = [
                {
                    "rule_id": c.get("claim_id", "?"),
                    "signal_id": c.get("signal_type"),
                    "matched": True,
                    "payload": {
                        "direction": c.get("direction"),
                        "strength": c.get("strength"),
                        "source_layers": c.get("source_layers", []),
                    },
                }
                for c in atomic_claims
            ]
            if rule_results:
                dao.record_rule_results(dao_conn, run_id, rule_results)

            # record_expression：compute_only 跳过（没有实际 expression）
            if source != "computed":
                dao.record_expression(
                    dao_conn, run_id,
                    source=db_source,  # "llm" | "template"
                    text=rendered_text,
                    covered_claim_ids=[c.get("claim_id", "?") for c in atomic_claims],
                    validation_passed=validation.passed,
                )

            # record_audit
            findings = []
            for layer_name in ("layer1", "layer2", "layer3"):
                layer_obj = getattr(validation, layer_name, None)
                if layer_obj is not None and not getattr(layer_obj, "passed", True):
                    findings.append({
                        "layer": layer_name.upper(),
                        "finding_code": "FAIL",
                        "message": getattr(layer_obj, "errors", None) or "validation failed",
                    })
            for g in validation.gates:
                if not g.passed:
                    findings.append({
                        "layer": g.gate,
                        "finding_code": "BLOCK",
                        "message": "; ".join(g.reasons[:3]),
                    })
            if not findings:
                findings.append({"layer": "OVERALL", "finding_code": "OK", "message": "all checks passed"})

            audit_id = dao.record_audit(
                dao_conn, run_id,
                request_id=request_id,
                trace_id=trace_id,
                document_id=canonical_id,
                validation_passed=validation.passed,
                gates={
                    g.gate: {"passed": g.passed, "reasons": g.reasons}
                    for g in validation.gates
                },
                findings=findings,
            )

            # record_api_request
            dao.record_api_request(
                dao_conn,
                request_id=request_id,
                trace_id=trace_id,
                method="INTERNAL",
                path="/v1/daily-guide",
                status_code=200,
                error_code=None,
                latency_ms=0,
            )
        except Exception as e:  # noqa: BLE001 - DAO 不能报错主管道
            log.warning("DAO 写路径失败（仅日志记录，不影响主管道）: %s", e)
            return None, None
        return run_id, audit_id
