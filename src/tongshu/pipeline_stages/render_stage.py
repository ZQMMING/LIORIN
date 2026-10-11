"""RenderStage — 阶段 7-8（渲染 + 模板回退）。

职责：
    7. 构造 RenderRequest（与 SIR meta / audit 共享 request_id）
    8. 调 Renderer（被禁用 → 永远走 TemplateFallback）

返回 RenderStageResult，包含最终输出文本与 source 标识。

设计要点：
    - rendered=None 表示硬失败（rendered_text 仍可经 TemplateFallback 兜底）
    - source 初始为 "llm_renderer"（成功后），失败时由下游 ValidationStage 决定
      是否切到 "template_fallback"——RenderStage 不主动降级（避免抢 ValidationStage 职责）
    - render_elapsed_ms 单位 ms；compute_only 模式下 RenderStage.run() 不被调用
      （由 pipeline.run() 在 compute_only 分支直接构造占位 RenderStageResult）

⚠ 2026-10-11 用户口径：删除 LLM 渲染路径——LLM API key 401（无效），
  LLM 渲染层整体下线。本阶段改为**直接走 TemplateFallback**：
    · 不调 self.renderer.render()（跳过 LLM 网络）
    · rendered 永远 None
    · rendered_text = TemplateFallback(theme, cross_status) 65-85 字符模板
    · source 永远 "template_fallback"
  Renderer 实例保留注入但本阶段不消费；其它 owner（如需恢复）仍可接回。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 3 C3)
Migrated from: pipeline.py:237-257（run() 阶段 7-8）
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from ..render.render_request import build_render_request
from ..render.renderer import Renderer
from ..render.template_fallback import TemplateFallback
from ..render.heluo_view_renderer import HeluoViewRenderer
from ..types import RenderStageResult

if TYPE_CHECKING:
    from .compute_stage import ComputeResult


log = logging.getLogger(__name__)


def yearly_target_year(compute, heluo_result) -> int | None:
    """推断大运当年用的年份。

    顺序：
    1. compute.render_input.analysis_date.year（如果有）
    2. heluo_result.timeline.yearly_hexagrams 里 yuantang/year 命中 2026 的
    3. 兜底：yearly[-1]['year']
    """
    # 1. compute 的元数据
    ri = getattr(compute, "render_input", None)
    if ri is not None:
        ad = getattr(ri, "analysis_date", None)
        if ad is not None:
            return ad.year
    # 2. 取 heluo_target_date 推导的 target_year——通过 guajie.liunian_year 推断
    gj = getattr(heluo_result, "guajie", None) or {}
    ly = gj.get("liunian_year")
    if ly:
        try:
            return int(str(ly))
        except Exception:
            pass
    # 3. 兜底取 yearly 末年
    yearly = getattr(getattr(heluo_result, "timeline", None), "yearly_hexagrams", None) or []
    if yearly:
        return yearly[-1].get("year")
    return None


class RenderStage:
    """阶段 7-8: 渲染 + 模板回退（compute_only 不走此 Stage）。

    2026-10-11 用户口径：渲染层接 HeluoResult 字段 → 用户视角中文。
    - 主路径：HeluoViewRenderer（六层卦象 + 解卦 + 诊断 + 建议 全量映射）
    - 兜底路径：TemplateFallback（无 heluo_result 或主路径产空时）
    - LLM 渲染路径下线（API key 401）
    """

    def __init__(
        self,
        renderer: Renderer,
        template_fallback: TemplateFallback,
    ) -> None:
        # renderer 实例仍保留注入（其它 owner 可恢复），但本阶段不消费。
        self.renderer = renderer
        self.template_fallback = template_fallback
        # 2026-10-11：HeluoResult 字段 → 用户视角中文 的映射层（视图层）
        self.heluo_view_renderer = HeluoViewRenderer()

    def run(
        self,
        compute: "ComputeResult",
        request_id: str,
        theme: str,
    ) -> RenderStageResult:
        """主路径：HeluoViewRenderer 映射 HeluoResult 字段；
        兜底：TemplateFallback 通用模板。"""
        canonical = compute.canonical

        # 7. Build Render Request
        render_request = build_render_request(
            canonical_id=canonical.canonical_id,
            canonical_schema_version=canonical.schema_version,
            theme=theme,
            request_id=request_id,
        )

        # 8. 渲染：HeluoViewRenderer → TemplateFallback
        t0 = time.monotonic()
        rendered_text = ""
        source = "template_fallback"

        # 主路径：把 HeluoResult 的解卦/诊断/建议映射成中文
        heluo_result = getattr(compute, "heluo_result", None)
        if heluo_result is not None:
            try:
                # 大运当年取 analysis_date.year；不传则兜底取 yearly 末年
                target_year = None
                # analysis_date 不在 render 上下文；compute 也不带——所以从
                # yearly[-1] 兜底（pipeline 实际跑的 heluo_target_date 已经在
                # canonical.calculate 中启用 fast-path，yearly 末年是合理近似）
                target_year = yearly_target_year(compute, heluo_result)
                mapped = self.heluo_view_renderer.render(
                    heluo_result, theme=theme, target_year=target_year)
                if mapped:
                    rendered_text = mapped
                    source = "helvo_view"
            except Exception as exc:  # noqa: BLE001 — 映射失败不阻断
                log.warning("HeluoViewRenderer failed (degrade to template): %s", exc)

        # 兜底：映射为空时给通用模板
        if not rendered_text:
            cross_status = self._derive_cross_status(compute.cross_result)
            fallback = self.template_fallback.render(theme, cross_status)
            rendered_text = fallback or ""
            source = "template_fallback"
        render_elapsed_ms = (time.monotonic() - t0) * 1000.0

        return RenderStageResult(
            render_request_dict=render_request.to_dict(),
            rendered=None,  # LLM 已下线，永不返回
            rendered_text=rendered_text,
            source=source,  # type: ignore[arg-type]
            render_elapsed_ms=render_elapsed_ms,
        )

    @staticmethod
    def make_computed() -> RenderStageResult:
        """compute_only 模式占位（pipeline.run() 在 compute_only 分支调用）。"""
        return RenderStageResult(
            render_request_dict={},
            rendered=None,
            rendered_text="",
            source="computed",
            render_elapsed_ms=None,
        )

    @staticmethod
    def _derive_cross_status(cross_result) -> str:
        """从 cross_result 派生 cross_status（与 pipeline.run() 阶段 9 派生口径一致）。

        M2 架构下 CrossDomainResult 无 status 字段，由 coverage 形态推导：
        - 全无证据 → INSUFFICIENT
        - 部分引擎有证据 → PARTIAL
        - 全引擎有证据 + coverage 非空 → ALIGNED

        2026-10-11 修：render_stage.run() 之前直接读 cross_result.status（不存在），
        AttributeError 把整个渲染兜底打挂；现在用派生口径，模板兜底可命中。
        """
        if cross_result is None:
            return "INSUFFICIENT"
        try:
            engines_with_evidence = sum(
                1 for eng_set in cross_result.by_engine.values()
                if eng_set.evidence_ids
            )
            engines_total = len(cross_result.by_engine)
            if engines_with_evidence == 0:
                return "INSUFFICIENT"
            if engines_with_evidence < engines_total:
                return "PARTIAL"
            if cross_result.coverage.total_assertions == 0:
                return "INSUFFICIENT"
            return "ALIGNED"
        except Exception:  # noqa: BLE001 — 派生失败兜底
            return "INSUFFICIENT"
