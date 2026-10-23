"""HL 引擎异常。

依据：无。

Version: 1.0.0
Created: 2026-08-21 (Phase 0 / HL-A2)
"""

from __future__ import annotations


class HeluoEngineError(Exception):
    """HL 引擎基类异常。"""


class YuanTangResolutionError(HeluoEngineError):
    """元堂取法不能解决（如 6 阳交全阳交全阴、多重交叉以上未定义）。"""


class HourOutOfRangeError(HeluoEngineError):
    """生时超出 0-23 范围。"""


class ForbiddenRuleError(HeluoEngineError):
    """使用了违反 SHUNTIAN §7 红线的算法（如 hour%6 一刀切）。"""


__all__ = [
    "HeluoEngineError",
    "YuanTangResolutionError",
    "HourOutOfRangeError",
    "ForbiddenRuleError",
]
