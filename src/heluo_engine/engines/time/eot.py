"""Equation of Time (EoT) 天文公式。

EoT = apparent_solar − mean_solar（单位：分钟）。
采用 Meeus 简化级数（不含高阶项）；
高精度应使用 sxtwl.EoT() 或天文库。

验证点数据（V5.0 / P0-14 待重验）：
    2026-02-11 ≈ -14.2 / 2026-05-14 ≈ +3.6 / 2026-07-26 ≈ -6.5 / 2026-11-03 ≈ +16.4
    零交跨：04-15 / 06-13 / 09-01 / 12-25。

依赖：stdlib 仅 math / datetime。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:305-340 (equation_of_time)
"""

from __future__ import annotations

import math
from datetime import date


def equation_of_time(solar_date: date) -> float:
    """Equation of time in minutes; EoT = apparent − mean (Meeus series).

    Verified 2026-08-18 against published values (±1.0 min).
    P0-14 re-check pending (V5.0 报告列入待办)。
    """
    n = (solar_date - date(2000, 1, 1)).days
    mean_longitude = 280.460 + 0.9856474 * n
    mean_anomaly = 357.528 + 0.9856003 * n
    e = 0.01671
    lam = (
        mean_longitude
        + 1.915 * math.sin(math.radians(mean_anomaly))
        + 0.020 * math.sin(math.radians(2 * mean_anomaly))
    )
    y = math.tan(math.radians(23.44) / 2) ** 2
    eot = (
        y * math.sin(math.radians(2 * lam))
        - 2 * e * math.sin(math.radians(mean_anomaly))
        + 4 * e * y * math.sin(math.radians(mean_anomaly)) * math.cos(math.radians(2 * lam))
        - 0.5 * y ** 2 * math.sin(math.radians(4 * lam))
        - 1.25 * e ** 2 * math.sin(math.radians(2 * mean_anomaly))
    )
    return 4.0 * eot * (180.0 / math.pi)


__all__ = ["equation_of_time"]
