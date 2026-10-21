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

独立入口 compute() 与正式链路一致，内部经 TimeResolver 按出生地真太阳时排盘
（消除"民用时直排"路径），默认 location="北京" 保证不传时向后兼容；
正式链路入口 compute_from_context() 复用 BaziAdapter
（skip_late_zi=True，上游 TimeResolver 已完成 23:00 换日，避免双重换日）。
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Union

from .bazi_adapter import BaziAdapter
from .bazi_engine import BaziChart, BaziEngine, BRANCH_CN, STEM_CN
from .heluo.canonical import HeluoCanonical, HeluoResult
from .time.resolver import TimeResolver


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
    # 独立入口：直接公历日期 → 真太阳时排盘 → 河洛（测试/单用例）
    # ------------------------------------------------------------------
    def compute(
        self,
        solar_date: tuple[int, int, int, int],
        gender: str = "male",
        birth_datetime: Optional[datetime] = None,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        target_day: Optional[int] = None,
        location: str = "北京",
        timezone: Optional[str] = None,
        apparent_solar: bool = True,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
        # 与正式链路统一：经 TimeResolver 按出生地真太阳时排盘，
        # 不再用民用时直排（避免西部晚子时边界时柱错一个时辰）。
        y, m, d, h = solar_date[0], solar_date[1], solar_date[2], solar_date[3]
        minute: Optional[int] = None
        if birth_datetime is not None:
            minute = birth_datetime.minute
        if len(solar_date) > 4:
            minute = solar_date[4]  # 支持 5 元组 (y,m,d,h,minute)
        ctx = TimeResolver().resolve_context(
            birth_date=date(y, m, d),
            hour=h,
            minute=minute,
            timezone=timezone,
            location=location,
            apparent_solar=apparent_solar,
            gender=gender,
        )
        return self.compute_from_context(
            ctx,
            gender=gender,
            target_year=target_year,
            target_month=target_month,
            target_day=target_day,
            huangli_provider=huangli_provider,
        )

    # ------------------------------------------------------------------
    # 正式链路：CalculationContext → BaziAdapter → 河洛
    # ------------------------------------------------------------------
    def compute_from_context(
        self,
        ctx,
        gender: Optional[str] = None,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        target_day: Optional[int] = None,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
        g = gender or ctx.subject_gender or "male"
        chart = self._bazi_adapter.compute(ctx, gender=g)
        tsd = getattr(ctx, "true_solar_datetime", None)
        return self.compute_from_chart(
            chart,
            target_year=target_year,
            target_month=target_month,
            target_day=target_day,
            true_solar_datetime=tsd.isoformat() if tsd is not None else None,
            huangli_provider=huangli_provider,
        )

    # ------------------------------------------------------------------
    # BaziChart → 河洛（核心投影转发）
    # ------------------------------------------------------------------
    def compute_from_chart(
        self,
        chart: BaziChart,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        target_day: Optional[int] = None,
        true_solar_datetime: Optional[str] = None,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
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
            true_solar_datetime=true_solar_datetime,
            target_year=target_year,
            target_month=target_month,
            target_day=target_day,
        )

        # H8: 解卦层（原典判词）挂载 — 独立于冻结的 calculate，防御性兜底
        # 四层爻断：仅接流年/流月/流日（target_year/month/day），
        # 流时卦（target_hour）剥离不接——按爻管时段逐段展开运算量大，按需另行调用。
        try:
            from dataclasses import replace
            from .heluo.guajie import build_guajie_from_result
            result = replace(
                result,
                guajie=build_guajie_from_result(
                    result, bazi=bazi,
                    target_year=target_year,
                    target_month=target_month,
                    target_day=target_day,
                    huangli_provider=huangli_provider,
                ),
            )
        except Exception as _e:  # 解卦层失败不阻塞主链，但留痕（不再静默 pass）
            try:
                from dataclasses import replace
                result = replace(
                    result, guajie={"error": f"guajie 构建失败: {_e}"})
            except Exception:
                pass
        return result
