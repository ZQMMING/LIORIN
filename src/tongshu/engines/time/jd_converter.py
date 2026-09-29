"""JD (Julian Date) to DateTime converter.

Provides reliable conversion between JD and datetime for solar term calculations.
Uses Meeus' Astronomical Algorithms, Chapter 7.

IMPORTANT: sxtwl's JD values need adjustment:
    - sxtwl stores节气时刻 in a custom JD system
    - To convert: subtract 1/3 from sxtwl's JD, then apply standard JD→UTC algorithm
    - Result is UTC time; add 8 hours for Beijing Time

Version: 1.0.5 (P2.7-H18-P0: Correct sxtwl JD offset)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta


def jd_to_datetime(jd: float) -> datetime:
    """Convert sxtwl JD to datetime (Beijing Time, UTC+8).

    V2.7 fix: sxtwl 的 JD 不是标准 UTC JD, 而是自定义的"北京时区戳"。
    直接 utcfromtimestamp(JD - 2440587.5)*86400 就是北京时间, 不需要 +8h。
    详见 docs/audit/BAZI_ENGINE_AUDIT_20260909.md R-04 根因分析。

    Args:
        jd: Julian Date from sxtwl.getJieQiJD()
    Returns:
        datetime object representing Beijing Time (UTC+8, tz-aware)
    """
    import datetime as _dt
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
