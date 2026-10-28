"""经度修正 (longitude − ref_meridian) × 4min/度 。

依据：P0-14 / D2 裁定。
- ref_meridian = UTC-offset 小时×15°（DST-aware）
- 经度修正：出生地经度 − 参考子周经度 × 4 分钟/度

依赖：stdlib 仅。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:23 (MIN_PER_DEGREE constant)
              + resolve() 内部的经度修正计算
"""

from __future__ import annotations


# 经度差 1° = 4 分钟。
MIN_PER_DEGREE: float = 4.0


def ref_meridian_from_offset(utc_offset_min: int) -> float:
    """IANA UTC offset → 参考子周经度（度）。

    Args:
        utc_offset_min: UTC 偏移（分钟，DST-aware）。例如 CET=+60, CEST=+120。
    Returns:
        参考子周经度（度，保留 2 位小数）。例如 UTC+1 → 15°E, UTC+8 → 120°E。
    """
    return round(utc_offset_min / 60.0 * 15.0, 2)


def longitude_correction_minutes(longitude: float, ref_meridian: float) -> float:
    """出生地经度 − 参考子周经度 × 4 min/°。

    Returns: 分钟（保留 2 位小数）。
    """
    return round((longitude - ref_meridian) * MIN_PER_DEGREE, 2)


__all__ = ["MIN_PER_DEGREE", "ref_meridian_from_offset", "longitude_correction_minutes"]
