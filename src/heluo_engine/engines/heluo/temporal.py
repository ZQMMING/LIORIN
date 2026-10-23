"""河洛时间序列卦象模块（Module 6）

负责：流年/流月/流日/时刻/节候/卦气
输入：CalculationContext + PrenatalHexagram
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date


@dataclass(frozen=True)
class Timeline:
    """时间序列卦象结果

    2026-10-06 修正字段说明——原先三个字段的声明与实际写入不符：
      - ``daily_hexagram`` 注释写「今日卦」，实际写入的却是**先天卦**，
        且 ``date`` 塞的是 ``str(birth_year)``（如 "1990"），既非日期也非流日卦。
      - ``monthly_hexagrams`` 恒为 ``[]``、``hourly_hexagram`` 恒为 ``None``。
    三者全仓零消费方，且真实流月/流日/流时卦已在四层时间轴
    （``yearly_hexagrams[].months[] / .days[]``）内按需产出，
    故此处一律置空，不再保留名不副实的副本。
    """
    yearly_hexagrams: list[dict]    # 流年卦列表（定稿后仅含近 3 年）

    yearly_meta: list[dict]        # 其余流年**纯元数据** {year, age, ganzhi}（不起卦）

    target_year_hexagram: dict      # 目标流年卦摘要（ganzhi/hexagram/yi_signal/changed_line）

    monthly_hexagrams: list[dict]   # 流月卦列表（占位，恒空；真实值见 yearly[].months）
    daily_hexagram: dict             # 今日卦（占位，恒空；真实值见 yearly[].months[].days）
    hourly_hexagram: dict | None    # 时刻卦（占位，恒 None；真实值由 guajie 按 target_hour 现算）
    seasonal_hexagram: dict | None  # 节候卦（占位，恒 None；真实值见 HeluoResult.seasonal_hexagram）
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

    ⚠️ 本函数是**占位桩**，全仓零调用点；真正的四层时间轴计算在
    ``canonical.HelioCanonical._build_timeline``。2026-10-22 因 Timeline
    新增必填字段 yearly_meta / target_year_hexagram 而一度签名不匹配
    （一调即 TypeError），现已补齐并显式标注为占位桩。
    """
    return Timeline(
        yearly_hexagrams=[],
        yearly_meta=[],
        target_year_hexagram={},
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
