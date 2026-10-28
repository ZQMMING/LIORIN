# -*- coding: utf-8 -*-
"""PATCH-141C Transparent Condition Evaluator
只判月令藏干某目标十神是否透干. 不判格局/旺衰/用神."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engines.common.l0_fact_builder import ten_god

ROOT = Path(__file__).resolve().parents[2]
REG = json.load(open(ROOT/'registries/transparent_condition_registry_v1.json', encoding='utf-8'))['conditions']


def eval_transparent(condition_text, facts):
    spec = REG.get(condition_text)
    if not spec:
        return {"condition": condition_text, "status": "UNKNOWN", "reason": "condition_not_registered"}
    if spec.get('eval') == 'NOT_IMPLEMENTED':
        return {"condition": condition_text, "status": "UNKNOWN", "reason": spec['predicate']+'_not_implemented'}
    if spec.get('source') == 'anywhere':
        cat = spec['target_category']
        ah = facts.get('any_stem_has_ten_god', {})
        if cat not in ah:
            return {"condition": condition_text, "status": "UNKNOWN", "reason": "anywhere_fact_missing"}
        st = 'SATISFIED' if ah[cat] else 'UNSATISFIED'
        return {"condition": condition_text, "status": st, "checked_predicate": f"any_stem_has_{cat}"}
    target = spec['target_ten_god']
    dg = facts['day_stem']
    transparent = facts.get('month_transparent', [])
    if not transparent:
        return {"condition": condition_text, "status": "UNSATISFIED",
                "checked_predicate": "month_transparent", "predicate_value": transparent}
    # 透干列表中, 该天干对日主的十神是否=target
    hit = [s for s in transparent if ten_god(dg, s) == target]
    st = 'SATISFIED' if hit else 'UNSATISFIED'
    return {"condition": condition_text, "status": st,
            "checked_predicate": f"transparent_ten_god={target}", "hit": hit}


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, '.')
    from engines.common.l0_fact_builder import build
    gc001 = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
    print('GC-001 戌藏戊辛丁, transparent=', gc001['month_transparent'])
    for c in ['财透','官透','印透','杀透','财官双透','火星']:
        print(c, '->', json.dumps(eval_transparent(c, gc001), ensure_ascii=False))
