# -*- coding: utf-8 -*-
"""PATCH-156 官格三态全链: SUPPORTED/NOT_SUPPORTED/PENDING"""
import sys, json
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.pzzq_producer_v1 import produce_pattern_candidates
from engines.common.pzzq_resolver_v2 import resolve, evaluate_conditions
rows = [json.loads(l) for l in open('registries/assertions/pzzq_assertions.jsonl', encoding='utf-8')]
def guan(f):
    cs = [x for x in produce_pattern_candidates(f)['pattern_candidates'] if x['pattern_type']=='正官'][0]
    return evaluate_conditions(resolve(cs, rows), f)
# 乙日申月透庚官, 无财干, 官支申不被冲
sup = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
# 见财(戊透) -> blocked命中
hit = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','亥']})
cases = [
    ('SUPPORTED', guan(sup)['candidate_state']['candidate_direction'], 'SUPPORTED'),
    ('required SAT', guan(sup)['required_bundle']['bundle_status'], 'SATISFIED'),
    ('blocked CLEAR', guan(sup)['blocked_bundle']['bundle_status'], 'CLEAR'),
    ('见财命中NOT_SUPPORTED', guan(hit)['candidate_state']['candidate_direction'], 'NOT_SUPPORTED'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
