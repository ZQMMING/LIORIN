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

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from .engines.bazi_adapter import BaziAdapter
from .engines.bazi_engine import BaziChart, BaziEngine, BRANCH_CN, STEM_CN
from .engines.heluo.canonical import (
    HeluoCanonical, HeluoResult, resolve_jieqi_window,
)

if TYPE_CHECKING:                     # pragma: no cover
    from .engines.time.calculation_context import CalculationContext

#: 性别类型（下游八字引擎只接受这两个字面量）
Gender = Literal["male", "female"]

#: 河洛默认使用的时区（与 canonical 构造 HeluoInput 时一致）
HELUO_TZ = "Asia/Shanghai"


def now_beijing() -> datetime:
    """当前北京时间（带 tzinfo）。

    河洛的流日卦按**当前日期**自动推算，故取数须有明确时区口径，
    避免服务器时区/夏令时造成「今天」漂移。
    """
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(HELUO_TZ))
    except Exception:                                  # pragma: no cover
        return datetime.now()


def resolve_target_date(
    target_date: Optional[str] = None,
    target_year: Optional[int] = None,
    target_month: Optional[int] = None,
    target_day: Optional[int] = None,
    now: Optional[datetime] = None,
) -> tuple[int, int, int]:
    """解析流日卦的**目标日**（公历年, 月, 日）。

    优先级：
      1. 显式 ``target_date``（公历 ``YYYY-MM-DD``）；
      2. 显式 ``(target_year, target_month, target_day)`` 三者齐全；
      3. **今天**（北京时间）—— 生产默认：河洛的流日卦按当前日期自动推算。

    ⚠ 只在**三者齐全**时才用第 2 条；若只给了 target_year（如 fast-path 只算
    某年），仍以「今天」的月日为准补齐，避免「年对了、月日错位」这种半截输入。
    """
    if target_date:
        y, m, d = (int(x) for x in str(target_date)[:10].split("-"))
        return y, m, d
    now = now or now_beijing()
    if target_year is not None and target_month is not None and target_day is not None:
        return target_year, target_month, target_day
    return (target_year if target_year is not None else now.year,
            target_month if target_month is not None else now.month,
            target_day if target_day is not None else now.day)


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


#: 合法的性别取值（下游八字引擎只接受这两个）
GENDERS = ("male", "female")

#: 常见别名 → 规范值（大小写/简写容错，避免在深处才炸）
_GENDER_ALIASES = {
    "male": "male", "m": "male", "man": "male", "boy": "male", "男": "male",
    "female": "female", "f": "female", "woman": "female", "girl": "female",
    "女": "female",
}


