# -*- coding: utf-8 -*-
"""PATCH-173-B 食神制杀结构成立 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import shishen_zhisha_established
# 乙日午月食神, 时干辛=七杀 -> 结构SAT
f1 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['辛','巳']})
# 食神格但无杀(时干戊财)
f2 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['戊','辰']})
r1=shishen_zhisha_established(f1); r2=shishen_zhisha_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("食神+见杀=结构SAT", r1['state'], 'SATISFIED')
ck("食神无杀=不成立", r2['state'], 'UNSATISFIED')
ck("note含不等于美格/有效", '不等于制杀有效' in r1.get('note',''), True)
ck("note含身强未授权", '160' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
