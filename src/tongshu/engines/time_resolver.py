"""True-solar-time (真太阳时) resolution — P0-14 计算上下文约束。

**过渡 shim**（Phase 2 / Step 7 产出）：原文件 459 行均已迁出至 engines/time/
子包，本文件仅重导出公共符号以保持向后兼容。
新代码请直接 import 自 tongshu.engines.time。

原始实现已迁出（保持原始行为）：
    engines/time/exceptions.py          TimeResolverError / LocationError / TimezoneError
    engines/time/day_boundary.py        DAY_BOUNDARY + traditional_hour_name
    engines/time/longitude_offset.py    MIN_PER_DEGREE + 经度修正
    engines/time/eot.py                 equation_of_time
    engines/time/timezone_resolver.py   IANA + DST
    engines/time/location_registry.py   LocationEntry + LocationRegistry
    engines/time/calculation_context.py ResolvedBirthInstant + CalculationContext
    engines/time/resolver.py            TimeResolver 主类

Migrated: 2026-08-20 (Phase 2 / Step 7)
"""

from __future__ import annotations

from .time import (
    # Constants
    DAY_BOUNDARY,
    MIN_PER_DEGREE,
    RESOLVER_VERSION,
    POLICY_VERSION,
    DEFAULT_LOCATIONS_PATH,
    # Errors
    TimeResolverError,
    LocationError,
    TimezoneError,
    # Dataclasses
    LocationEntry,
    ResolvedBirthInstant,
    CalculationContext,
    # Main class
    TimeResolver,
    # Helpers
    LocationRegistry,
    traditional_hour_name,
    equation_of_time,
    ref_meridian_from_offset,
    longitude_correction_minutes,
    parse_timezone,
    utc_offset_minutes,
)

__all__ = [
    "DAY_BOUNDARY",
    "MIN_PER_DEGREE",
    "RESOLVER_VERSION",
    "POLICY_VERSION",
    "DEFAULT_LOCATIONS_PATH",
    "TimeResolverError",
    "LocationError",
    "TimezoneError",
    "LocationEntry",
    "LocationRegistry",
    "ResolvedBirthInstant",
    "CalculationContext",
    "TimeResolver",
    "traditional_hour_name",
    "equation_of_time",
    "ref_meridian_from_offset",
    "longitude_correction_minutes",
    "parse_timezone",
    "utc_offset_minutes",
]
