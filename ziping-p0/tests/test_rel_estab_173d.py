# -*- coding: utf-8 -*-
"""PATCH-173-D 伤官佩印成立 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import shangguan_peiyin_established
# 乙日巳月伤官, 时干壬=偏印
f1 = build({'year':['甲','子'],'month':['丙','巳'],'day':['乙','卯'],'hour':['壬','午']})
# 伤官无印(时干戊财)
f2 = build({'year':['甲','子'],'month':['丙','巳'],'day':['乙','卯'],'hour':['戊','辰']})
r1=shangguan_peiyin_established(f1); r2=shangguan_peiyin_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("伤官+见印=成立", r1['state'], 'SATISFIED')
ck("伤官无印=不成立", r2['state'], 'UNSATISFIED')
ck("note含伤官旺后续", '伤官旺' in r1.get('note',''), True)
ck("note含不等于格成", '不等于格成' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
