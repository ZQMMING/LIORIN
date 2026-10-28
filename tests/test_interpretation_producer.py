# -*- coding: utf-8 -*-
"""PATCH-159 Interpretation Producer三路径"""
import sys, json
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.pzzq_producer_v1 import produce_pattern_candidates
from engines.common.pzzq_resolver_v2 import resolve, evaluate_conditions
from engines.common.judgment_producer import produce_judgment
from engines.common.interpretation_producer import produce_interpretation
rows = [json.loads(l) for l in open('registries/assertions/pzzq_assertions.jsonl', encoding='utf-8')]
def judg(f, ptype='正官'):
    cs = [x for x in produce_pattern_candidates(f)['pattern_candidates'] if x['pattern_type']==ptype][0]
    return produce_judgment(cs, evaluate_conditions(resolve(cs, rows), f), rows)
sup = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
hit = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','亥']})
cai = build({'year':['癸','亥'],'month':['壬','戌'],'day':['乙','未'],'hour':['戊','午']})
i_sup = produce_interpretation(judg(sup))
i_hit = produce_interpretation(judg(hit))
i_pend = produce_interpretation(judg(cai,'正财'))
cases = [
    ('SUPPORTED释义', i_sup['status'], 'RECORDED'),
    ('反挂judgment_id', i_sup['judgment_id'], judg(sup)['judgment_id']),
    ('provenance后追溯', i_sup['based_on'], judg(sup)['assertion_ids']),
    ('NOT_SUPPORTED释义', i_hit['status'], 'RECORDED'),
    ('PENDING不产确定释义', i_pend['status'], 'PENDING_REVIEW'),
    ('PENDING plain_text空', i_pend['plain_text'], None),
    ('释义含非成格', '非成格' in i_sup['plain_text'], True),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
