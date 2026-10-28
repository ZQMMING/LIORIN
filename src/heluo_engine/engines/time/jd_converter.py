"""JD (Julian Date) to DateTime converter.

Provides reliable conversion between JD and datetime for solar term calculations.
Uses Meeus' Astronomical Algorithms, Chapter 7.

IMPORTANT: sxtwl's JD values need adjustment:
    - sxtwl stores节气时刻 in a custom JD system
    - To convert: subtract 1/3 from sxtwl's JD, then apply standard JD→UTC algorithm
    - Result is UTC time; add 8 hours for Beijing Time

Version: 1.0.5 (P2.7-H18-P0: Correct sxtwl JD offset)
   1.0.6 (2026-10-22): 1582-10-15 之前按**儒略历**换算（对齐 sxtwl 内部口径）
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

#: 格里历改历瞬间（1582-10-15 00:00 的 JD）。此前为儒略历。
#: sxtwl 的 JD2DD 在此之前给的是**儒略历**日期（见 sxtwl 源），故本模块必须
#: 用同一约定换算，否则同一物理日会被标成两个不同的日期。
_GREGORIAN_REFORM_JD = 2299160.5


def jd_to_datetime(jd: float) -> datetime:
    """Convert sxtwl JD to datetime (Beijing Time, UTC+8).

    V2.7 fix: sxtwl 的 JD 不是标准 UTC JD, 而是自定义的"北京时区戳"。
    直接 utcfromtimestamp(JD - 2440587.5)*86400 就是北京时间, 不需要 +8h。
    详见 docs/audit/BAZI_ENGINE_AUDIT_20260909.md R-04 根因分析。

    2026-10-22 修正（历法口径）：**1582-10-15 之前按儒略历换算**。

    背景：sxtwl 内部（``JD2DD``、``fromSolar``、``getDayGZ``、``getMonthGZ``）
    对 1582 年前的日期一律用**儒略历**；而本函数此前对**所有** JD 都按
    proleptic Gregorian 换算 —— 两者在 1150 / 1206 年**相差 7 天**
    （实测：大雪 1206 = sxtwl 标 1206-11-30 09:34，本函数原标 1206-12-07 09:34）。

    后果（**实测**）：八字引擎用本函数做「节」边界比较，1582 年前出生日的
    **月柱 / 立春年柱边界整体后移 7 天**（日柱不受影响：日干支由 sxtwl 的
    连续日序给出，与标签历法无关）。例：1206-11-30 21:00，原典《河洛真数》
    L186 作「丙寅 庚子 丙子 己亥」（子月），修前判成「丙寅 己亥 丙子 己亥」
    （亥月）；另有 158 处直接抛 "No '节' found within 33 days"。

    影响面（**实测**）：1582-10-15 之后**逐字节相同**（同一代码分支）：
    逐日核对 1582-10-16 ~ 2200-12-31 共 225,797 天，差异 0 天；
    1900-2100 抽样 5904 组四柱，差异 0 处。

    Args:
        jd: Julian Date from sxtwl.getJieQiJD()
    Returns:
        datetime object representing Beijing Time (UTC+8, tz-aware)
    """
    import datetime as _dt
    if jd < _GREGORIAN_REFORM_JD:
        # ── 儒略历路径（1582-10-15 之前）──
        #   与 sxtwl.JD2DD 同一约定（实测：1000/1150/1206/1500/1582 各节气
        #   时刻与 JD2DD 逐分钟一致），故八字引擎的「节」边界与 sxtwl 的
        #   日/月/年柱口径恢复自洽。
        jd0 = jd + 0.5
        z = int(jd0)
        f = jd0 - z
        a = z
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        day = b - d - int(30.6001 * e)
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        base = _dt.datetime(year, month, day) + _dt.timedelta(
            seconds=round(f * 86400))
        return base.replace(tzinfo=timezone(timedelta(hours=8)))
    # V2.8 LOCK: sxtwl JD = BJT timestamp 编码 (sxtwl 内部已用 BJT)
    # epoch = JD 2440587.5 = 1970-01-01 00:00 UTC, 但 sxtwl 用 BJT
    # sxtwl 立春 2460345.185 → BJT 16:26:53 (验证: utcfromtimestamp 给出此值)
    # V2.7 astimezone(+8h) 会再加 8h → 错位 00:26 次日
    # V2.8 正确做法: epoch + delta 已是 BJT 时刻, 直接标记 BJT tzinfo
    epoch = _dt.datetime(1970, 1, 1)
    days = jd - 2440587.5
    delta = _dt.timedelta(days=days)
    bjt_dt = epoch + delta  # 这是 BJT 时刻 (naive)
    return bjt_dt.replace(tzinfo=timezone(timedelta(hours=8)))


def get_nearest_jieqi(
    sxtwl_day_obj, direction: int, birth_dt: datetime, max_days: int = 32
) -> tuple[float, datetime] | None:
    """Find the nearest Jieqi (节) datetime relative to birth time.

    Args:
        sxtwl_day_obj: sxtwl Day object for testing
        direction: +1 for forward (顺排), -1 for backward (逆排)
        birth_dt: Birth datetime (Beijing Time, timezone-aware)
        max_days: Maximum search range

    Returns:
        Tuple of (jd_of_jieqi, jieqi_dt) or None
    """
    import sxtwl

    for i in range(1, max_days + 1):
        if direction == +1:
            test_dt = birth_dt + timedelta(days=i)
        else:
            test_dt = birth_dt - timedelta(days=i)

        day_obj = sxtwl.fromSolar(test_dt.year, test_dt.month, test_dt.day)

        if day_obj.hasJieQi():
            jieqi_jd = day_obj.getJieQiJD()
            jieqi_dt = jd_to_datetime(jieqi_jd)
            return jieqi_jd, jieqi_dt

    return None
