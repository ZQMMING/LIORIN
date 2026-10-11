"""RenderStage — 阶段 7-8（渲染 + 模板回退）。

职责：
    7. 构造 RenderRequest（与 SIR meta / audit 共享 request_id）
    8. 调用 Renderer（捕获 RenderClientError → TemplateFallback）

返回 RenderStageResult，包含最终输出文本与 source 标识。

设计要点：
    - rendered=None 表示硬失败（rendered_text 仍可经 TemplateFallback 兜底）
    - source 初始为 "llm_renderer"（成功后），失败时由下游 ValidationStage 决定
      是否切到 "template_fallback"——RenderStage 不主动降级（避免抢 ValidationStage 职责）
    - render_elapsed_ms 单位 ms；compute_only 模式下 RenderStage.run() 不被调用
      （由 pipeline.run() 在 compute_only 分支直接构造占位 RenderStageResult）

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
from ..render.clients.openai_compat import RenderClientError
from ..render.template_fallback import TemplateFallback
from ..types import RenderStageResult

if TYPE_CHECKING:
    from .compute_stage import ComputeResult


log = logging.getLogger(__name__)


class RenderStage:
    """阶段 7-8: 渲染 + 模板回退（compute_only 不走此 Stage）。"""

    def __init__(
        self,
        renderer: Renderer,
        template_fallback: TemplateFallback,
    ) -> None:
        self.renderer = renderer
        self.template_fallback = template_fallback

    def run(
        self,
        compute: "ComputeResult",
        request_id: str,
        theme: str,
    ) -> RenderStageResult:
        """执行渲染；硬失败 → rendered=None + rendered_text="",RenderStageResult 不主动降级。

        下游 ValidationStage 决定是否切到 template_fallback source。
        """
        canonical = compute.canonical

        # 7. Build Render Request (same request_id as the SIR meta / audit)
        render_request = build_render_request(
            canonical_id=canonical.canonical_id,
            canonical_schema_version=canonical.schema_version,
            theme=theme,
            request_id=request_id,
        )

        # 8. Render — a hard client failure (contract §7.4: transport error
        # or MAX_RETRIES exhausted) degrades to Template Fallback, never 500.
        t0 = time.monotonic()
        rendered = None
        try:
            rendered = self.renderer.render(
                sir=canonical.to_dict(),
                render_request=render_request.to_dict(),
            )
        except RenderClientError as e:
            log.warning("Renderer hard failure (contract §7): %s", e)
        render_elapsed_ms = (time.monotonic() - t0) * 1000.0

        # source 决策：rendered 不为 None → "llm_renderer"；失败 → TemplateFallback
        if rendered is not None:
            source: str = "llm_renderer"
            rendered_text = rendered.text
        else:
            # 硬失败：模板回退兜底（即使 ValidationStage 没要求，也保证非空）
            fallback = self.template_fallback.render(theme, compute.cross_result.status if compute.cross_result else None)
            rendered_text = fallback or ""
            source = "template_fallback" if rendered_text else "template_fallback"

        return RenderStageResult(
            render_request_dict=render_request.to_dict(),
            rendered=rendered,
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
