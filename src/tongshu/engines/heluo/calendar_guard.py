# -*- coding: utf-8 -*-
"""历法口径自检（calendar_guard.py）。

为什么需要这个模块
------------------

**1582 年（格里历改历）之前，sxtwl 的节气儒略日给出的是「儒略历」日期**，
而仓库通用换算 ``tongshu.engines.time.jd_converter.jd_to_datetime`` 按
**proleptic Gregorian** 换算 —— 两者在 1150 / 1206 这类年份**相差 7 天**
（1150 年实测：sxtwl 标 大雪=1150-11-30 19:06，jd_to_datetime 标 1150-12-07 19:06）。

后果（**已实测，不改他域代码**）：
八字引擎用 ``jd_to_datetime`` 做「节」边界比较，故 1582 年前的出生日，
其**月柱 / 立春年柱边界整体后移 7 天**（日柱不受影响：日干支由 sxtwl 的连续
日序给出，与标签历法无关）。例：1206-11-30 21:00（sxtwl 儒略历），
原典《河洛真数》L186 判作「丙寅 庚子 丙子 己亥」（子月），八字引擎因
上述 7 日错位判成「丙寅 己亥 丙子 己亥」（亥月）。

本模块的职责边界
----------------

* **不修正**任何外部引擎（八字 / 时间域不在河洛职责内）——只如实报告。
* 在河洛侧把口径差异**显式留痕**：错位或被换算过的输入被当成真实输入，
  比答错更坏（与「出生年占位留痕」同一原则）。

口径规则（可在守卫中逐条回查）
--------------------------------

1. 河洛的农历/节气链一律以 **sxtwl** 为准（``canonical._jie_by_batch``、
   ``jiehhou`` 均用 ``sxtwl.JD2DD``，即 1582 年前为儒略历）。
2. 古 dates 的公历标签若按 proleptic Gregorian 换算，会与 sxtwl 差
   ``Y//100 - Y//400 - 2`` 天（1150/1206 年 = 7 天，1500 年 = 10 天）。
3. 日柱必须与 sxtwl 自算一致；不一致即判定为**换算口径问题**。
4. 月柱/日柱在**交节当日**与 sxtwl 整日口径天然可能差一柱（八字引擎按
   节气精确时刻切分，sxtwl 按整日给出），此类属正常边界差异，不报。
"""
from __future__ import annotations

from typing import Any, Sequence

__all__ = [
    "check_calendar_consistency",
    "julian_gregorian_offset",
    "sxtwl_pillars",
]

_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"


def julian_gregorian_offset(year: int, month: int, day: int) -> int:
    """1582-10-15 之前，儒略历标签与 proleptic 格里历标签相差的天数。

    标准公式 ``Y//100 - Y//400 - 2``（3 月起算，2 月及以前归上一年）。
    1582-10-15（格里历）之后两者一致，返回 0。

    实测锚点：1150 年 = 7 天、1206 年 = 7 天、1500 年 = 10 天。
    """
    if (year, month, day) >= (1582, 10, 15):
        return 0
    y = year - 1 if month <= 2 else year
    return y // 100 - y // 400 - 2


def sxtwl_pillars(birth_date: str) -> dict[str, str] | None:
    """按 sxtwl（1582 年前 = 儒略历）自算该公历日的四柱。

    返回 ``{"year":..., "month":..., "day":..., "hour":...}``；缺 hour 时
    hour 给 None。sxtwl 不可用或日期非法时返回 None（调用方按「不判」处理）。
    """
    try:
        import sxtwl
    except ImportError:                      # pragma: no cover - 依赖缺失
        return None
    try:
        y, m, d = (int(x) for x in str(birth_date)[:10].split("-"))
    except Exception:
        return None
    try:
        day = sxtwl.fromSolar(y, m, d)
    except Exception:
        return None
    ygz, mgz, dgz = day.getYearGZ(), day.getMonthGZ(), day.getDayGZ()
    out = {
        "year": _GAN[ygz.tg] + _ZHI[ygz.dz],
        "month": _GAN[mgz.tg] + _ZHI[mgz.dz],
        "day": _GAN[dgz.tg] + _ZHI[dgz.dz],
        "hour": None,
    }
    return out


