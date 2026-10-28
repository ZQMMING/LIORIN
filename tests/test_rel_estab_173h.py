# -*- coding: utf-8 -*-
"""PATCH-173-H 官杀制刃候选结构 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import guansha_zhiren_established
# 甲日卯月阳刃, 时干辛=正官 -> 候选结构
f1 = build({'year':['甲','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['辛','未']})
# 非阳刃(乙日卯月)
f2 = build({'year':['甲','子'],'month':['乙','卯'],'day':['乙','卯'],'hour':['辛','未']})
r1=guansha_zhiren_established(f1); r2=guansha_zhiren_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("阳刃+官=候选结构", r1['state'], 'SATISFIED')
ck("非阳刃=不成立", r2['state'], 'UNSATISFIED')
ck("note含七杀被合后续", '七杀被合' in r1.get('note',''), True)
ck("note含不等于刃格成", '刃格成' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
