"""ComputeStage — 阶段 1-6（计算 + SIR 构造）。

职责：
    1. bazi / ziwei / huangli 三引擎计算
    2. 信号提取（Bazi/Ziwei 分轨，DECISION-002）
    3. 跨域编排（CrossDomainOrchestrator，P1.6）
    4. atomic_claims 构造（含 mapping_refs 附加，direction 来自授权 Rule）
    5. SIR 构造（CanonicalComposer）
    6. SIR schema 校验（jsonschema Draft202012Validator）

设计：纯计算，无渲染、无校验、无审计。返回 ComputeResult。

Version: 1.1.0 (P1.6: CrossDomainOrchestrator 接入生产路径)
Created: 2026-08-20 (Phase 2 / Step 3 C2)
Migrated from: pipeline.py:113-235（run() 阶段 1-6）
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
import uuid
from pathlib import Path

from ..canonical.canonical_validator import validate_canonical
from ..canonical.composer import CanonicalComposer
from ..cross_domain import CrossDomainOrchestrator
from ..engines.bazi_adapter import BaziAdapter
from ..engines.bazi_engine import BaziEngine
from ..engines.huangli_engine import HuangliEngine
from ..engines.time.calculation_context import CalculationContext
from ..engines.ziwei_adapter import ZiweiAdapter
from ..engines.ziwei_engine import ZiweiEngine
from ..reasoning.mapping_registry import MappingRegistry
from ..reasoning.matcher import RuleMatcher
from ..reasoning.signal_engine import SignalEngine
from ..reasoning.theme_engine import ThemeEngine
from ..spec.canonical import EngineEvidence, SemanticAtom, EngineName, TemporalScope
from ..temporal.convergence import TemporalConvergenceEngine
from ..temporal.schema import PredictionWindow, TemporalGranularity, TemporalSignal
from ..types import ComputeResult

log = logging.getLogger(__name__)


class ComputeStage:
    """阶段 1-6: 纯计算 + SIR 构造。

    P1.6: 接受可选的 assertion_library（ProductionRuleLibrary），
    通过 CrossDomainOrchestrator 编排跨域证据，direction 来自 Rule 授权。
    """

    def __init__(
        self,
        bazi_engine: BaziEngine,
        ziwei_engine: ZiweiEngine,
        huangli_engine: HuangliEngine,
        signal_engine: SignalEngine,
        theme_engine: ThemeEngine,
        mapping_registry: MappingRegistry | None,
        composer: CanonicalComposer,
        schema_dir: Path,
        matcher: RuleMatcher,
        renderer_model_id: str,
        assertion_library=None,  # ProductionRuleLibrary | None (P1.6)
        temporal_convergence_engine: TemporalConvergenceEngine | None = None,  # P1.7
        blind_engine=None,  # BZ-BLIND-001: BlindBaziEngine | None（可注入测试；None=懒加载）
    ) -> None:
        self.bazi_engine = bazi_engine
        self.ziwei_engine = ziwei_engine
        self.huangli_engine = huangli_engine
        self.signal_engine = signal_engine
        self.theme_engine = theme_engine
        self.mapping_registry = mapping_registry
        self.composer = composer
        self.schema_dir = Path(schema_dir)
        self.matcher = matcher
        self._renderer_model_id = renderer_model_id
        # BUG-P0-03: 河洛引擎已从主工作区移除（独立为 feature/heluo-engine-package-20261011 包）。
        # 河洛→Yi 输入源不再可用，heluo_result 恒为 None，不影响 bazi/ziwei/huangli 主链路。
        self.heluo_canonical = None
        # B-02: 时间政策 Adapter（封装 23:00 日界 / 阳→农历转换）
        self._bazi_adapter = BaziAdapter(bazi_engine)
        self._ziwei_adapter = ZiweiAdapter(ziwei_engine)
        # E7: 梅花易数 Adapter（可选，None = 未启用）
        from ..feature_registry import FeatureRegistry
        from ..engines.meihua import cast_by_time, cast_by_numbers
        self._meihua_feature_registry = FeatureRegistry()
        from ..feature_registry.adapters.mei_hua_adapter import MeiHuaFeatureAdapter
        self._meihua_adapter = MeiHuaFeatureAdapter(self._meihua_feature_registry)
        self._meihua_compute_fn = None  # set externally or use defaults
        self._meihua_question = ""
        # BZ-BLIND-001: 盲派 Adapter（可选，None = 未启用/降级）。
        # 消费主链 BaziChart（S0 契约 compute_from_chart，禁止重排盘）。
        self._blind_feature_registry = FeatureRegistry()
        from ..feature_registry.adapters.blind_school_adapter import BlindSchoolFeatureAdapter
        self._blind_adapter = BlindSchoolFeatureAdapter(self._blind_feature_registry)
        self._blind_engine = blind_engine  # BlindBaziEngine | None（懒加载）
        # P1.6: CrossDomainOrchestrator（可选，None = 降级为旧信号路径）
        self._assertion_library = assertion_library
        self._orchestrator = None
        if assertion_library is not None and getattr(assertion_library, "is_production", False):
            self._orchestrator = CrossDomainOrchestrator(assertion_library=assertion_library)
        # P1.7: TemporalConvergenceEngine（可选，None = 跳过时序收敛）
        self._temporal_convergence_engine = temporal_convergence_engine

    def run(
        self,
        analysis_date: date,
        birth_date: tuple[int, int, int, int],
        gender: str,
        theme: str,
        request_id: str,
        trace_id: str,
        calc_context: CalculationContext | None = None,
        judgment_claims: list[dict] | None = None,  # BZ-FNDR-15.16 INT-06: Composer 产 claims
        judgment_composer=None,  # BZ-FNDR-15.16 INT-06: Composer 实例 (内部编排)
    ) -> ComputeResult:
        """执行阶段 1-6 全流程：bazi+ziwei+huangli → signals → cross → claims → SIR → schema。"""

        # 1. Engine layer
        # B-02: calc_context 提供时经时间政策 Adapter 调用（23:00 日界 / 阳→农历）；
        # 无 calc_context 时保留直调以向后兼容。
        if calc_context is not None:
            effective_gender = calc_context.subject_gender or gender
            bazi_chart = self._bazi_adapter.compute(calc_context, gender=effective_gender)
            year, month, day, hour = calc_context.bazi_view
            ziwei_chart = self._ziwei_adapter.compute(year, month, day, hour, gender=effective_gender)
        else:
            # 无 calc_context：为保证排盘恒真太阳时（不再民用时直排），
            # 用 TimeResolver 按默认 location 构造真太阳时 ctx 兜底。
            # 调用方应优先显式传 calc_context（真实出生地）；此处默认北京。
            from datetime import date as _date
            from ..engines.time.resolver import TimeResolver
            by, bm, bd, bh = birth_date
            _default_ctx = TimeResolver().resolve_context(
                birth_date=_date(by, bm, bd),
                hour=bh,
                minute=30,  # 时辰中点（无分钟输入）
                timezone="Asia/Shanghai",
                location="北京",
                gender=gender,
            )
            effective_gender = _default_ctx.subject_gender or gender
            bazi_chart = self._bazi_adapter.compute(_default_ctx, gender=effective_gender)
            year, month, day, hour = _default_ctx.bazi_view
            ziwei_chart = self._ziwei_adapter.compute(
                year, month, day, hour, gender=effective_gender
            )
        huangli_day = self.huangli_engine.get_day(analysis_date)

        # BZ-FNDR-15 (⑮-0 Bazi -> Ziping 接入契约):
        # 把 bazi_chart 转成 CanonicalBaziChart 作为下游子平的契约入口.
        # from_bazi_chart() 是唯一工厂路径, 自动登记 provenance=from_bazi_chart,
        # 下游 Ziping 通过 assert_canonical_gate(require_factory=True) 校验构造来源.
        # BZ-FNDR-15 (⑮-0 接入契约): 用 ZiPingCanonicalBaziChart 而非裸 CanonicalBaziChart.
        # ZiPing 必须消费 ⑬⑨⑩ ⑥⑪ 的确定性派生 (luck_pillars / branch_*_map /
        # kong_wang / day_branch_main_ten_god / five_element_balance),
        # 这些不在 ⑭ 冻结的 CanonicalBaziChart 里, 但属于 ZiPing 正式契约.
        from ..models.canonical_bazi import ZiPingCanonicalBaziChart
        canonical_bazi_chart = ZiPingCanonicalBaziChart.from_bazi_chart(bazi_chart)

        # 1b. 河洛理数 + 易经解释引擎（BUG-P0-03 接入主 Pipeline）。
        # 河洛计算 → YiAdapter 适配为 YiStructure → YiInterpretationEngine 解释。
        # 任何一步失败都降级为 None，不影响既有 bazi/ziwei/huangli 主链路。
        # 1b. 河洛理数 + 易经解释引擎：河洛引擎已从主工作区移除（独立包），
        # heluo_result / yi_structure / yi_interpretation 恒为 None，主链路不受影响。
        heluo_result, yi_structure, yi_interpretation = None, None, None

        # 1c. 梅花易数引擎（E7 接入）
        # 支持两种模式: Mode A(时间起卦) / Mode B(数字起卦)
        # 计算结果经 Adapter 转换为 FeatureMapResult
        meihua_result = self._compute_meihua(year, month, day, hour, gender)

        # 1d. 盲派引擎（BZ-BLIND-001 接入）
        # 数据流: BaziChart（主链八字排盘结果）→ BlindBaziEngine.compute_from_chart()
        #     → BlindBaziResult → BlindSchoolFeatureAdapter.adapt() → FeatureMapResult
        # 任何失败降级为 None，不影响既有主链路。
        blind_result = self._compute_blind(bazi_chart, gender)

        # 2. 信号提取（Bazi only - P1-C fix keeps Ziwei separate）
        build_result = self.signal_engine.build(
            bazi_chart, ziwei_chart, huangli_day, gender=gender, theme=theme, heluo_result=heluo_result
        )
        signals = build_result["signals"]
        canonical_signals = build_result.get("canonical_signals", {})

        # 3. Cross-domain orchestration (P1.6)
        # If assertion_library is provided, use CrossDomainOrchestrator to produce
        # authorized assertions with direction from Rule (not from Signal).
        # P1.6 BLOCKING FIX: No fail-open fallback — authorization failure = NO CLAIM.
        cross_result = None
        authorized_assertions = []
        if self._orchestrator is not None and signals:
            cross_result = self._orchestrate_signals(bazi_chart, ziwei_chart, signals)
            authorized_assertions = self._extract_authorizations(cross_result)

        # 3b. Temporal convergence (P1.7)
        # Harmonize signals across temporal layers (BIRTH/YEAR/DAY) for unified view.
        temporal_convergence = None
        if self._temporal_convergence_engine is not None and signals:
            temporal_convergence = self._run_temporal_convergence(signals, analysis_date)

        # 4. Generate atomic_claims from authorized assertions (P1.6 fail-closed)
        # No authorization → NO CLAIM. Legacy fallback removed.
        if authorized_assertions:
            atomic_claims = self._build_claims_from_assertions(theme, authorized_assertions)
        else:
            atomic_claims = []

        # BZ-FNDR-15.16 INT-06: 合并 JudgmentClaimComposer 产 claims (S6 de-dup)
        # Composer 命名空间 AC-ZP-*, Chain-A 命名空间 AC-{assertion_id},
        # namespace 已天然不冲突, 0 de-dup 风险.
        # 顺序: Chain-A 在前 (assertion-driven), Judgment 在后 (deterministic domains).
        # ComputeStage 内部编排 Composer (B+4a 架构保护: 不让 Pipeline 重复 run())
        if judgment_composer is not None:
            try:
                from ..reasoning.ziping_bridge import run_ziping_judgment
                _synth = run_ziping_judgment(bazi_chart)
                _claims = judgment_composer.compose(_synth)
                if _claims:
                    judgment_claims = list(judgment_claims or []) + _claims
            except Exception as _e:  # pragma: no cover - 防御性
                log.warning("INT-06 internal Composer failed (fail-closed): %s", _e)
        if judgment_claims:
            atomic_claims = atomic_claims + list(judgment_claims)

        # 4b. V3.6 §18-21 词库标签层:附加 mapping_refs / modern_theme(DECISION 6
        # 语义边界:只加标签,绝不改写 USO 枚举 / rule_refs / evidence_refs)。
        if self.mapping_registry is not None:
            atomic_claims = self.mapping_registry.apply_to_claims(atomic_claims)

        # 5. Compose SIR
        # Lazy-init CanonicalComposer if not set (needs theme from run() params)
        if self.composer is None:
            self.composer = CanonicalComposer(
                theme=theme,
                engine_versions={
                    "bazi": "1.0.0",
                    "ziwei": "1.0.0",
                    "rules": "1.0.0",
                    "reasoning": "1.0.0",
                },
            )
        canonical = self.composer.compose(
            analysis_date=analysis_date,
            bazi=bazi_chart,
            ziwei=ziwei_chart,
            huangli=huangli_day,
            signals=signals,
            cross_result=cross_result,
            atomic_claims=atomic_claims,
            exclusions=[],
            meta_observability={
                "request_id": request_id,
                "trace_id": (trace_id if trace_id is not None else f"TRACE-{uuid.uuid4().hex[:10].upper()}"),
                "model_version": self._renderer_model_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # 6. Validate canonical
        is_valid, errs = validate_canonical(canonical.to_dict(), self.schema_dir)
        if not is_valid:
            log.warning(f"Canonical validation failed: {errs}")
            # Per architecture: do not proceed with invalid SIR
            # For demo, log and continue

        return ComputeResult(
            bazi_chart=bazi_chart,
            ziwei_chart=ziwei_chart,
            huangli_day=huangli_day,
            signals=signals,
            canonical_signals=canonical_signals,
            cross_result=cross_result,
            authorized_assertions=authorized_assertions,
            temporal_convergence=temporal_convergence,
            atomic_claims=atomic_claims,
            canonical=canonical,
            canonical_schema_valid=is_valid,
            canonical_schema_errors=tuple(errs) if errs else (),
            computed_at=datetime.now(timezone.utc),
            heluo_result=heluo_result,
            yi_structure=yi_structure,
            yi_interpretation=yi_interpretation,
            meihua_result=meihua_result,
            blind_result=blind_result,  # BZ-BLIND-001: 盲派 FeatureMapResult | None
            # BZ-FNDR-15: ⑮-0 接入契约 — 装上 canonical_bazi_chart 给下游 Ziping 消费
            canonical_bazi_chart=canonical_bazi_chart,
        )

    def _compute_meihua(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        gender: str,
    ) -> Any:
        """梅花易数时间起卦（Mode A）。

        数据流：cast_by_time() → MeihuaResult → MeiHuaFeatureAdapter.adapt() → FeatureMapResult
        任何失败降级为 None，不影响主链路。
        """
        try:
            from ..engines.meihua import cast_by_time
            meihua_raw = cast_by_time(year, month, day, hour, question="出生时间起卦")
            return self._meihua_adapter.adapt(meihua_raw)
        except Exception as exc:  # noqa: BLE001 — 梅花降级，不中断主管道
            log.warning("MeiHua integration failed (degraded, 不影响主链路): %s", exc)
            return None

    def _compute_blind(
        self,
        bazi_chart,
        gender: str,
    ) -> Any:
        """盲派引擎（BZ-BLIND-001 接入主 Pipeline）。

        数据流：BaziChart（主链八字排盘结果）→ BlindBaziEngine.compute_from_chart()
            → BlindBaziResult → BlindSchoolFeatureAdapter.adapt() → FeatureMapResult

        约束（盲派架构铁律 §70/§90）：盲派唯一共同消费层 = 八字排盘引擎输出的
        基础事实；compute_from_chart 吃外部 BaziChart、禁止重排盘。
        任何失败降级为 None，绝不让盲派错误中断既有主链路。
        """
        try:
            if self._blind_engine is None:
                from ..engines.blind_bazi_engine import BlindBaziEngine
                self._blind_engine = BlindBaziEngine()
            blind = self._blind_engine.compute_from_chart(bazi_chart, gender=gender)
            return self._blind_adapter.adapt(blind)
        except Exception as exc:  # noqa: BLE001 — 盲派降级，不中断主管道
            log.warning("Blind integration failed (degraded, 不影响主链路): %s", exc)
            return None

    # ─── P1.6: CrossDomainOrchestrator integration ──────────────────────────────

    def _orchestrate_signals(
        self, bazi_chart, ziwei_chart, signals: dict[str, list]
    ):
        """Map engine signals to CrossDomainOrchestrator input and run orchestration."""
        # Build EngineEvidence from signals grouped by engine
        # Also add ten_god evidence from BaziEngine for production rule matching (P1.6)

        # BZ-FNDR-15.2 (⑮-0 P1-2): 十神由 Pillar.stem_ten_god 直接消费.
        # 不调用 bazi_ten_gods.ten_god() 重算 (User 明确拒绝 'fallback 到 ten_god').
        # 缺失时 fail-closed (RuntimeError), 防止 "下游重新计算 Bazi 事实" 的暗门.
        # Pillar.stem_ten_god 由 ⑦ CLOSED 的十神引擎保证.

        engine_evidences: dict[str, list] = {"ZI_PING": [], "ZI_WEI": []}

        # Add BaziEngine ten-god evidence for production rule matching
        day_master = bazi_chart.day_master
        stem_positions = {
            "year": bazi_chart.year_pillar.heavenly_stem,
            "month": bazi_chart.month_pillar.heavenly_stem,
            "day": day_master,
            "hour": bazi_chart.hour_pillar.heavenly_stem,
        }
        # BZ-FNDR-15.2 (⑮-0 P1-2): stem_ten_god 缺失必须 fail-closed.
        # 原 BZ-FNDR-15 的 "缺则 fallback" 被 User 2026-09-10 明确拒绝:
        #   "十神已经由 Bazi 计算完成, ZiPing 不得重新计算"
        #   "stem_ten_god 缺失 → FAIL-CLOSED, 不允许 ten_god() fallback"
        # 后果: 一旦 Bazi 引擎某次没填 Pillar.stem_ten_god, _orchestrate_signals 立刻
        # 抛 RuntimeError 而不是悄悄重算十神 — 防止 "下游重新计算 Bazi 事实" 的暗门.
        pillar_ten_gods = {
            "year": getattr(bazi_chart.year_pillar, "stem_ten_god", "") or "",
            "month": getattr(bazi_chart.month_pillar, "stem_ten_god", "") or "",
            "day": "DAY_MASTER",  # 日主对自身特殊标记
            "hour": getattr(bazi_chart.hour_pillar, "stem_ten_god", "") or "",
        }
        for pos, stem in stem_positions.items():
            tg = pillar_ten_gods.get(pos)
            if not tg:
                # BZ-FNDR-15.2 P1-2: fail-closed, 不再 fallback 到 ten_god()
                raise RuntimeError(
                    f"BZ-FNDR-15.2 fail-closed: Pillar[{pos}].stem_ten_god 为空. "
                    f"Bazi 引擎未填十神, 不能由 compute_stage 偷偷重算 "
                    f"(违反'ZiPing 不得重新计算 Bazi 事实'原则). "
                    f"当前日主: {day_master}, {pos} 干: {stem}. "
                    f"请检查 Bazi 引擎 attach_p2_fields 是否正常执行."
                )
            engine_evidences["ZI_PING"].append(
                EngineEvidence(
                    evidence_id=f"BZI-TG-{pos}",
                    engine=EngineName.ZI_PING,
                    rule_id=f"BZI_TEN_GOD_{pos.upper()}",
                    value=tg,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={"ten_god": tg, "stem": stem, "pillar": pos},
                    source_rule_ref="data/rules/bazi_ten_gods.json",
                    source_field="ten_god",
                )
            )

        # Add Ziwei chart-based evidence (so ZI_WEI gets non-empty by_engine)
        # 这是最小代价修复:让 ziwei chart 的 soul/body palace 派生一条固定 ZI_WEI evidence,
        # 使 CrossDomainOrchestrator.by_engine["ZI_WEI"] 非空 → cross_status → ALIGNED。
        if ziwei_chart is not None:
            if "ZI_WEI" not in engine_evidences:
                engine_evidences["ZI_WEI"] = []
            soul_palace = (
                ziwei_chart.get("soul") if hasattr(ziwei_chart, "get")
                else getattr(ziwei_chart, "soul", None)
            )
            body_palace = (
                ziwei_chart.get("body") if hasattr(ziwei_chart, "get")
                else getattr(ziwei_chart, "body", None)
            )
            engine_evidences["ZI_WEI"].append(
                EngineEvidence(
                    evidence_id="ZW-CHART-SOUL",
                    engine=EngineName.ZI_WEI,
                    rule_id="ZW_SOUL_PALACE_MAIN",
                    value=str(soul_palace) if soul_palace else "UNKNOWN",
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "soul_palace_main_star_zh": str(soul_palace) if soul_palace else "",
                        "body_palace_main_star_zh": str(body_palace) if body_palace else "",
                    },
                    source_rule_ref="data/rules/zw_soul_palace.json",
                    source_field="soul_palace_main_star_zh",
                )
            )

        # Add signal-based evidence
        # 修复 P0: 根据 signal.source_engine 路由到 ZI_PING / ZI_WEI (而不是硬编码 ZI_PING)
        for layer, sigs in signals.items():
            for sig in sigs:
                # 优先用 signal 自带的 engine 字段；其次根据 rule_refs 前缀判断
                raw_eng = getattr(sig, "source_engine", None) or getattr(sig, "engine", None)
                if raw_eng is None:
                    # 从 rule_refs 前缀推断: ZW-* → ZI_WEI, 其余 ZI_PING
                    rule_refs = getattr(sig, "rule_refs", []) or []
                    raw_eng = "ZI_WEI" if any(str(r).startswith("ZW-") for r in rule_refs) else "ZI_PING"
                engine_name = str(raw_eng)
                if engine_name not in engine_evidences:
                    engine_evidences[engine_name] = []
                # Derive temporal_scope from signal layer (P1.6 fix)
                temporal = {
                    "BASELINE": TemporalScope.BIRTH,
                    "CYCLE_CONTEXT": TemporalScope.YEAR,
                    "DAILY_ACTIVATION": TemporalScope.DAY,
                }.get(layer, TemporalScope.BIRTH)
                engine_evidences[engine_name].append(
                    EngineEvidence(
                        evidence_id=sig.signal_id,
                        engine=EngineName(engine_name),
                        rule_id=sig.rule_refs[0] if sig.rule_refs else sig.signal_id,
                        value=sig.ontology_type,
                        temporal_scope=temporal,
                        attributes={"ontology_type": sig.ontology_type, "layer": layer},
                        source_rule_ref=sig.rule_refs[0] if sig.rule_refs else "",
                        source_field="",
                    )
                )

        # Map Evidence → SemanticAtom
        def atom_fn(ev: EngineEvidence) -> SemanticAtom | None:
            attrs = ev.attributes
            # P1.6: Handle ten_god evidence for production rule matching
            ten_god = attrs.get("ten_god")
            if ten_god:
                ten_god_map = {
                    "比肩": "TEN_GOD_BI_JIAN",
                    "劫财": "TEN_GOD_JIE_CAi",
                    "食神": "TEN_GOD_SHI_SHEN",
                    "伤官": "TEN_GOD_SHANG_GUAN",
                    "偏财": "TEN_GOD_PIAN_CAi",
                    "正财": "TEN_GOD_ZHENG_CAi",
                    "七杀": "TEN_GOD_QI_SHA",
                    "正官": "TEN_GOD_ZHENG_GUAN",
                    "偏印": "TEN_GOD_PIAN_YIN",
                    "正印": "TEN_GOD_ZHENG_YIN",
                }
                atom_id = ten_god_map.get(ten_god, f"TEN_GOD_{ten_god}")
                return SemanticAtom(
                    atom_id=atom_id,
                    engine=ev.engine,
                    evidence_ref=ev.evidence_id,
                    semantic_keys=[ten_god],
                    domain_candidates=["GROWTH", "FINANCE"],
                    label_zh=ten_god,
                    category="TEN_GOD",
                )
            # Fallback: signal-based evidence
            atom_id = f"{ev.engine.value}_{attrs.get('ontology_type', 'UNKNOWN')}"
            return SemanticAtom(
                atom_id=atom_id,
                engine=ev.engine,
                evidence_ref=ev.evidence_id,
                semantic_keys=[attrs.get("ontology_type", "")],
                domain_candidates=["CAREER", "FINANCE", "GROWTH"],
                label_zh=attrs.get("ontology_type", ""),
                category="",
            )

        return self._orchestrator.orchestrate(
            case_id="pipeline",
            temporal_scope="birth",
            engine_evidences=engine_evidences,
            atom_map_fn=atom_fn,
        )

    # ─── P1.7: Temporal Convergence ────────────────────────────────────────────

    @staticmethod
    def _map_signal_to_temporal(
        sig, layer: str, target_year: int, engine_name: str
    ) -> TemporalSignal | None:
        """Convert a production Signal → TemporalSignal for convergence engine."""
        _DIR_MAP = {
            "INCREASE": "POSITIVE",
            "DECLINE": "NEGATIVE",
            "STABLE": "NEUTRAL",
            "VOLATILE": "CHANGE",
        }
        _STRENGTH_MAP = {"low": 0.3, "moderate": 0.5, "high": 0.7}
        _GRAN_MAP = {
            "DAILY_ACTIVATION": TemporalGranularity.DAILY,
            "CYCLE_CONTEXT": TemporalGranularity.YEARLY,
            "BASELINE": TemporalGranularity.YEARLY,
        }

        direction = _DIR_MAP.get(sig.direction, "UNKNOWN")
        try:
            strength = float(sig.strength)
        except (TypeError, ValueError):
            strength = _STRENGTH_MAP.get(sig.strength, 0.5)
        granularity = _GRAN_MAP.get(layer, TemporalGranularity.YEARLY)

        return TemporalSignal(
            signal_id=sig.signal_id,
            engine=engine_name,
            prediction_window=PredictionWindow(
                start_year=target_year,
                end_year=target_year,
                granularity=granularity,
            ),
            direction=direction,
            strength=max(0.0, min(1.0, strength)),
            provenance=f"{sig.ontology_type}@{layer}",
        )

    def _run_temporal_convergence(
        self, signals: dict[str, list], analysis_date: date
    ) -> Any:
        """Map all signals → TemporalSignal and run convergence engine."""
        if self._temporal_convergence_engine is None:
            return None
        engine = self._temporal_convergence_engine
        added = 0
        for layer, sigs in signals.items():
            # Use domain-derived engine name from first signal
            engine_name = sigs[0].system if sigs and hasattr(sigs[0], "system") and sigs[0].system else "Shuntian"
            for sig in sigs:
                ts = self._map_signal_to_temporal(sig, layer, analysis_date.year, engine_name)
                if ts is not None:
                    if engine.add_signal(ts):
                        added += 1
        if added == 0:
            return None
        return engine.compute_convergence()

    def _extract_authorizations(self, cross_result) -> list[dict]:
        """Extract authorized assertions from CrossDomainResult with Rule direction.

        P1.6 fix: look up rule by (domain, semantic) to get real direction.
        """
        assertions = []
        if cross_result is None:
            return assertions
        # Map assertion_id → evidence_id from CrossDomainResult.by_engine (EngineEvidenceSet.evidence_ids).
        # Coverage's EngineAssertionSet only carries assertion_ids (no evidence_ids), so we cross-reference by_engine.
        evidence_id_map: dict[str, str] = {}
        for engine_name, eng_set in cross_result.by_engine.items():
            for idx, aid in enumerate(eng_set.assertion_ids):
                if idx < len(eng_set.evidence_ids):
                    evidence_id_map[aid] = eng_set.evidence_ids[idx]
        for domain, domain_index in cross_result.coverage.coverage.items():
            for semantic, ds_index in domain_index.items():
                for engine_name, eng_set in ds_index.by_engine.items():
                    for assertion_id in eng_set.assertion_ids:
                        # Look up rule from production library to get real direction
                        rule = None
                        if self._assertion_library is not None:
                            from ..spec.canonical import SemanticAtom, EngineName as EN
                            atom = SemanticAtom(
                                atom_id=semantic, engine=EN(engine_name),
                                evidence_ref=f"AS-{assertion_id}", semantic_keys=[semantic],
                                domain_candidates=[domain], label_zh="", category="",
                            )
                            rule = self._assertion_library.find_rule(atom, {})
                        assertions.append({
                            "assertion_id": assertion_id,
                            "engine": engine_name,
                            "domain": domain,
                            "semantic": semantic,
                            "authorized_rule_id": rule.rule_id if rule else None,
                            "rule_direction": rule.direction.value if rule else "UNKNOWN",
                            "authorization_source": "CrossDomainOrchestrator",
                            "evidence_id": evidence_id_map.get(assertion_id, assertion_id),
                        })
        return assertions

    def _build_claims_from_assertions(self, theme: str, assertions: list[dict]) -> list[dict]:
        """Build claims from authorized assertions. direction comes from Rule, not Signal.

        P1.6 boundary: claims from authorized assertions only.
        No signal.direction bypass.
        """
        claims = []
        for auth in assertions:
            claims.append({
                "claim_id": f"AC-{auth['assertion_id']}",
                "assertion_id": auth["assertion_id"],
                "authorized_rule_id": auth.get("authorized_rule_id"),
                "signal_type": auth.get("domain", "UNKNOWN"),
                "claim": f"主体在 {theme} 主题上经 [{auth['authorization_source']}] 授权。",
                "direction": auth.get("rule_direction", "UNKNOWN"),
                "strength": "AUTHORIZED",
                "source_layers": [auth["engine"]],
                "rule_refs": [auth["assertion_id"]],
                "evidence_refs": [auth["evidence_id"]] if auth.get("evidence_id") else [auth["assertion_id"]],
            })
        return claims
