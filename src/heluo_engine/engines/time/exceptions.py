"""Time resolution 异常类层。

依赖关系：无依赖（号为最底层）。

Version: 1.0.0  Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:46-58
"""

from __future__ import annotations


class TimeResolverError(Exception):
    """Base error for time resolution."""


class LocationError(TimeResolverError):
    """Unknown / unresolvable birth location."""


class TimezoneError(TimeResolverError):
    """Invalid IANA timezone name."""


__all__ = ["TimeResolverError", "LocationError", "TimezoneError"]
