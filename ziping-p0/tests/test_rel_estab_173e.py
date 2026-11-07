# -*- coding: utf-8 -*-
"""PATCH-173-E 财生官成立 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import cai_shengguan_established
# 乙日: 月干庚=正官, 时干戊=正财 -> 财+正官
f1 = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','寅']})
# 乙日: 月干辛=七杀(非正官), 时干戊=财 -> 财+杀≠财生官
f2 = build({'year':['甲','子'],'month':['辛','酉'],'day':['乙','卯'],'hour':['戊','寅']})
r1=cai_shengguan_established(f1); r2=cai_shengguan_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("财+正官=成立", r1['state'], 'SATISFIED')
ck("财+七杀≠财生官", r2['state'], 'UNSATISFIED')
ck("note含不等于财旺生官", '不等于财旺生官' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