def _is_jie_day(birth_date: str) -> bool:
    """该公历日是否含「节」（奇数索引）。交节当日属边界差异，不报。"""
    try:
        import sxtwl
    except ImportError:                      # pragma: no cover - 依赖缺失
        return False
    try:
        y, m, d = (int(x) for x in str(birth_date)[:10].split("-"))
        day = sxtwl.fromSolar(y, m, d)
    except Exception:
        return False
    try:
        jq = day.getJieQi()
    except Exception:
        return False
    return jq >= 0 and jq % 2 == 1


def check_calendar_consistency(
    bazi: Sequence[Any] | None,
    birth_date: str,
) -> list[str]:
    """比对输入四柱与 sxtwl 自算四柱，返回留痕文字（空列表 = 无异常）。

    参数
    ----
    bazi: ``[(年干,年支), (月干,月支), (日干,日支), (时干,时支)]``；
          允许只给前三柱。``None`` / 长度不足 → 不判（返回 []）。
    birth_date: 公历日期字符串 ``YYYY-MM-DD``（**按 sxtwl 口径**：1582 年前
          为儒略历标签）。

    返回
    ----
    ``list[str]``：每条一行证据文字；无异常时为空列表。
    """
    if not bazi or len(bazi) < 3 or not birth_date:
        return []
    try:
        y, m, d = (int(x) for x in str(birth_date)[:10].split("-"))
    except Exception:
        return []

    mine = sxtwl_pillars(birth_date)
    if mine is None:
        return []

    notes: list[str] = []
    offset = julian_gregorian_offset(y, m, d)
    era_note = (
        f"（该日期在格里历改历前，sxtwl 用儒略历标签，"
        f"与 proleptic Gregorian 相差 {offset} 天）"
        if offset else ""
    )

    def _pair(i: int) -> str:
        try:
            g, z = bazi[i][0], bazi[i][1]
        except Exception:
            return ""
        return f"{g}{z}"

    # ① 日柱：必须一致，不一致 = 换算口径问题
    in_day, sxtwl_day = _pair(2), mine["day"]
    if in_day and sxtwl_day and in_day != sxtwl_day:
        notes.append(
            f"  历法口径自检：**日柱不一致**（输入 {in_day}，sxtwl 自算 {sxtwl_day}）"
            f"—— 公历换算口径与河洛节气链（sxtwl）不同，{era_note}"
            "；日柱一错，支数、卦、元堂、判词整条链全错，请核对该出生日期的历法口径。"
        )

    # ② 月柱：交节当日允许差一柱（整日口径 vs 精确时刻口径），其余报差异
    in_month, sxtwl_month = _pair(1), mine["month"]
    if (in_month and sxtwl_month and in_month != sxtwl_month
            and not _is_jie_day(birth_date)):
        notes.append(
            f"  历法口径自检：月柱不一致（输入 {in_month}，sxtwl 节气月 {sxtwl_month}），"
            f"且该日非交节日 —— {era_note}"
            "；月柱错则月令、得时、化工及流月链判词随之偏差。"
        )

    # ③ 年柱：立春年界同理，交节当日不报
    in_year, sxtwl_year = _pair(0), mine["year"]
    if (in_year and sxtwl_year and in_year != sxtwl_year
            and not _is_jie_day(birth_date)):
        notes.append(
            f"  历法口径自检：年柱不一致（输入 {in_year}，sxtwl 立春年 {sxtwl_year}），"
            f"且该日非交节日 —— {era_note}；年柱错则三元寄宫与流年干支随之偏差。"
        )

    return notes
