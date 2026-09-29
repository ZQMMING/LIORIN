"""子时跨日政策（依据 P0-14 / D1 裁定）。

负责：
    - DAY_BOUNDARY: 子时跨日的小时阈值（23 = 23:00 换日）
    - _TRADITIONAL_HOURS: 24 个小时→时辰名映射
    - traditional_hour_name(): 调用接口

依赖：无。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:30-44
"""

from __future__ import annotations


# 2026-09-14 子正换日裁决（覆盖 P0-14 旧“23:00 换日”）：日界 = 0:00（子正）。
# DAY_BOUNDARY 保留 23，语义改为“夜子时起始小时”（23:00-23:59:59 时柱按次日日干），不再是换日点。
DAY_BOUNDARY: int = 23

# 传统时辰名（以有效太阳时为准；23=晚子时、0=早子时，均属子时）。
_TRADITIONAL_HOURS: dict[int, str] = {
    0:  "子时(早)", 1:  "丑时", 2:  "丑时", 3:  "寅时", 4:  "寅时",
    5:  "卯时", 6:  "卯时", 7:  "辰时", 8:  "辰时", 9:  "巳时", 10: "巳时",
    11: "午时", 12: "午时", 13: "未时", 14: "未时", 15: "申时", 16: "申时",
    17: "酉时", 18: "酉时", 19: "戌时", 20: "戌时", 21: "亥时", 22: "亥时",
    23: "子时(晚)",
}


def traditional_hour_name(hour: int) -> str:
    """传统时辰名（0-23）；23 与 0 均为子时，标注 晚/早 以区分。"""
    return _TRADITIONAL_HOURS[hour % 24]


__all__ = ["DAY_BOUNDARY", "traditional_hour_name"]
