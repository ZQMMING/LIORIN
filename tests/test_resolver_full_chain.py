# -*- coding: utf-8 -*-
"""PATCH-150 Resolver真实全链 assert/fail 回归"""
import sys, json
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.pzzq_producer_v1 import produce_pattern_candidates
from engines.common.pzzq_resolver_v2 import resolve, evaluate_conditions

rows = [json.loads(l) for l in open('registries/assertions/pzzq_assertions.jsonl', encoding='utf-8')]

def chain(facts, pattern):
    cands = [c for c in produce_pattern_candidates(facts)['pattern_candidates'] if c['pattern_type'] == pattern]
    if not cands: return None
    return evaluate_conditions(resolve(cands[0], rows), facts)

A = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['戊','午']})
B = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
# 官格: 乙日申月透庚
G = build({'year': ['甲','子'], 'month': ['庚','申'], 'day': ['乙','卯'], 'hour': ['丁','亥']})

cases = [
    ('A required', chain(A,'正财')['required_bundle']['bundle_status'], 'SATISFIED'),
    ('A direction', chain(A,'正财')['candidate_state']['candidate_direction'], 'PENDING'),
    ('B direction', chain(B,'正财')['candidate_state']['candidate_direction'], 'NOT_SUPPORTED'),
    ('官格 required', chain(G,'正官')['required_bundle']['bundle_status'], 'SATISFIED'),
    ('官格 blocked', chain(G,'正官')['blocked_bundle']['bundle_status'], 'CLEAR'),
    ('官格 direction', chain(G,'正官')['candidate_state']['candidate_direction'], 'SUPPORTED'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
