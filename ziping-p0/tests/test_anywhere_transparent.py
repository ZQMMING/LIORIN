# -*- coding: utf-8 -*-
"""PATCH-152.1 见财/印/官 anywhere assert回归"""
import sys, json
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition
from engines.common.pzzq_producer_v1 import produce_pattern_candidates
from engines.common.pzzq_resolver_v2 import resolve, evaluate_conditions

rows = [json.loads(l) for l in open('registries/assertions/pzzq_assertions.jsonl', encoding='utf-8')]

# 官格链
def guan(f):
    cs = [x for x in produce_pattern_candidates(f)['pattern_candidates'] if x['pattern_type']=='正官'][0]
    return evaluate_conditions(resolve(cs, rows), f)

# 乙日(财=土,官=金,印=水)
guancase_sat = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','亥']})  # 见财(戊)
guancase_none = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})  # 无土

cases = [
    # 见财SAT/UNSAT
    ('见财SAT', route_condition('见财', guancase_sat)['status'], 'SATISFIED'),
    ('见财UNSAT', route_condition('见财', guancase_none)['status'], 'UNSATISFIED'),
    # 见印(乙日印=水, 申月壬=水印透? 天干无壬癸则UNSAT; 造一个有癸)
    ('见印UNSAT(无水印干)', route_condition('见印', guancase_none)['status'], 'UNSATISFIED'),
    ('见印SAT', route_condition('见印', build({'year':['癸','亥'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']}))['status'], 'SATISFIED'),
    # 见官(乙日官=金, 申月庚透=官)
    ('见官SAT', route_condition('见官', guancase_none)['status'], 'SATISFIED'),
    # 日干不误触发: 乙日, 日干乙本身非财官印, 不影响
    ('日干不误触发', route_condition('见官', build({'year':['甲','子'],'month':['丁','未'],'day':['乙','亥'],'hour':['丙','子']}))['status'], 'UNSATISFIED'),
    # 财透(月令透) vs 见财(anywhere) 隔离: 戌月财透但天干无戊己? 区分
    ('财透=月令透(非anywhere)', route_condition('财透', build({'year':['癸','亥'],'month':['壬','戌'],'day':['乙','未'],'hour':['壬','午']}))['status'], 'UNSATISFIED'),
    # 官格链: 见财SAT->BLOCKED->NOT_SUPPORTED
    ('官格见财BLOCKED', guan(guancase_sat)['blocked_bundle']['bundle_status'], 'BLOCKED'),
    ('官格见财direction', guan(guancase_sat)['candidate_state']['candidate_direction'], 'NOT_SUPPORTED'),
    # 无见财但刑冲破害UNKNOWN -> BLOCK_UNKNOWN -> PENDING
    ('官格无见财blocked CLEAR', guan(guancase_none)['blocked_bundle']['bundle_status'], 'CLEAR'),
    ('官格无见财SUPPORTED', guan(guancase_none)['candidate_state']['candidate_direction'], 'SUPPORTED'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
