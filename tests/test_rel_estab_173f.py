# -*- coding: utf-8 -*-
"""PATCH-173-F 印化杀结构关系 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import yin_huasha_established
# 乙日: 月干辛=七杀, 时干壬=偏印 -> 印+杀
f1 = build({'year':['甲','子'],'month':['辛','酉'],'day':['乙','卯'],'hour':['壬','午']})
# 印+正官(庚)无杀 -> 不等于印化杀
f2 = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['壬','午']})
r1=yin_huasha_established(f1); r2=yin_huasha_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("印+杀=成立", r1['state'], 'SATISFIED')
ck("印+正官≠印化杀", r2['state'], 'UNSATISFIED')
ck("note含不等于化杀有效", '不等于化杀有效' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
