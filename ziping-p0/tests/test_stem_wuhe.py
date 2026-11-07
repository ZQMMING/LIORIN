# -*- coding: utf-8 -*-
"""PATCH-153 天干五合 Relation Fact assert回归 (仅存在, 不判合化)"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition

he = build({'year':['甲','子'],'month':['己','亥'],'day':['乙','卯'],'hour':['丁','午']})  # 甲己
nohe = build({'year':['甲','子'],'month':['丙','亥'],'day':['乙','卯'],'hour':['丁','午']})  # 无甲己
cases = [
    ('甲己合存在', route_condition('甲己合', he)['status'], 'SATISFIED'),
    ('甲己合不存在', route_condition('甲己合', nohe)['status'], 'UNSATISFIED'),
    ('乙庚合存在', route_condition('乙庚合', build({'year':['乙','子'],'month':['庚','亥'],'day':['丙','寅'],'hour':['丁','午']}))['status'], 'SATISFIED'),
    ('合化木未注册', route_condition('合化木', he)['status'], 'UNKNOWN'),
    ('合而不化未注册', route_condition('合而不化', he)['status'], 'UNKNOWN'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
