# -*- coding: utf-8 -*-
"""PATCH-173-C 伤官生财成立 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import shangguan_shengcai_established
# 乙日巳月伤官, 时戊辰财有根
f1 = build({'year':['甲','子'],'month':['丙','巳'],'day':['乙','卯'],'hour':['戊','辰']})
# 非伤官格
f2 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['戊','辰']})
r1=shangguan_shengcai_established(f1); r2=shangguan_shengcai_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("伤官+见财=成立", r1['state'], 'SATISFIED')
ck("非伤官格=不成立", r2['state'], 'UNSATISFIED')
ck("note含财无根不等于关系不存在", '财无根不等于关系不存在' in r1.get('note',''), True)
ck("note含财有根为后续", '财有根' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
