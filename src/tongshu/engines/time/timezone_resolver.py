"""时区解析封装（IANA + DST-aware）。

包装 zoneinfo.ZoneInfo，供 resolver 调用。依赖：
    - Python 3.9+ zoneinfo（标准库）
    - 中国 1986-1991 夏令时残留水准裡历史。

依赖：exceptions。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:resolve() 内部的 ZoneInfo 分支
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .exceptions import TimezoneError


def parse_timezone(tz_name: str) -> ZoneInfo:
    """解析 IANA timezone 名为 ZoneInfo。

    Raises:
        TimezoneError: 非法或不可解析的 timezone 名。
    """
    try:
        return ZoneInfo(tz_name)
    except Exception as e:
        raise TimezoneError(f"invalid IANA timezone {tz_name!r}") from e


def utc_offset_minutes(local_dt: datetime) -> int:
    """从 timezone-aware datetime 提取 UTC offset（分钟，DST-aware）。"""
    return int(local_dt.utcoffset().total_seconds() // 60)


__all__ = ["parse_timezone", "utc_offset_minutes"]
