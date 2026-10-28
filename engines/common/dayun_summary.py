# -*- coding: utf-8 -*-
"""大运层: 原局+大运干支, 重算结构变化.
不评分不阈值, 只输出离散枚举变化."""
from typing import Any, Dict, List
from engines.common.l0_fact_builder import build, HIDDEN, WUXING
from engines.common.daymaster_root_class import classify_root_in_branches
from engines.common.daymaster_branch_tier import classify_branch_tier
from engines.common.chong_transit import chong_with_transit
from engines.common.daymaster_tian_he import HE_TO_HUASHEN


def dayun_summary(pillars: Dict[str, list], dayun: List[str]) -> Dict[str, Any]:
    """pillars: 原局四柱; dayun: 大运干支列表(如['甲子','乙丑'])."""
    facts = build(pillars)
    dm = pillars['day'][0]
    branches = [pillars[k][1] for k in ('year','month','day','hour')]
    mzi = facts['month_branch']
    mqi = WUXING[HIDDEN[mzi][0]]

    # 原局
    r0 = classify_root_in_branches(dm, branches, HIDDEN)
    t0 = classify_branch_tier(branches, mqi)

    # 大运支
    dy_branches = [g[1] for g in dayun]
    all_branches = branches + dy_branches
    r1 = classify_root_in_branches(dm, all_branches, HIDDEN)
    t1 = classify_branch_tier(all_branches, mqi)

    # 大运冲支
    chong = chong_with_transit(branches, mqi, dy_branches[0] if dy_branches else branches[0])

    # 大运天干合
    all_stems = [pillars[k][0] for k in ('year','month','day','hour')] + [g[0] for g in dayun]
    he_pairs = []
    for i in range(len(all_stems)):
        for j in range(i+1, len(all_stems)):
            hs = frozenset((all_stems[i], all_stems[j]))
            if hs in HE_TO_HUASHEN:
                he_pairs.append({'stems':[all_stems[i],all_stems[j]],'huashen':HE_TO_HUASHEN[hs]})

    # 大运root_struck: 大运支冲原局根支
    from engines.common.chong_transit import LIU_CHONG
    root_branches = [k for k,v in r0.get('per_pillar',{}).items() if v]
    dy_root_struck = []
    for dc in dy_branches:
        for rb in root_branches:
            if frozenset((dc,rb)) in LIU_CHONG: dy_root_struck.append((dc,rb))

    # 大运合化成功: 天干合+化神得令+局全
    from engines.common.l0_fact_builder import ten_god, WUXING as WX
    he_huashen_deshi = False
    for p in he_pairs:
        if p['huashen'] == mqi: he_huashen_deshi = True

    # 大运透干重算: 加大运天干后十神成党
    all_stems_dm = [s for s in all_stems]
    party_count = {}
    for s in all_stems_dm:
        tg = ten_god(dm, s)
        party_count[tg] = party_count.get(tg, 0) + 1
    # 细化: 十神成党结构(透干+通根)
    party_detail = {}
    for tg, cnt in party_count.items():
        # 透干: 该十神天干出现
        tou = cnt > 0
        # 通根: 该十神五行在地支有根
        tg_wx = WX.get(dm, '')
        # 简化: 透干>=2视为成党
        party_detail[tg] = {'stem_count': cnt, 'party_formed': cnt >= 2}

    # 大运三合三会重算
    SANHE = {frozenset(('亥','卯','未')):'木', frozenset(('寅','午','戌')):'火', frozenset(('巳','酉','丑')):'金', frozenset(('申','子','辰')):'水'}
    SANHUI = {frozenset(('寅','卯','辰')):'木', frozenset(('巳','午','未')):'火', frozenset(('申','酉','戌')):'金', frozenset(('亥','子','丑')):'水'}
    sanhe_ju = []
    sanhui_ju = []
    for br, wx in SANHE.items():
        if br.issubset(all_branches): sanhe_ju.append(wx)
    for br, wx in SANHUI.items():
        if br.issubset(all_branches): sanhui_ju.append(wx)

    # 复合七档(权威, 逐柱; 复用 transit_power, 不另造强弱)
    from engines.common.transit_power import build_transit_power, transit_clash_verdicts
    _base_tp = build_transit_power(pillars, [])
    base_spectrum = _base_tp['spectrum'].get('spectrum')
    per_step_transit = []
    for _gz in dayun:
        _tp = build_transit_power(pillars, [_gz])
        _dme = _tp['daymaster_element']
        per_step_transit.append({
            'ganzhi': _gz,
            'spectrum': _tp['spectrum'].get('spectrum'),
            'daymaster_ben': _tp['wuxing_power']['wuxing_power'][_dme]['ben_n'],
            'clash': [_v['verdict'] for _v in transit_clash_verdicts(_tp)]})

    return {
        'base_spectrum': base_spectrum,
        'per_step_transit': per_step_transit,
        'daymaster': dm,
        'month_qi': mqi,
        'original_root': {'has_root': r0['has_root'], 'heavy': r0['has_heavy_root']},
        'dayun_root': {'has_root': r1['has_root'], 'heavy': r1['has_heavy_root']},
        'root_changed': (r0['has_root'] != r1['has_root'] or r0['has_heavy_root'] != r1['has_heavy_root']),
        'dayun_root_struck': dy_root_struck,
        'chong': chong,
        'dayun_he_pairs': he_pairs,
        'party_count': party_count,
        'party_detail': party_detail,
        'he_huashen_deshi': he_huashen_deshi,
        'sanhe_ju': sanhe_ju,
        'sanhui_ju': sanhui_ju,
        'judgment_status': 'DAYUN_SUMMARY_ONLY',
        'boundary_note': '大运层重算结构变化; 离散枚举不评分; 不输出吉凶',
    }
