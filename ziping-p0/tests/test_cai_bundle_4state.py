# -*- coding: utf-8 -*-
"""PATCH-144 财格required bundle四态golden: UNSAT>UNKNOWN>SAT"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition
from engines.common.condition_bundle import aggregate_required

# A: 乙日戌月(戌藏戊辛丁), 财=土有根=>财有根SAT; 戊辛丁未透=>财透UNSAT
A = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
# C: 乙日戌月, 时干戊透=>财透SAT; 戌藏戊=财根SAT
C = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['戊','午']})
# D: 丁日, 时干庚透=>财透SAT(丁火财=金); 寅卯辰子藏干无金=>财有根UNSAT
D = build({'year': ['甲','寅'], 'month': ['丁','卯'], 'day': ['丁','午'], 'hour': ['庚','子']})
# B: required含古文词"配合"(no_router=UNKNOWN)
B = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})

cases = [
    ('A 财SAT财透UNSAT', A, ['财有根','财透'], 'UNSATISFIED'),
    ('C 财SAT财透SAT', C, ['财有根','财透'], 'SATISFIED'),
    ('D 财透SAT财有根UNSAT', D, ['财有根','财透'], 'UNSATISFIED'),
    ('B 含配合UNKNOWN', B, ['财有根','配合'], 'UNKNOWN'),
]
fails = 0
for name, f, req, exp in cases:
    items = [{'condition': c, 'status': route_condition(c, f)['status']} for c in req]
    got = aggregate_required(items)['bundle_status']
    ok = got == exp
    fails += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {[i['status'] for i in items]} -> {got} (期望{exp})")
print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