def _normalize_gender(gender: Optional[str]) -> Gender:
    """性别值归一 + **显式报错**。

    ⚠ 2026-10-25：本层签名是 ``gender: str``，而下游八字引擎只接受
      ``Literal["male", "female"]`` ⇒ 传 ``"Male"`` / ``"M"`` / ``""`` 会在
      **深处**才出错，报错与真正的错因相距很远（难以定位）。
      ⇒ 在**入口**归一并对非法值显式报错。

    Raises:
        ValueError: 性别值既非规范值也无已知别名。
    """
    if gender is None:
        return "male"
    raw = str(gender).strip().lower()
    if raw in _GENDER_ALIASES:
        norm: Gender = _GENDER_ALIASES[raw]      # type: ignore[assignment]
        return norm
    raise ValueError(
        "性别值不合法：%r（合法值 %s；常见别名如 M/F/男/女 亦可）"
        % (gender, "/".join(GENDERS))
    )


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
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        target_day: Optional[int] = None,
        target_date: Optional[str] = None,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
        """独立入口：公历出生日期 → 排盘（八字引擎）→ 河洛。

        ``target_date``（公历 ``YYYY-MM-DD``）= **流日卦的取用日**；
        不传则按**当前日期（北京时间）**自动推算（用户裁决：「流日卦…根据当前
        日期自动算」）。显式 ``target_year/month/day`` 三者齐全时优先。

        ⚠ ``gender`` 在本层**显式校验**（见 :func:`_normalize_gender`）：
          下游八字引擎只接受 ``"male"`` / ``"female"``，而本层签名是 ``str``
          ⇒ 传 ``"Male"`` / ``"M"`` / ``"unknown"`` 会在**深处**才炸，
          报错信息与真正的错因（性别值不合法）相距很远。
          ⇒ 归一 + 显式报错（缺失被当成正常，比答错更坏）。
        """
        chart = self._bazi_engine.compute(
            solar_date,
            gender=_normalize_gender(gender),
            skip_late_zi=False,  # 独立入口由 BaziEngine 内部处理夜子时
            birth_datetime=birth_datetime,
        )
        return self.compute_from_chart(
            chart,
            target_year=target_year,
            target_month=target_month,
            target_day=target_day,
            target_date=target_date,
            huangli_provider=huangli_provider,
        )

    # ------------------------------------------------------------------
    # 正式链路：CalculationContext → BaziAdapter → 河洛
    # ------------------------------------------------------------------
    def compute_from_context(
        self, ctx: "CalculationContext", gender: Optional[str] = None,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
        g = _normalize_gender(gender or getattr(ctx, "subject_gender", None)
                              or "male")
        chart = self._bazi_adapter.compute(ctx, gender=g)
        return self.compute_from_chart(chart, huangli_provider=huangli_provider)

    # ------------------------------------------------------------------
    # BaziChart → 河洛（核心投影转发）
    # ------------------------------------------------------------------
    def compute_from_chart(
        self,
        chart: BaziChart,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        target_day: Optional[int] = None,
        target_date: Optional[str] = None,
        huangli_provider: Optional[object] = None,
    ) -> HeluoResult:
        # 流日卦的取用日：显式 target_date > 显式三元 > **今天（北京时间）**
        _ty, _tm, _td = resolve_target_date(
            target_date, target_year, target_month, target_day)
        # ⚠ 2026-10-24 真缺陷修复：resolve_target_date 返回的是**公历**月日，
        #   而河洛日卦层的内部契约是**节气月序 + 自节起的日序**
        #   （canonical.calculate 的 target_month/target_day 即此义）。
        #   两者口径不同：公历 10 月 ≠ 节气/农历十月（十月 = 立冬月，11/7 起）。
        #   此前 adapter 直接透传 ⇒ 顶层 daily_hexagram 取的是**别的月**的日卦：
        #   实测 target_date=2026-10-23（寒露后第 16 日，属九月/寒露月）
        #   被算成**十月/立冬月**的段，date_from=2026-11-25 —— 与目标日相差 33 天。
        #   现按节气窗口换算（换算规则与原典依据见 canonical.resolve_jieqi_window）。
        _solar_date = f"{_ty:04d}-{_tm:02d}-{_td:02d}"
        _win = resolve_jieqi_window(_ty, _tm, _td)
        _cal_note = ""
        target_jie_year: Optional[int] = None
        if _win.get("ok"):
            target_month = int(_win["month"])
            target_day = int(_win["day"])
            target_jie_year = int(_win["year"])
        else:
            # 节气表不可用（sxtwl 缺失）⇒ 无法换算。
            # 不静默换口径：退回旧口径并**显式留痕**（缺失被当成正常，比答错更坏）。
            _cal_note = (
                "⚠ 节气表不可用，流日层退回公历月日口径"
                f"（{_win.get('error') or '未知原因'}）—— 流日取用月/日不可信"
            )
        target_year = _ty
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
            era_source = "derived"          # 三元据真实出生年推导
        else:
            # 手动构造 chart 未带出生时间：年柱反推由河洛内部处理，era 回退默认
            birth_year = None
            birth_date = None
            # ⚠ 2026-10-24 审计修：此前此处静默回落 era="zhong" 且**不留来源标记**。
            #   era 决定寄宫对象（上元寄艮/坤、下元寄离/兑…），寄宫一变 →
            #   先天卦变 → 元堂变 → 后天卦变 → 全链判词全变；而下游无从判别
            #   这个 era 是真值还是兜底。现按 birth_year_source 的同一约定留痕。
            era_source = "fallback"         # **兜底**，非真实出生年推导

        era = sanyuan(birth_year) if birth_year is not None else "zhong"

        result = self._canonical.calculate(
            bazi=bazi,
            gender=chart.gender,
            birth_hour=birth_hour,
            era=era,
            era_source=era_source,
            birth_year=birth_year,
            birth_date=birth_date,
            target_year=target_year,
            target_month=target_month,
            target_day=target_day,
            # 公历原值 + 窗口所属年 + 口径留痕（2026-10-24）
            target_solar_date=_solar_date,
            target_jie_year=target_jie_year,
            target_date_note=_cal_note,
        )

        # H8: 解卦层（原典判词）挂载 — 独立于冻结的 calculate，防御性兜底
        #
        # ⚠ 2026-10-24 审计修：原为 `except Exception: pass` —— 解卦层失败时
        #   result.guajie 保持 None，**下游看到「没有判词」却无法分辨**
        #   「解卦层挂了」与「这盘本来就没判词」：缺失被当成正常，静默无痕。
        #   现按 guajie 层自身的披露格式（guajie.py:1859 `{"error": ...}`）
        #   挂上错误字典：不阻塞主链，但错误**显形**，调用方可据此判别。
        try:
            from .engines.heluo.guajie import build_guajie_from_result
            result = replace(result, guajie=build_guajie_from_result(
                result, bazi=bazi,
                target_year=target_year, target_month=target_month,
                target_day=target_day, huangli_provider=huangli_provider,
            ))
        except Exception as exc:
            # 不阻塞主链，但必须留痕（缺失被当成正常，比答错更坏）。
            result = replace(result, guajie={
                "error": f"guajie 构建失败: {type(exc).__name__}: {exc}",
            })

        # ★ 2026-10-24 解读层接线：六模块编排（平台信号/解读/指引/诊断/指标/卦象状态）
        #   此前这 6 个模块在 src/ 内**零生产调用方** —— 逻辑与单测都在，
        #   但生产链从不产出它们的输出 ⇒ 下游拿不到解读层结果。
        #   任一子块失败不阻塞主链，失败原因写入 interpretation["warnings"]。
        try:
            from .engines.heluo.interpretation_pipeline import build_interpretation
            result = replace(result, interpretation=build_interpretation(result))
        except Exception as exc:
            result = replace(result, interpretation={
                "warnings": [f"解读层编排失败: {type(exc).__name__}: {exc}"],
            })
        return result
