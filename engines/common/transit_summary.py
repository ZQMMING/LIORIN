# -*- coding: utf-8 -*-
"""应期层综合: 原局+岁运干支, 输出root/tier/冲支变化."""
from typing import Any, Dict, List
from engines.common.l0_fact_builder import build, HIDDEN, WUXING
from engines.common.daymaster_root_class import classify_root_in_branches
from engines.common.daymaster_branch_tier import classify_branch_tier
from engines.common.chong_transit import chong_with_transit


def transit_summary(pillars: Dict[str, list], transits: List[str]) -> Dict[str, Any]:
    """pillars: 原局四柱 {year:[干,支],...}; transits: 岁运支列表."""
    facts = build(pillars)
    dm = pillars['day'][0]
    branches = [pillars[k][1] for k in ('year','month','day','hour')]
    mzi = facts['month_branch']
    mqi = WUXING[HIDDEN[mzi][0]]

    r0 = classify_root_in_branches(dm, branches, HIDDEN)
    t0 = classify_branch_tier(branches, mqi)

    all_branches = branches + list(transits)
    r1 = classify_root_in_branches(dm, all_branches, HIDDEN)
    t1 = classify_branch_tier(all_branches, mqi)

    chong = chong_with_transit(branches, mqi, transits[0] if transits else branches[0])

    return {
        'daymaster': dm,
        'month_qi': mqi,
        'original_root': {'has_root': r0['has_root'], 'heavy': r0['has_heavy_root']},
        'transit_root': {'has_root': r1['has_root'], 'heavy': r1['has_heavy_root']},
        'root_changed': (r0['has_root'] != r1['has_root'] or r0['has_heavy_root'] != r1['has_heavy_root']),
        'chong': chong,
        'judgment_status': 'TRANSIT_SUMMARY_ONLY',
        'boundary_note': '应期层重算结构变化; 离散枚举不评分; 不输出吉凶',
    }
