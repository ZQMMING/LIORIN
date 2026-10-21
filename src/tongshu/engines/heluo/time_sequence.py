"""⚠️ DEPRECATED — 旧版流年/流月/流日干支占位实现

已被 timeline_yun.py（流卦链）替代。
保留本文件仅作为历史参考，生产代码请勿 import 此模块。
"""
from __future__ import annotations
import warnings
warnings.warn(
    "time_sequence.py is deprecated. Use timeline_yun instead.",
    DeprecationWarning,
    stacklevel=2,
)
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

log = logging.getLogger(__name__)

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


# ═══════════════════════════════════════════════════════════════════
# HL-10 流年计算
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuNianInput:
    """流年计算输入。"""
    birth_year: int
    target_year: int  # 目标年份
    gender: str  # 'male' | 'female'


@dataclass
class LiuNianResult:
    """流年计算结果。"""
    input: LiuNianInput
    liu_nian_ganzhi: str  # 流年干支
    liu_nian_hexagram: str = ""
    element: str = ""


def compute_liu_nian(input_data: LiuNianInput) -> LiuNianResult:
    """
    计算流年干支。
    
    算法:
    1. 流年干支 = (target_year - 4) % 60
    2. 映射到六十四卦
    """
    stem_idx = (input_data.target_year - 4) % 10
    branch_idx = (input_data.target_year - 4) % 12
    
    liu_nian_ganzhi = f"{STEMS[stem_idx]}{BRANCHES[branch_idx]}"
    
    return LiuNianResult(
        input=input_data,
        liu_nian_ganzhi=liu_nian_ganzhi,
        element=STEMS[stem_idx]  # 简化：取天干五行
    )


# ═══════════════════════════════════════════════════════════════════
# HL-11 流月计算
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuYueInput:
    """流月计算输入。"""
    birth_year: int
    birth_month: int
    target_year: int
    target_month: int
    gender: str


@dataclass
class LiuYueResult:
    """流月计算结果。"""
    input: LiuYueInput
    liu_yue_ganzhi: str
    liu_yue_hexagram: str = ""


def compute_liu_yue(input_data: LiuYueInput) -> LiuYueResult:
    """
    计算流月干支。
    
    算法:
    1. 根据年干确定月干起算
    2. 从立春开始计算月支
    """
    # 年干决定月干起算
    year_stem = (input_data.target_year - 4) % 10
    stem_starts = {0: 2, 1: 4, 2: 0, 3: 2, 4: 4, 5: 0, 6: 2, 7: 4, 8: 0, 9: 2}
    stem_offset = stem_starts.get(year_stem, 0)
    
    # 流月干支
    month_stem = (stem_offset + input_data.target_month - 1) % 10
    month_branch = (input_data.target_month + 1) % 12  # 简化映射
    
    liu_yue_ganzhi = f"{STEMS[month_stem]}{BRANCHES[month_branch]}"
    
    return LiuYueResult(
        input=input_data,
        liu_yue_ganzhi=liu_yue_ganzhi
    )


# ═══════════════════════════════════════════════════════════════════
# HL-12 流日计算
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuRiInput:
    """流日计算输入。"""
    birth_year: int
    birth_month: int
    birth_day: int
    target_date: datetime
    gender: str


@dataclass
class LiuRiResult:
    """流日计算结果。"""
    input: LiuRiInput
    liu_ri_ganzhi: str
    liu_ri_hexagram: str = ""


def compute_liu_ri(input_data: LiuRiInput) -> LiuRiResult:
    """
    计算流日干支。
    
    算法:
    1. 以公元4年1月1日=甲子日为基准
    2. 计算目标日期与基准日的天数差
    3. 天干地支各取模循环
    """
    jiazi_base = datetime(4, 1, 1)
    days_diff = (input_data.target_date - jiazi_base).days
    
    stem_idx = days_diff % 10
    branch_idx = days_diff % 12
    
    liu_ri_ganzhi = f"{STEMS[stem_idx]}{BRANCHES[branch_idx]}"
    
    return LiuRiResult(
        input=input_data,
        liu_ri_ganzhi=liu_ri_ganzhi
    )


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import json
    
    # 测试 HL-10
    ln_input = LiuNianInput(birth_year=1990, target_year=2025, gender="male")
    ln_result = compute_liu_nian(ln_input)
    print(f"HL-10 流年: {ln_result.liu_nian_ganzhi}")
    
    # 测试 HL-11
    ly_input = LiuYueInput(birth_year=1990, birth_month=5, target_year=2025, target_month=8, gender="male")
    ly_result = compute_liu_yue(ly_input)
    print(f"HL-11 流月: {ly_result.liu_yue_ganzhi}")
    
    # 测试 HL-12
    lr_input = LiuRiInput(birth_year=1990, birth_month=5, birth_day=15, 
                         target_date=datetime(2025, 8, 21), gender="male")
    lr_result = compute_liu_ri(lr_input)
    print(f"HL-12 流日: {lr_result.liu_ri_ganzhi}")
