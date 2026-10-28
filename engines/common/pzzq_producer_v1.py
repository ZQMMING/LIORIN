# -*- coding: utf-8 -*-
"""PATCH-138 PZZQ Producer v1
消费L0 facts -> 月令入口 -> pattern_candidates. 不判成格/破格/用神.
"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import ten_god

# 十神 -> 格局类型名(事实映射, 非吉凶)
TEN_GOD_TO_PATTERN = {
    '正官': '正官', '七杀': '七杀', '正财': '正财', '偏财': '偏财',
    '正印': '正印', '偏印': '偏印', '食神': '食神', '伤官': '伤官',
    '比肩': '建禄', '劫财': '月劫',
}


def produce_pattern_candidates(facts):
    dg = facts['day_stem']
    out = {'status': 'PRODUCED', 'pattern_candidates': [], 'source': []}
    mhs = facts['month_hidden_stems']
    transparent = facts['month_transparent']

    chosen = []
    if transparent:
        for s in transparent:
            tg = ten_god(dg, s)
            chosen.append((s, tg, 'transparent'))
        out['source'].append('month_transparent')
    else:
        # 不透: 取月令本气(藏干首位)
        s = mhs[0]
        tg = ten_god(dg, s)
        chosen.append((s, tg, 'month_benqi'))
        out['source'].append('month_benqi')

    for s, tg, how in chosen:
        out['pattern_candidates'].append({
            'pattern_type': TEN_GOD_TO_PATTERN.get(tg, tg),
            'ten_god': tg,
            'month_stem': s,
            'basis': how,
            'evidence': [
                f"month_branch={facts['month_branch']}",
                f"hidden={','.join(mhs)}",
                f"transparent={transparent}",
                f"day_stem={dg}",
            ],
            'conditions': {'required': [], 'blocked': [], 'supported': []},
            'status': 'CANDIDATE',
        })
    
    # PATCH-v2 非月令透干定格候选(年干/月干/时干): 经典中存在非月令定格用法
    # 仅作为候选并列, 不替代月令定格, 不判成格/成败
    # 月干仅当其不是月令藏干时才加入(避免与月令透干重复)
    other_stems = []
    stem_rels = facts.get('stem_relations', {})
    month_hs = set(mhs) if mhs else set()
    if isinstance(stem_rels, dict):
        for pos in ('year', 'month', 'hour'):
            rel = stem_rels.get(pos, {})
            if isinstance(rel, dict):
                s = rel.get('stem', '')
                if s and s != dg:
                    # 月干若是月令藏干, 已在月令透干中考虑, 不重复
                    if pos == 'month' and s in month_hs:
                        continue
                    other_stems.append((s, pos + '_stem'))
    
    existing_types = set(p['pattern_type'] for p in out['pattern_candidates'])
    for s, pos in other_stems:
        tg = ten_god(dg, s)
        ptype = TEN_GOD_TO_PATTERN.get(tg, tg)
        if ptype and ptype not in existing_types and tg not in ('比肩', '劫财'):
            out['pattern_candidates'].append({
                'pattern_type': ptype,
                'ten_god': tg,
                'stem': s,
                'position': pos,
                'basis': 'non_month_transparent_candidate',
                'evidence': [
                    f"{pos}={s}",
                    f"ten_god={tg}",
                    f"day_stem={dg}",
                ],
                'conditions': {'required': [], 'blocked': [], 'supported': []},
                'status': 'CANDIDATE',
                'boundary_note': '非月令透干定格候选, 仅并列参考, 不替代月令定格, 不判成格/成败',
            })
            existing_types.add(ptype)
            out['source'].append(f'{pos}_transparent_candidate')
    
    # PATCH-v3 地支藏干定格候选(四支地支): 经典中存在地支藏干定格用法
    # 仅作为候选并列, 不替代月令定格, 不判成格/成败
    hidden_stems_all = facts.get('hidden_stems', {}) or {}
    for pos in ('year', 'month', 'day', 'hour'):
        hs_list = hidden_stems_all.get(pos, []) or []
        for s in hs_list:
            if s and s != dg:
                tg = ten_god(dg, s)
                ptype = TEN_GOD_TO_PATTERN.get(tg, tg)
                if ptype and ptype not in existing_types and tg not in ('比肩', '劫财'):
                    out['pattern_candidates'].append({
                        'pattern_type': ptype,
                        'ten_god': tg,
                        'stem': s,
                        'position': pos + '_hidden',
                        'basis': 'branch_hidden_candidate',
                        'evidence': [
                            f"{pos}_branch={facts.get(pos + '_branch', '')}",
                            f"hidden_stem={s}",
                            f"ten_god={tg}",
                            f"day_stem={dg}",
                        ],
                        'conditions': {'required': [], 'blocked': [], 'supported': []},
                        'status': 'CANDIDATE',
                        'boundary_note': '地支藏干定格候选, 仅并列参考, 不替代月令定格, 不判成格/成败',
                    })
                    existing_types.add(ptype)
                    out['source'].append(f'{pos}_hidden_candidate')
    
    return out


if __name__ == '__main__':
    import io, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    from engines.common.l0_fact_builder import build
    gc001 = {'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']}
    facts = build(gc001)
    print('GC-001 pattern_candidates:', json.dumps(produce_pattern_candidates(facts), ensure_ascii=False))
    # 乙日酉月透辛 -> 七杀候选
    f2 = {'year': ['甲','子'], 'month': ['辛','酉'], 'day': ['乙','卯'], 'hour': ['丁','亥']}
    print('乙酉透辛:', json.dumps(produce_pattern_candidates(build(f2)), ensure_ascii=False))
