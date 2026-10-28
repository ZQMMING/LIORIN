# -*- coding: utf-8 -*-
"""应期层: 加岁运支后重算冲支结果.
不评分不阈值, 只输出tier变化和冲结果枚举."""
from typing import Any, Dict, List
from engines.common.daymaster_branch_tier import classify_branch_tier, BRANCH_WX

LIU_CHONG = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]

def chong_with_transit(original_branches: List[str], month_qi_wx: str,
                       transit_branch: str) -> Dict[str, Any]:
    """加岁运支后重算.
    original_branches: 原局四柱地支 list.
    month_qi_wx: 月令本气五行.
    transit_branch: 岁运加入的地支.
    返回: 原局tier / 复合tier / 冲结果变化."""
    orig_tier = classify_branch_tier(original_branches, month_qi_wx)
    combined = list(original_branches) + [transit_branch]
    new_tier = classify_branch_tier(combined, month_qi_wx)

    def _chong(tier_map):
        out = []
        for a, b in LIU_CHONG:
            if a in tier_map and b in tier_map:
                ta, tb = tier_map[a], tier_map[b]
                if ta > tb:
                    v = f'{a}旺{b}衰, {b}拔'
                elif tb > ta:
                    v = f'{b}旺{a}衰, {a}拔'
                else:
                    v = f'{a}{b}同阶两停'
                out.append({'pair':[a,b],'ta':ta,'tb':tb,'verdict':v})
        return out

    return {
        'original_branches': original_branches,
        'transit_branch': transit_branch,
        'original_tier': orig_tier,
        'combined_tier': new_tier,
        'original_chong': _chong(orig_tier),
        'combined_chong': _chong(new_tier),
        'judgment_status': 'CHONG_TRANSIT_ONLY',
        'boundary_note': '加岁运支重算tier和冲结果; 不评分不阈值; 旺衰枚举比较非数值',
    }
