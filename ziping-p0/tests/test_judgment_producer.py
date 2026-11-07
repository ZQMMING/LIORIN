# -*- coding: utf-8 -*-
"""PATCH-158 Judgment Producer三路径golden + 158.1 provenance加固"""
import sys, json
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.pzzq_producer_v1 import produce_pattern_candidates
from engines.common.pzzq_resolver_v2 import resolve, evaluate_conditions
from engines.common.judgment_producer import produce_judgment
rows = [json.loads(l) for l in open('registries/assertions/pzzq_assertions.jsonl', encoding='utf-8')]
def judg(f, ptype='正官'):
    cs = [x for x in produce_pattern_candidates(f)['pattern_candidates'] if x['pattern_type']==ptype][0]
    r = evaluate_conditions(resolve(cs, rows), f)
    return produce_judgment(cs, r, rows)
sup = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
hit = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','亥']})
cai = build({'year':['癸','亥'],'month':['壬','戌'],'day':['乙','未'],'hour':['戊','午']})
# 158.1 歧义: 同词对应两条assertion -> fail-closed
amb = produce_judgment({'pattern_type':'正官'},
    {'candidate_state':{'candidate_direction':'SUPPORTED'},
     'conditions':{'required':['官有根'],'blocked':[]}},
    [{'assertion_id':'A1','subject':'官格','object':'官有根','source_evidence':['E1']},
     {'assertion_id':'A2','subject':'官格','object':'官有根','source_evidence':['E2']}])
cases = [
    ('SUPPORTED产Judgment', judg(sup)['status'], 'RECORDED'),
    ('SUPPORTED direction', judg(sup)['direction'], 'SUPPORTED'),
    ('SUPPORTED有provenance', len(judg(sup)['assertion_ids']) > 0, True),
    ('NOT_SUPPORTED', judg(hit)['status'], 'RECORDED'),
    ('NOT_SUPPORTED direction', judg(hit)['direction'], 'NOT_SUPPORTED'),
    ('财格PENDING不产确定', judg(cai,'正财')['status'], 'PENDING_REVIEW'),
    ('歧义不唯一fail-closed', amb['status'], 'AMBIGUOUS_PROVENANCE_FAIL_CLOSED'),
    # 158.2 Schema完整性: RECORDED Judgment必填字段齐全
    ('Schema字段齐', all(k in judg(sup) for k in
        ['judgment_id','subject','predicate','object','direction','state',
         'evidence','assertion_ids','source','provenance','authorization','status']), True),
    ('非成格标注', '非成格' in judg(sup).get('note',''), True),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
