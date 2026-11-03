# -*- coding: utf-8 -*-
"""PATCH-160-C / 地支四阶旺衰层级派生器

回应"旺者冲衰衰者拔"所需的: 冲两支各自的旺衰层级.
不编"极旺到极衰"七级(那是综合强弱, 已封). 只由两个已授权布尔组合成四阶:

  阶3: 得月令本气 AND 同党成党
  阶2: 得月令本气 AND 无同党
  阶1: 失月令     AND 同党成党
  阶0: 失月令     AND 无同党

两个布尔都原典可溯:
  - 得月令本气 = 地支五行 == 月令本气五行
  - 同党成党   = 四柱地支中同五行 >= 2 (客观位置计数, 非权重)

不输出"旺/衰"综合判断; 本层只给每支一个可比较的结构阶位.
"""
from typing import Any, Dict, List

BRANCH_WX = {
    '子': '水', '亥': '水',
    '寅': '木', '卯': '木',
    '巳': '火', '午': '火',
    '申': '金', '酉': '金',
    '辰': '土', '戌': '土', '丑': '土', '未': '土',
}


def classify_branch_tier(branches, month_qi_wx):
    """可重入: 给定地支列表和月令五行, 返回 {branch: tier}. 供应期层重算."""
    from engines.common.l0_fact_builder import WUXING
    if isinstance(branches, str):
        branches = [branches]
    wx_count = {}
    for b in branches:
        wx = BRANCH_WX[b]
        wx_count[wx] = wx_count.get(wx, 0) + 1
    out = {}
    for b in branches:
        wx = BRANCH_WX[b]
        has_mq = (wx == month_qi_wx)
        has_party = (wx_count.get(wx, 0) >= 2)
        out[b] = 3 if (has_mq and has_party) else 2 if has_mq else 1 if has_party else 0
    return out


def build_branch_tiers(pillars: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    """pillars 四柱; facts = L0 build(). 返回每支四阶枚举."""
    branches = {k: pillars[k][1] for k in ('year', 'month', 'day', 'hour')}
    month_branch = facts['month_branch']
    month_benqi_stem = facts['hidden_stems']['month'][0]
    from engines.common.l0_fact_builder import WUXING
    month_qi_wx = WUXING[month_benqi_stem]

    tier_map = classify_branch_tier(list(branches.values()), month_qi_wx)

    per_pillar = {}
    for k, b in branches.items():
        wx = BRANCH_WX[b]
        per_pillar[k] = {
            'branch': b, 'wuxing': wx,
            'has_month_qi': (wx == month_qi_wx),
            'has_party': tier_map.get(b, 0) in (1, 3),
            'tier': tier_map.get(b, 0),
        }

    # --- 遍历六冲对, 比两支阶位 ---
    comb = facts.get('combination_facts', {}) or {}
    liu_chong = comb.get('liuchong') or []
    # 建 支->阶 索引(同名支取最高阶)
    branch_tier = {}
    for v in per_pillar.values():
        b = v['branch']
        branch_tier[b] = max(branch_tier.get(b, -1), v['tier'])

    clash_results = []
    for pair in liu_chong:
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
            continue
        a, b = pair
        ta, tb = branch_tier.get(a, 0), branch_tier.get(b, 0)
        if ta > tb:
            verdict = f'{a}旺{b}衰(阶{ta}>{tb}), {b}衰者拔'
        elif tb > ta:
            verdict = f'{b}旺{a}衰(阶{tb}>{ta}), {a}衰者拔'
        else:
            verdict = f'{a}{b}同阶(阶{ta}), 两停不拔不发'
        clash_results.append({
            'pair': [a, b], 'tier_a': ta, 'tier_b': tb, 'verdict': verdict,
        })

    return {
        'generator': 'BranchTierDeriver',
        'month_qi_wuxing': month_qi_wx,
        'per_pillar': per_pillar,
        'clash_results': clash_results,
        'judgment_status': 'STRUCTURAL_TIER_ONLY',
        'boundary_note': (
            '四阶=得月令本气+同党成党 两个原典可溯布尔组合; '
            '冲两支比阶, 不编七级旺衰, 不输出日主综合强弱; '
            '阶差仅判谁拔谁, 同阶两停, 不涉及百分比'
        ),
    }
