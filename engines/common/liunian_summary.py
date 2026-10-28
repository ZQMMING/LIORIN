# -*- coding: utf-8 -*-
"""流年层: 原局+大运+流年, 重算结构变化."""
from typing import Any, Dict, List
from engines.common.dayun_summary import dayun_summary


def liunian_summary(pillars: Dict[str, list], dayun: List[str],
                    liunian: str) -> Dict[str, Any]:
    """pillars: 原局; dayun: 大运干支; liunian: 流年干支."""
    # 先算大运层
    base = dayun_summary(pillars, dayun)
    # 加大流年
    all_branches = [pillars[k][1] for k in ('year','month','day','hour')] + [g[1] for g in dayun] + [liunian[1]]
    all_stems = [pillars[k][0] for k in ('year','month','day','hour')] + [g[0] for g in dayun] + [liunian[0]]

    from engines.common.l0_fact_builder import build, ten_god, WUXING, HIDDEN
    facts = build(pillars)
    dm = pillars['day'][0]
    mqi = WUXING[HIDDEN[facts['month_branch']][0]]

    from engines.common.daymaster_branch_tier import classify_branch_tier
    from engines.common.daymaster_root_class import classify_root_in_branches
    t1 = classify_branch_tier(all_branches, mqi)
    r1 = classify_root_in_branches(dm, all_branches, HIDDEN)

    party_count = {}
    for s in all_stems:
        tg = ten_god(dm, s)
        party_count[tg] = party_count.get(tg, 0) + 1
    party_detail = {}
    for tg, cnt in party_count.items():
        party_detail[tg] = {'stem_count': cnt, 'party_formed': cnt >= 2}

    from engines.common.chong_transit import chong_with_transit, LIU_CHONG
    root_branches_orig = [pillars[k][1] for k in ('year','month','day','hour')]
    lc_set = set(frozenset(p) for p in LIU_CHONG)
    ln_root_struck = [[liunian[1], rb] for rb in root_branches_orig if frozenset((liunian[1],rb)) in lc_set]
    from engines.common.daymaster_tian_he import HE_TO_HUASHEN
    he_pairs=[]
    for i in range(len(all_stems)):
        for j in range(i+1,len(all_stems)):
            hs=frozenset((all_stems[i],all_stems[j]))
            if hs in HE_TO_HUASHEN: he_pairs.append({'stems':[all_stems[i],all_stems[j]],'huashen':HE_TO_HUASHEN[hs]})
    he_huashen_deshi = any(p['huashen']==mqi for p in he_pairs)
    chong = chong_with_transit([pillars[k][1] for k in ('year','month','day','hour')], mqi, liunian[1])

    # 流年三合三会重算
    SANHE = {frozenset(('亥','卯','未')):'木', frozenset(('寅','午','戌')):'火', frozenset(('巳','酉','丑')):'金', frozenset(('申','子','辰')):'水'}
    SANHUI = {frozenset(('寅','卯','辰')):'木', frozenset(('巳','午','未')):'火', frozenset(('申','酉','戌')):'金', frozenset(('亥','子','丑')):'水'}
    sanhe_ju = [wx for br,wx in SANHE.items() if br.issubset(all_branches)]
    sanhui_ju = [wx for br,wx in SANHUI.items() if br.issubset(all_branches)]

    # 复合七档(权威): 原局+流年; 以及每步大运+流年(供按实际所行大运选取)
    from engines.common.transit_power import build_transit_power as _btp, transit_clash_verdicts as _tcv
    _ln_tp = _btp(pillars, [liunian])
    liunian_transit = {'spectrum': _ln_tp['spectrum'].get('spectrum'),
                       'clash': [_v['verdict'] for _v in _tcv(_ln_tp)]}
    per_dayun_liunian = []
    for _gz in dayun:
        _tp = _btp(pillars, [_gz, liunian])
        per_dayun_liunian.append({'dayun': _gz, 'liunian': liunian,
            'spectrum': _tp['spectrum'].get('spectrum'),
            'clash': [_v['verdict'] for _v in _tcv(_tp)]})

    return {
        'liunian_transit': liunian_transit,
        'per_dayun_liunian': per_dayun_liunian,
        'daymaster': dm,
        'month_qi': mqi,
        'dayun_root': base['dayun_root'],
        'liunian_root': {'has_root': r1['has_root'], 'heavy': r1['has_heavy_root']},
        'root_changed': (base['dayun_root']['has_root'] != r1['has_root'] or
                         base['dayun_root']['heavy'] != r1['has_heavy_root']),
        'party_count': party_count,
        'party_detail': party_detail,
        'chong': chong,
        'he_pairs': he_pairs,
        'he_huashen_deshi': he_huashen_deshi,
        'ln_root_struck': ln_root_struck,
        'liunian': liunian,
        'sanhe_ju': sanhe_ju,
        'sanhui_ju': sanhui_ju,
        'judgment_status': 'LIUNIAN_SUMMARY_ONLY',
        'boundary_note': '流年层重算结构变化; 离散枚举不评分; 不输出吉凶',
    }
