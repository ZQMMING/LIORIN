"""河洛适配层 — BaziChart / CalculationContext → HeluoCanonical.calculate。

正式数据流（V2 R-04）：
    TimeResolver.resolve_context() → CalculationContext
        → BaziAdapter.compute(ctx) → BaziChart
        → HeluoAdapter.compute_from_chart(chart) → HeluoResult

适配层职责（只做投影转发，不重写上游 BaziEngine / 河洛引擎）：
1. BaziChart 四柱（拼音 Pillar）→ 河洛中文干支元组 [(年干,年支), ...]
2. birth_hour = 时柱地支（中文）
3. birth_year / birth_date 从 chart.birth_datetime 提取（缺省回退 None）
4. era 自动推导：原典三元锚点（1864 上元 / 1924 中元 / 1984 下元，
   60 年一轮换、180 年一循环）——实现《河洛理数真正算法确认书 V1》§2.3 缺口

独立入口 compute() 直接吃公历日期排盘（skip_late_zi=False，由 BaziEngine 内部
处理夜子时换日）；正式链路入口 compute_from_context() 复用 BaziAdapter
（skip_late_zi=True，上游 TimeResolver 已完成 23:00 换日，避免双重换日）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from .bazi_adapter import BaziAdapter
from .bazi_engine import BaziChart, BaziEngine, BRANCH_CN, STEM_CN
from .heluo.canonical import HeluoCanonical, HeluoResult


# ============================================================================
# 三元自动推导（原典《遇五寄宫法》：上元甲子男艮女坤 / 中元甲子阴男阳女坤
# 阳男阴女艮 / 下元甲子男离女兑；60 年轮换，180 年循环）
# 锚点：1864 上元 → 1924 中元 → 1984 下元 → 2044 上元 → …
# 回查原典：1504(上) → 1564(中) → 1624(下) → 1684(上) → 1744(中) → 1804(下) ✓
# ============================================================================
def sanyuan(year: int) -> str:
    """出生公历年份 → 三元（shang / zhong / xia）。

    公式：offset = (year - 1864) % 180；<60 上元、<120 中元、其余下元。
    """
    offset = (year - 1864) % 180
    if offset < 60:
        return "shang"
    if offset < 120:
        return "zhong"
    return "xia"


class HeluoAdapter:
    """八字排盘 → 河洛理数 串接适配器。"""

    def __init__(
        self,
        bazi_engine: Optional[BaziEngine] = None,
        canonical: Optional[HeluoCanonical] = None,
    ) -> None:
        self._bazi_engine = bazi_engine or BaziEngine()
        self._bazi_adapter = BaziAdapter(self._bazi_engine)
        self._canonical = canonical or HeluoCanonical()

    # ------------------------------------------------------------------
    # 独立入口：直接公历日期排盘 → 河洛（测试/单用例）
    # ------------------------------------------------------------------
    def compute(
        self,
        solar_date: tuple[int, int, int, int],
        gender: str = "male",
        birth_datetime: Optional[datetime] = None,
    ) -> HeluoResult:
        chart = self._bazi_engine.compute(
            solar_date,
            gender=gender,
            skip_late_zi=False,  # 独立入口由 BaziEngine 内部处理夜子时
            birth_datetime=birth_datetime,
        )
        return self.compute_from_chart(chart)

    # ------------------------------------------------------------------
    # 正式链路：CalculationContext → BaziAdapter → 河洛
    # ------------------------------------------------------------------
    def compute_from_context(
        self, ctx, gender: Optional[str] = None
    ) -> HeluoResult:
        g = gender or ctx.subject_gender or "male"
        chart = self._bazi_adapter.compute(ctx, gender=g)
        return self.compute_from_chart(chart)

    # ------------------------------------------------------------------
    # BaziChart → 河洛（核心投影转发）
    # ------------------------------------------------------------------
    def compute_from_chart(self, chart: BaziChart) -> HeluoResult:
        bazi = [
            (
                STEM_CN[chart.year_pillar.heavenly_stem],
                BRANCH_CN[chart.year_pillar.earthly_branch],
            ),
            (
                STEM_CN[chart.month_pillar.heavenly_stem],
                BRANCH_CN[chart.month_pillar.earthly_branch],
            ),
            (
                STEM_CN[chart.day_pillar.heavenly_stem],
                BRANCH_CN[chart.day_pillar.earthly_branch],
            ),
            (
                STEM_CN[chart.hour_pillar.heavenly_stem],
                BRANCH_CN[chart.hour_pillar.earthly_branch],
            ),
        ]
        birth_hour = BRANCH_CN[chart.hour_pillar.earthly_branch]

        bd: Optional[datetime] = chart.birth_datetime
        if bd is not None:
            birth_year: Optional[int] = bd.year
            birth_date: Optional[str] = bd.date().isoformat()
        else:
            # 手动构造 chart 未带出生时间：年柱反推由河洛内部处理，era 回退默认
            birth_year = None
            birth_date = None

        era = sanyuan(birth_year) if birth_year is not None else "zhong"

        result = self._canonical.calculate(
            bazi=bazi,
            gender=chart.gender,
            birth_hour=birth_hour,
            era=era,
            birth_year=birth_year,
            birth_date=birth_date,
        )

        # H8: 解卦层（原典判词）挂载 — 独立于冻结的 calculate，防御性兜底
        try:
            from dataclasses import replace
            from .heluo.guajie import build_guajie_from_result
            result = replace(result, guajie=build_guajie_from_result(result, bazi=bazi))
        except Exception:
            pass  # 解卦层失败不阻塞主链
        return result
