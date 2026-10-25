# -*- coding: utf-8 -*-
"""历法口径自检（calendar_guard.py）。

为什么需要这个模块
------------------

**1582 年（格里历改历）之前，sxtwl 的节气儒略日给出的是「儒略历」日期**，
而仓库通用换算 ``heluo_engine.engines.time.jd_converter.jd_to_datetime`` 按
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
    "authoritative_year_month",
    "resolve_year_month",
]

_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"

#: 时辰 → 该时辰的起止小时（子时跨夜：23:00→次日 01:00）
_SHICHEN_WINDOW: dict[str, tuple[int, int]] = {
    "子": (23, 25), "丑": (1, 3), "寅": (3, 5), "卯": (5, 7), "辰": (7, 9),
    "巳": (9, 11), "午": (11, 13), "未": (13, 15), "申": (15, 17),
    "酉": (17, 19), "戌": (19, 21), "亥": (21, 23),
}


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


# ═══════════════════════════════════════════════════════════════════
# 年柱 / 月柱自校（河洛口径）
# ═══════════════════════════════════════════════════════════════════
#
# 为什么需要自校
# --------------
# 河洛自身的农历/节气链一律以 **sxtwl** 为准（canonical._jie_by_batch、
# jiehhou 均用 sxtwl.JD2DD，即 1582 年前为儒略历）。但**输入四柱**通常来自
# 八字引擎，而八字引擎的「节」边界比较用 jd_to_datetime（proleptic
# Gregorian）—— 1582 年前**整体后移 7 天**（见模块头）。
#
# 后果不是小疵：月支一变，**地支奇偶**就变 → 天数地数变 → **先天卦、元堂、
# 后天卦、全部判词全变**（子为奇数=天，亥为偶数=地）。
#
# 故河洛侧按**自己的口径**自校年/月柱：不一致时以 sxtwl 为准并留痕。
# 这不是「河洛压过八字」——是让河洛内部口径自洽（它的月令、节候卦、
# 化工、流月链本来就全都按 sxtwl 走）。
#
# 边界处理
# --------
# * sxtwl 的 getYearGZ / getMonthGZ 是**整日**口径，八字引擎按**精确时刻**切分；
#   故交节当日的整日值可能与八字不同 —— 那是正常边界差异，**不改**。
# * 交节时刻落在出生时辰窗口内时 → **不可判定**，保持输入值不动并留痕
#   （不臆断）。
# * 日柱/时柱与节边界无关，**不动**。

def _birth_window(birth_date: str, birth_hour: str | None):
    """出生时辰的绝对时间窗 ``(起, 止)``（sxtwl 标签口径的 naive datetime）。

    ``birth_hour`` 为空 → 整日窗口（00:00→24:00）。
    """
    from datetime import datetime, timedelta
    try:
        y, m, d = (int(x) for x in str(birth_date)[:10].split("-"))
    except Exception:
        return None
    if not birth_hour or birth_hour not in _SHICHEN_WINDOW:
        return datetime(y, m, d), datetime(y, m, d) + timedelta(days=1)
    h0, h1 = _SHICHEN_WINDOW[birth_hour]
    start = datetime(y, m, d) + timedelta(hours=h0)
    end = datetime(y, m, d) + timedelta(hours=h1)
    return start, end


def _jieqi_datetime(year: int, jq_index: int):
    """该公历年指定节气（sxtwl 口径）的时刻；无则 None。"""
    try:
        import sxtwl
    except ImportError:                      # pragma: no cover - 依赖缺失
        return None
    try:
        infos = sxtwl.getJieQiByYear(year)
    except Exception:
        return None
    for info in infos:
        idx = getattr(info, "jqIndex", None)
        jd = getattr(info, "jd", None)
        if idx is None or jd is None or idx % 24 != jq_index % 24:
            continue
        t = sxtwl.JD2DD(jd)
        if not (0 < t.Y <= 2200):
            continue
        from datetime import datetime
        return datetime(int(t.Y), int(t.M), int(t.D), int(t.h), int(t.m))
    return None


def authoritative_year_month(
    birth_date: str,
    birth_hour: str | None = None,
) -> dict:
    """按河洛口径（sxtwl，1582 年前 = 儒略历）自算出生时刻的年柱与月柱。

    返回 ``{"year": "庚午"|None, "month": "庚子"|None, "ambiguous": [...]}``；
    ``None`` 表示该柱**不可判定**（交节时刻落在出生时辰窗口内），此时保持
    输入值不动。
    """
    out: dict[str, Any] = {"year": None, "month": None, "ambiguous": []}
    try:
        import sxtwl
    except ImportError:                      # pragma: no cover - 依赖缺失
        return out
    try:
        y, m, d = (int(x) for x in str(birth_date)[:10].split("-"))
    except Exception:
        return out

    day = sxtwl.fromSolar(y, m, d)
    prev = sxtwl.fromSolar(y, m, d - 1)
    win = _birth_window(birth_date, birth_hour)
    if win is None:
        return out
    w_start, w_end = win

    def _before(jq_index: int) -> bool | None:
        """出生是否确定早于该节：True=确定早、False=确定晚、None=不可判定。"""
        jd_dt = _jieqi_datetime(y, jq_index)
        if jd_dt is None:
            return None
        if jd_dt >= w_end:
            return True
        if jd_dt <= w_start:
            return False
        return None

    # 年柱：立春为界（jq 3 = 立春）
    before = _before(3)
    ygz = day.getYearGZ()
    if before is True:
        ygz = prev.getYearGZ()
    elif before is None:
        out["ambiguous"].append("年柱（立春时刻落在出生时辰窗口内，不可判定）")
    out["year"] = _GAN[ygz.tg] + _ZHI[ygz.dz]

    # 月柱：以「节」为界（奇数索引为节）
    jq = day.getJieQi()
    mgz = day.getMonthGZ()
    if jq >= 0 and jq % 2 == 1:
        before = _before(jq)
        if before is True:
            mgz = prev.getMonthGZ()
        elif before is None:
            out["ambiguous"].append(
                f"月柱（{_JQ_NAME.get(jq % 24, '该节')}时刻落在出生时辰窗口内，不可判定）")
    out["month"] = _GAN[mgz.tg] + _ZHI[mgz.dz]
    return out


#: 节气索引 → 名（仅用于留痕措辞）
_JQ_NAME: dict[int, str] = {
    0: "冬至", 1: "小寒", 2: "大寒", 3: "立春", 4: "雨水", 5: "惊蛰",
    6: "春分", 7: "清明", 8: "谷雨", 9: "立夏", 10: "小满", 11: "芒种",
    12: "夏至", 13: "小暑", 14: "大暑", 15: "立秋", 16: "处暑", 17: "白露",
    18: "秋分", 19: "寒露", 20: "霜降", 21: "立冬", 22: "小雪", 23: "大雪",
}


def _gz60_index(ganzhi: str) -> int | None:
    """干支在 60 甲子中的序号（0..59）；不成干支返回 None。"""
    if len(ganzhi) != 2:
        return None
    g, z = ganzhi[0], ganzhi[1]
    if g not in _GAN or z not in _ZHI:
        return None
    _gi, _zi = _GAN.index(g), _ZHI.index(z)
    for n in range(60):
        if _GAN[n % 10] == g and _ZHI[n % 12] == z:
            return n
    return None


def _adjacent(a: str, b: str, ring: int) -> bool:
    """两个干支/地支在环上是否**相邻**（差一位）。

    只有相邻才可能是「交节边界错位」；相差更远说明输入与出生日期
    **根本不是一回事**（合成 fixture、或输入本身有误）—— 那种情况河洛
    **不改**（改动会篡改调用方的显式输入），只留痕告警。
    """
    if ring == 12:
        # 月柱：只比**地支**（月柱的干随年干变，不参与相邻判定）
        ba, bb = a[-1], b[-1]
        if ba not in _ZHI or bb not in _ZHI:
            return False
        ia, ib = _ZHI.index(ba), _ZHI.index(bb)
    else:
        ia, ib = _gz60_index(a), _gz60_index(b)
        if ia is None or ib is None:
            return False
    return (ia - ib) % ring == 1 or (ib - ia) % ring == 1


def resolve_year_month(
    bazi: Sequence[Any] | None,
    birth_date: str,
    birth_hour: str | None = None,
) -> tuple[list[tuple[str, str]] | None, list[str]]:
    """按河洛口径自校输入四柱的**年柱 / 月柱**。

    返回 ``(修正后的四柱, 留痕文字)``；四柱无需修正时原样返回。
    只改年柱/月柱 —— 日柱、时柱与节边界无关，**不动**。

    修正只在「两柱相邻」时进行：相邻 = 交节边界错位的典型形态。
    相差更远（输入与日期根本不对应）时**不改**，只留痕 ——
    合成 fixture 与真实输入都不该被河洛擅自改写。
    """
    if not bazi or len(bazi) < 3 or not birth_date:
        return (list(bazi) if bazi else None), []
    auth = authoritative_year_month(birth_date, birth_hour)
    if not auth or (auth["year"] is None and auth["month"] is None):
        return list(bazi), []

    fixed = list(bazi)
    notes: list[str] = []
    for idx, key, label, ring in ((0, "year", "年柱", 60), (1, "month", "月柱", 12)):
        want = auth.get(key)
        if not want:
            continue
        try:
            cur = f"{bazi[idx][0]}{bazi[idx][1]}"
        except Exception:
            continue
        if cur == want:
            continue
        if not _adjacent(cur, want, ring):
            notes.append(
                f"  历法自校：{label}与出生日期不对应（输入 {cur}，按该日期的河洛口径应为 "
                f"{want}，两者不相邻）—— 疑似合成数据或输入有误；河洛**未改动**输入四柱，"
                "按所给四柱计算，请调用方核对。")
            continue
        fixed[idx] = (want[0], want[1])
        notes.append(
            f"  历法自校：{label}与河洛节气口径不符（输入 {cur}，河洛口径 {want}，相邻）"
            "—— 已按河洛口径（sxtwl，1582 年前为儒略历）修正。"
            "月柱一改则地支奇偶、天数地数、先天卦、元堂、判词全链随之变化。")
    if auth.get("ambiguous"):
        notes.append("  历法自校：" + "；".join(auth["ambiguous"]) + "，保持输入值不动。")
    return fixed, notes
