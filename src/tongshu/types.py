"""TONGSHU 公共类型层 — Stage 间数据协议。

本模块是 pipeline 重构的底座（pipeline-blueprint.md 步骤 1）。所有 Stage 间的
数据传递都通过本模块的 frozen dataclass，避免 Stage 之间循环 import，并保证
Stage 接口契约明确。

层级关系（所有路径相对 backend/src/tongshu/）：

    types.py (本模块，公共类型)
      ↑
      │   只读依赖（frozen dataclass / 协议对象）
      │
      ├─ engines/bazi_engine.py       (BaziChart)
      ├─ engines/ziwei_engine.py      (ZiweiChart)
      ├─ engines/huangli_engine.py    (HuangliDay)
      ├─ reasoning/signal_engine.py   (Signal)
      ├─ reasoning/cross_analysis.py  (CrossResult)
      ├─ canonical/composer.py        (CanonicalContent)
      ├─ validation/layer1.py         (Layer1Result)
      ├─ validation/layer2.py         (Layer2Result)
      ├─ validation/layer3.py         (Layer3Result)
      └─ audit/gates.py               (GateResult)

Stage 实现（步骤 3 引入）只 import 本模块；Stage 之间禁止互相 import。

公开 dataclass：

    ComputeResult         — Stage 1-6 输出（计算 + SIR）
    RenderStageResult     — Stage 7-8 输出（渲染 + fallback）
    ValidationStageResult — Stage 9 输出（3 层 + 4 Gate + fail-closed）
    PipelineInputs        — pipeline 顶层入参（解耦 kwargs）
    PipelineStage         — Literal 枚举（标识 Stage 类型，便于日志/调试）

向后兼容：本模块纯加法，不修改任何现有 dataclass。已通过单测 + Golden 验证
pipeline.py 仍可直接使用 PipelineResult（其构造保持原样）。

Author: Codex
Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Literal

# 引擎输出（frozen dataclass）
from .engines.bazi_engine import BaziChart
from .engines.ziwei_engine import ZiweiChart
from .engines.huangli_engine import HuangliDay

# 推理层（frozen dataclass）
from .reasoning.signal_engine import Signal

# SIR（frozen dataclass）
from .canonical.composer import CanonicalContent

# 验证层 + Gate（frozen dataclass）
from .validation.layer1 import Layer1Result
from .validation.layer2 import Layer2Result
from .validation.layer3 import Layer3Result
from .audit.gates import GateResult

if TYPE_CHECKING:  # 仅类型检查时引用，运行时无开销
    # render/renderer.py 中的 RenderResult 是非 frozen dataclass；
    # 在本模块中只作为类型注解使用，不在运行时实例化。
    from .render.render_request import RenderRequest
    from .render.renderer import RenderResult as LLMResult


# ----------------------------------------------------------------------
# Literal aliases（语义清晰 + IDE 自动补全）
# ----------------------------------------------------------------------

RenderSource = Literal["llm_renderer", "template_fallback", "computed"]
PipelineStageName = Literal["compute", "render", "validate", "audit"]


# ----------------------------------------------------------------------
# Stage 1-6 输出：纯计算 + SIR 构造
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ComputeResult:
    """阶段 1-6 的纯计算产出。

    含义：仅承载 engines + reasoning + canonical 三层结果。
    不含渲染、校验、审计——这些由后续 Stage 各自承担。

    BUG-P0-03 修复：新增 heluo_result / yi_structure / yi_interpretation 字段，
    使河洛引擎和易经解释引擎的结果进入主 Pipeline。
    """

    # 1. 引擎层原始输出
    bazi_chart: BaziChart
    ziwei_chart: ZiweiChart
    huangli_day: HuangliDay

    # 2. 信号提取（三层）
    signals: dict[str, list[Signal]]

    # 3. atomic_claims（mapping_refs 附加）
    atomic_claims: list[dict]

    # 5. SIR 构造 + schema 校验
    canonical: CanonicalContent
    canonical_schema_valid: bool
    canonical_schema_errors: tuple[str, ...]

    # 调试辅助
    computed_at: datetime

    # 6. 河洛 + 易经引擎输出（BUG-P0-03 新增，可选以保持向后兼容）
    heluo_result: Any = None          # HeluoResult | None
    yi_structure: Any = None          # YiStructure | None
    yi_interpretation: Any = None     # YiInterpretation | None
    canonical_signals: dict[str, list] = field(default_factory=dict)  # P1.3 dual-track

    # P1.6: CrossDomainOrchestrator 输出（None = 未接入生产路径）
    cross_result: Any = None          # CrossDomainResult | None
    # P1.6: 授权断言列表（来自 ProductionRuleLibrary.find_rule）
    authorized_assertions: list[dict] = field(default_factory=list)
    # P1.7: 时序收敛结果（None = 未接入或单层信号）
    temporal_convergence: Any = None  # TemporalConvergence | None
    # E7: 梅花易数引擎输出（可选项，None = 未启用）
    meihua_result: Any = None         # MeihuaResult | FeatureMapResult | None
    # 2026-10-08 接线：河洛诊断图与行动建议。
    # 这两层此前生产调用方为零，只在单测里被手动调过 → 真实排盘
    # 从来看不到它们。None = 未接入或该层降级（已记 warning）。
    heluo_diagnosis: Any = None      # DiagnosisResult | None
    heluo_guidance: Any = None       # HeluoGuidance | None

    # BZ-FNDR-15 (⑮-0 接入契约): CanonicalBaziChart 字段.
    # 由 compute_stage 内部通过 CanonicalBaziChart.from_bazi_chart(bazi_chart) 构造,
    # 自动登记 provenance=from_bazi_chart. 下游 Ziping 入口必须消费此字段
    # (而非直接 bazi_chart), 并在消费前调 assert_canonical_gate(require_factory=True).
    # 类型注解延迟到运行时 (CanonicalBaziChart 依赖 bazi_engine, 不在 types 模块顶层引用).
    canonical_bazi_chart: Any = None  # CanonicalBaziChart | None

    @property
    def signal_counts(self) -> dict[str, int]:
        """BASELINE/CYCLE_CONTEXT/DAILY_ACTIVATION 三层信号数。"""
        return {layer: len(sigs) for layer, sigs in self.signals.items()}


# ----------------------------------------------------------------------
# Stage 7-8 输出：渲染 + 模板回退
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RenderStageResult:
    """阶段 7-8 的渲染产出。

    rendered=None 表示硬失败（已回退到模板或空文本，rendered_text 兜底）。
    source='computed' 仅在 compute_only 模式下使用（不调 LLM）。
    """

    # RenderRequest 不可序列化（在 frozen 中存 dict 形态）
    render_request_dict: dict[str, Any]

    # LLM 客户端原始输出（None = 渲染失败 / compute_only）
    rendered: "LLMResult | None"

    # 最终输出文本（含 fallback / compute_only 占位）
    rendered_text: str

    # 输出来源（V3.6 §25 / pipeline.source 语义）
    source: RenderSource

    # 渲染耗时（ms）；None = 未渲染（compute_only 或硬失败）
    render_elapsed_ms: float | None


# ----------------------------------------------------------------------
# Stage 9 输出：3 层校验 + 4 Gate + fail-closed
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationStageResult:
    """阶段 9 的校验产出。

    passed = l1 ∧ l2 ∧ l3 ∧ G1 ∧ G2 ∧ G3 ∧ G4
    """

    layer1: Layer1Result | None
    layer2: Layer2Result | None
    layer3: Layer3Result | None
    gates: tuple[GateResult, ...]
    passed: bool
    # G0-2 (INT-03): 本运行通过 G1 的资源级 provenance 统计
    provenance_summary: dict[str, int] = None


# ----------------------------------------------------------------------
# pipeline 顶层入参（解耦 kwargs 顺序依赖）
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineInputs:
    """pipeline.run() 的全部入参聚合体。

    引入目的：
      - 解耦调用方对参数顺序的依赖
      - 便于 Stage 间传递同一入参对象（无需复制字段）
      - 后续若新增入参，只改本 dataclass 不影响 Stage 接口

    注：本 dataclass 当前未替代 kwargs 入参（保持公共 API 不变），
    仅作为文档化类型 + Stage 内部传递使用。
    """

    analysis_date: date
    birth_date: tuple[int, int, int, int]  # (Y, M, D, H)
    gender: Literal["male", "female"]
    theme: str

    # 可选（compute_only / forbidden_inferences / trace_id）
    compute_only: bool = False
    forbidden_inferences: tuple[dict, ...] = ()
    trace_id: str | None = None

    # 元数据
    request_id: str | None = None  # 内部生成若为 None

    def with_request_id(self, request_id: str) -> "PipelineInputs":
        """返回带 request_id 的新实例（frozen dataclass 用 replace 模式）。"""
        from dataclasses import replace
        return replace(self, request_id=request_id)


# ----------------------------------------------------------------------
# 公共导出
# ----------------------------------------------------------------------

__all__ = [
    # Literal aliases
    "RenderSource",
    "PipelineStageName",
    # Stage 结果 dataclass
    "ComputeResult",
    "RenderStageResult",
    "ValidationStageResult",
    # 顶层入参
    "PipelineInputs",
    # 重导出（方便调用方）
    "BaziChart",
    "ZiweiChart",
    "HuangliDay",
    "Signal",
    "CanonicalContent",
    "Layer1Result",
    "Layer2Result",
    "Layer3Result",
    "GateResult",
]
