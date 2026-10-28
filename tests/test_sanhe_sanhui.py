# -*- coding: utf-8 -*-
"""PATCH-154 三合/三会 Relation Fact (仅结构存在)"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition

sanhe = build({'year':['甲','申'],'month':['丙','子'],'day':['乙','辰'],'hour':['丁','午']})  # 申子辰
sanhui = build({'year':['甲','寅'],'month':['丙','卯'],'day':['乙','辰'],'hour':['丁','午']})  # 寅卯辰
plain = build({'year':['甲','子'],'month':['丙','亥'],'day':['乙','卯'],'hour':['丁','午']})  # 无局
cases = [
    ('申子辰三合', route_condition('申子辰合水', sanhe)['status'], 'SATISFIED'),
    ('申子辰非局', route_condition('申子辰合水', plain)['status'], 'UNSATISFIED'),
    ('寅卯辰三会木', route_condition('寅卯辰三会木', sanhui)['status'], 'SATISFIED'),
    ('寅卯辰非局', route_condition('寅卯辰三会木', plain)['status'], 'UNSATISFIED'),
    ('三会火非局', route_condition('巳午未三会火', plain)['status'], 'UNSATISFIED'),
    ('化水局未注册', route_condition('水局成化', sanhe)['status'], 'UNKNOWN'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
