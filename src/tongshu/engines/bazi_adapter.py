"""Bazi Adapter (P0-14) — CalculationContext → Existing BaziEngine.

适配层职责:把 TimeResolver/CalculationContext 的标准时间事实投影成 BaziEngine
的输入 tuple。**BaziEngine 本身不负责** timezone / longitude correction / EoT /
date boundary resolution —— 这些全部由上游(TimeResolver, T4)完成。

八字使用出生地当地真太阳时：23:00 换时不换日，00:00 换日；
由 CalculationContext.bazi_view 承载。
(effective_date 已换日)。本适配器禁止重写 bazi_engine;只做投影转发。

公共链(pipeline)保持原样:本适配器独立验证,不接入 pipeline,确保
Golden 20/20 不被公共链变化破坏。

V2 R-04 Contract:
- birth_civil_datetime → civil_date → 年柱/月柱节气边界判断
- effective_date (via bazi_view) → day_idx → 日柱/时柱干支序号
- true_solar_datetime: deprecated，已从主路径移除
"""

from __future__ import annotations

from typing import Literal

from .bazi_engine import BaziChart, BaziEngine
from .time_resolver import CalculationContext


class BaziAdapter:
    """把 CalculationContext 的八字视图送入现有 BaziEngine。"""

    def __init__(self, engine: BaziEngine | None = None):
        self._engine = engine or BaziEngine()

    @property
    def engine(self) -> BaziEngine:
        return self._engine

    def compute(
        self, ctx: CalculationContext, gender: Literal["male", "female"] = "male"
    ) -> BaziChart:
        """用 bazi_view（00:00 换日的日+时）驱动现有引擎。

        bazi_view = (effective_date.y, m, d, effective_hour)。
        引擎收到已归一化日期;日柱由 sxtwl 按日期取,小时自动成为对应日期的时辰。

        skip_late_zi 为兼容参数；引擎各调用路径均采用 00:00 换日。

        V2 R-04: 传入 birth_civil_datetime（原始输入时间），用于节气边界判断。
        避免 effective_date 污染年柱/月柱的节气判断。
        """
        view = ctx.bazi_view
        # 使用 birth_civil_datetime（原始输入时间，北京时间）进行节气判断
        # 避免真太阳时与钟表时间混用导致的边界错误
        return self._engine.compute(
            view,
            gender=gender,
            skip_late_zi=True,
            birth_datetime=ctx.birth_civil_datetime,  # 传入钟表时间而非真太阳时
        )
