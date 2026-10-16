"""engines/time/ — TimeResolver 拆分后的公共导出。

本包是 engines/time_resolver.py 拆分后的子包（Step 7 产出）。
原文件 time_resolver.py 变为薄转发 shim（仅重导出公共符号）。

调用方接口未变：
    from tongshu.engines.time_resolver import TimeResolver  # 仍然可用
    from tongshu.engines.time import TimeResolver            # 新路径

模块划分（依赖顺序）：
    exceptions          → 依赖顶层（无依赖）
    day_boundary        → DAY_BOUNDARY 常量 + traditional_hour_name()
    longitude_offset    → MIN_PER_DEGREE + 经度修正
    eot                 → equation_of_time() 天文公式
    timezone_resolver   → IANA + DST
    location_registry   → 地点加载 + 索引
    calculation_context → ResolvedBirthInstant + CalculationContext 数据类
    resolver            → TimeResolver 主类（薄编排）

Version: 1.0.0  Created: 2026-08-20 (Phase 2 / Step 7)
"""

from .calculation_context import (
    RESOLVER_VERSION,
    POLICY_VERSION,
    CalculationContext,
    ResolvedBirthInstant,
)
from .day_boundary import DAY_BOUNDARY, traditional_hour_name
from .eot import equation_of_time
from .exceptions import (
    LocationError,
    TimeResolverError,
    TimezoneError,
)
from .location_registry import (
    DEFAULT_LOCATIONS_PATH,
    LocationEntry,
    LocationRegistry,
)
from .longitude_offset import (
    MIN_PER_DEGREE,
    longitude_correction_minutes,
    ref_meridian_from_offset,
)
from .resolver import TimeResolver
from .timezone_resolver import parse_timezone, utc_offset_minutes


__all__ = [
    # Constants
    "DAY_BOUNDARY",
    "MIN_PER_DEGREE",
    "RESOLVER_VERSION",
    "POLICY_VERSION",
    "DEFAULT_LOCATIONS_PATH",
    # Errors
    "TimeResolverError",
    "LocationError",
    "TimezoneError",
    # Dataclasses
    "LocationEntry",
    "ResolvedBirthInstant",
    "CalculationContext",
    # Main class
    "TimeResolver",
    # Helpers
    "LocationRegistry",
    "traditional_hour_name",
    "equation_of_time",
    "ref_meridian_from_offset",
    "longitude_correction_minutes",
    "parse_timezone",
    "utc_offset_minutes",
]
