# -*- coding: utf-8 -*-
"""PATCH-133 QTBJ climate_producer
只消费 ActivatedAssertion(predicate/object) -> climate_state.
不读 L0/Evidence/原文; object仅提取五行/天干, 不做寒暖判断.
"""
import json
import re

STEMS = set('甲乙丙丁戊己庚辛壬癸')
WUXING = {'木','火','土','金','水'}

_PRED = {
    'requires': 'primary',
    'secondary_requires': 'secondary',
    'avoids': 'avoid',
    'controls': 'control',
    'balances': 'balance',
    'needs': 'primary',
    'prefers': 'preference',
    'rejects': 'avoid',
}


def _extract(object_text: str):
    """从 object 短语提取 天干/五行, 不推断"""
    stems = [c for c in object_text if c in STEMS]
    wx = [c for c in object_text if c in WUXING]
    return stems, wx


def produce(activated: list) -> dict:
    """activated: [ActivatedAssertion]. 输出 climate_state. 无 state 时 ABSTAIN."""
    if not activated:
        return {"status": "ABSTAIN", "reason": "no_activated_assertion"}

    out = {"status": "PRODUCED", "primary": [], "secondary": [],
           "avoid": [], "control": [], "balance": [], "preference": [],
           "evidence": [], "matched_by": []}
    for aa in activated:
        bucket = _PRED.get(aa['predicate'])
        if not bucket:
            continue
        stems, wx = _extract(aa['object'])
        entry = {"stem": stems, "element": wx, "source_object": aa['object']}
        out[bucket].append(entry)
        out['evidence'].extend(aa.get('source_evidence', []))
        out['matched_by'].append(aa['assertion_id'])
    # primary 去重
    seen=set(); prim=[]
    for p in out['primary']:
        key=(tuple(p['stem']),tuple(p['element']))
        if key in seen: continue
        seen.add(key); prim.append(p)
    out['primary']=prim

    # PATCH-134 方案1: primary多值不选, 保留多候选
    if len(prim)>1:
        out['status']='MULTIPLE_CANDIDATES'
        out['reason']='primary_not_resolved_wait_condition_normalizer'
    elif prim:
        out['status']='PRODUCED'
    else:
        out['status']='ABSTAIN'
        out['reason']='no_primary'
    return out


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    demo = [
        {"assertion_id":"QTBJ-GC001","source_evidence":["QTBJ-022-001"],
         "predicate":"requires","object":"癸水润","matched_facts":[]},
        {"assertion_id":"QTBJ-X","source_evidence":["QTBJ-0xx"],
         "predicate":"avoids","object":"火土燥","matched_facts":[]},
    ]
    print(json.dumps(produce(demo), ensure_ascii=False))
    print('空:', json.dumps(produce([]), ensure_ascii=False))
