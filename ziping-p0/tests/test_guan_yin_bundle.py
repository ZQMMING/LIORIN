# -*- coding: utf-8 -*-
"""PATCH-145 官格/印格 bundle golden (复用基础设施, 零引擎改动)"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition
from engines.common.condition_bundle import aggregate_required

def bundle(facts, req):
    items = [{'condition': c, 'status': route_condition(c, facts)['status']} for c in req]
    return aggregate_required(items)['bundle_status'], items

# 官格: 乙日正官=庚. 乙日申月(藏庚壬戊), 月干庚透=正官透SAT, 官有根SAT
guan_sat = build({'year': ['甲','子'], 'month': ['庚','申'], 'day': ['乙','卯'], 'hour': ['丁','亥']})
# 印格: 乙日亥月(亥藏壬=正印), 壬透=印透SAT, 印有根SAT
yin_sat = build({'year': ['甲','子'], 'month': ['壬','亥'], 'day': ['乙','卯'], 'hour': ['丁','亥']})
# 官格反例: 官无根
guan_unsat = build({'year': ['甲','寅'], 'month': ['丁','卯'], 'day': ['丁','午'], 'hour': ['己','未']})

req_guan = ['官有根', '官透']
req_yin = ['印有根', '印透']
cases = [
    ('官格SAT', guan_sat, req_guan, 'SATISFIED'),
    ('印格SAT', yin_sat, req_yin, 'SATISFIED'),
    ('官格UNSAT', guan_unsat, req_guan, 'UNSATISFIED'),
]
fails=0
for name, f, req, exp in cases:
    got, items = bundle(f, req); ok=got==exp; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {[i['status'] for i in items]} -> {got} (期望{exp})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
