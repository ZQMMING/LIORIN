# -*- coding: utf-8 -*-
"""PATCH-173-A 食神生财成立 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import shisheng_shengcai_established
# 乙日午月食神格, 时戊辰藏戊=正财有根
f1 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['戊','辰']})
# 非食神格(卯月建禄)
f2 = build({'year':['甲','子'],'month':['乙','卯'],'day':['乙','卯'],'hour':['戊','辰']})
r1=shisheng_shengcai_established(f1); r2=shisheng_shengcai_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("食神+财有根=成立", r1['state'], 'SATISFIED')
ck("非食神格=不成立", r2['state'], 'UNSATISFIED')
ck("不判格成", '格成' not in r1.get('state',''), True)
ck("成立note含不等于格成", '不等于格成' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
