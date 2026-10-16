"""河洛时间序列卦象模块（Module 6）

负责：流年/流月/流日/时刻/节候/卦气
输入：CalculationContext + PrenatalHexagram
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date


@dataclass(frozen=True)
class Timeline:
    """时间序列卦象结果"""
    yearly_hexagrams: list[dict]    # 流年卦列表
    monthly_hexagrams: list[dict]   # 流月卦列表
    daily_hexagram: dict             # 今日卦
    hourly_hexagram: dict | None    # 时刻卦
    seasonal_hexagram: dict | None  # 节候卦
    qi_phase: dict | None           # 卦气
    hua_gong: dict | None           # 化工状态（H6）


def compute_timeline(
    birth_date: date,
    prenatal_upper: str,
    prenatal_lower: str,
    prenatal_name: str,
) -> Timeline:
    """
    计算时间序列卦象。

    输入：出生年月日 + 本命卦
    输出：各时间维度的卦象

    注意：当前实现为占位，具体时间卦计算待版本锁定后接入。
    """
    return Timeline(
        yearly_hexagrams=[],
        monthly_hexagrams=[],
        daily_hexagram={
            'date': birth_date.isoformat(),
            'hexagram': prenatal_name,
            'upper': prenatal_upper,
            'lower': prenatal_lower,
        },
        hourly_hexagram=None,
        seasonal_hexagram=None,
        qi_phase=None,
        hua_gong=None,
    )


def compute_daily_hexagram(
    target_date: date,
    prenatal_upper: str,
    prenatal_lower: str,
) -> dict:
    """
    计算指定日期的卦象。

    输入：目标日期 + 本命卦
    输出：当日卦信息
    """
    return {
        'date': target_date.isoformat(),
        'prenatal_hexagram': f"{prenatal_upper}{prenatal_lower}",
        'note': 'Daily hexagram calculation pending version lock',
    }
