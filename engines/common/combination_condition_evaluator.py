# -*- coding: utf-8 -*-
"""PATCH-141D Combination Condition Evaluator
只判指定地支pair关系是否存在. 不判合化/冲动/喜忌/冲开."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REG = json.load(open(ROOT/'registries/combination_condition_registry_v1.json', encoding='utf-8'))['conditions']


def _has_pair(relation_list, pair):
    s = set(pair)
    return any(set(r) == s for r in relation_list)


def eval_combination(condition_text, facts):
    spec = REG.get(condition_text)
    if not spec:
        return {"condition": condition_text, "status": "UNKNOWN", "reason": "condition_not_registered"}
    cf = facts.get('combination_facts', {})
    if spec['kind'] == 'wuhe':
        rel = facts.get('stem_combination_facts', {}).get('wuhe', [])
        hit = _has_pair(rel, spec['pair'])
    elif spec['kind'] in ('sanhe', 'sanhui'):
        rel = cf.get(spec['kind'], [])
        hit = spec['name'] in rel
    elif spec['kind'] == 'target':
        tr = facts.get('target_relation_facts', {})
        rel = list(tr.keys())
        hit = bool(tr.get(spec['name'], False))
    else:
        rel = cf.get(spec['kind'], [])
        hit = _has_pair(rel, spec['pair'])
    key = spec.get('name', spec.get('pair'))
    return {"condition": condition_text,
            "status": "SATISFIED" if hit else "UNSATISFIED",
            "checked": f"{spec['kind']}={key}", "present_pairs": rel}


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, str(ROOT))
    from engines.common.l0_fact_builder import build
    gc001 = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
    print('combination:', gc001['combination_facts'])
    for c in ['午未合','子丑合','辰戌冲','巳亥冲','合化木','子未害']:
        print(c, '->', json.dumps(eval_combination(c, gc001), ensure_ascii=False))
