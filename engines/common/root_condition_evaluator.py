# -*- coding: utf-8 -*-
"""PATCH-141B Root Condition Evaluator
只判根条件三态. 有根可判, 根深/根浅=UNKNOWN(NOT_IMPLEMENTED).
不判格局/旺衰/用神.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = json.load(open(ROOT/'registries/root_condition_registry_v1.json', encoding='utf-8'))['conditions']


def eval_root(condition_text, facts):
    """condition_text: 如'有根''财有根''根深'. facts: L0输出."""
    spec = REG.get(condition_text)
    if not spec:
        return {"condition": condition_text, "status": "UNKNOWN", "reason": "condition_not_registered"}
    if spec['eval'] == 'NOT_IMPLEMENTED':
        return {"condition": condition_text, "status": "UNKNOWN", "reason": spec['predicate']+'_not_implemented'}
    if spec['predicate'] == 'target_root':
        tr = facts.get('target_root_facts', {})
        v = tr.get(spec['target'])
        if v is None:
            return {"condition": condition_text, "status": "UNKNOWN", "reason": "target_root_missing_fact"}
        st = 'SATISFIED' if v else 'UNSATISFIED'
        return {"condition": condition_text, "status": st,
                "checked_predicate": f"target_root={spec['target']}", "predicate_value": v}
    has_root = any(facts.get('root_facts', {}).values())
    if spec['eval'] == 'exists':
        st = 'SATISFIED' if has_root else 'UNSATISFIED'
    else:  # not_exists
        st = 'SATISFIED' if not has_root else 'UNSATISFIED'
    return {"condition": condition_text, "status": st,
            "checked_predicate": spec['predicate'], "predicate_value": has_root}


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, '.')
    from engines.common.l0_fact_builder import build
    gc001 = {'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']}
    facts = build(gc001)  # 日支未藏乙=有根
    # 无根case: 乙日寅卯无? 用丙子日(午藏丁己, 无丙?丙在午)
    no_root = build({'year': ['甲','子'], 'month': ['丙','子'], 'day': ['丁','亥'], 'hour': ['己','酉']})
    for cond in ['有根', '无根', '财有根', '根深', '根浅', '未知条件']:
        print('GC001', cond, '->', json.dumps(eval_root(cond, facts), ensure_ascii=False))
    print('无根case 有根 ->', json.dumps(eval_root('有根', no_root), ensure_ascii=False))
