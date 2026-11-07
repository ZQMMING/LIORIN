# -*- coding: utf-8 -*-
"""PATCH-173-G 财印三者同现 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import cai_yin_xiangsui_established
# 乙日: 年壬=印, 月庚=正官, 时戊=财 -> 三者全
f1 = build({'year':['壬','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','寅']})
# 缺印(年甲)
f2 = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['戊','寅']})
r1=cai_yin_xiangsui_established(f1); r2=cai_yin_xiangsui_established(f2)
print(r1['state'], r2['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("财+官+印=三者同现", r1['state'], 'SATISFIED')
ck("缺印=不成立", r2['state'], 'UNSATISFIED')
ck("note含不等于护官成立", '不等于护官成立' in r1.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
