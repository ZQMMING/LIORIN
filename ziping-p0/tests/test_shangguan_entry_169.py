# -*- coding: utf-8 -*-
"""PATCH-169 伤官格入口 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日巳月: 巳本气丙=伤官 -> 伤官格入口
f1 = build({'year':['甲','子'],'month':['丙','巳'],'day':['乙','卯'],'hour':['丁','亥']})
f2 = build({'year':['甲','子'],'month':['辛','酉'],'day':['乙','卯'],'hour':['丁','亥']})
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("乙日巳月=伤官入口", f1['shangguan_entry']['is_entry'], True)
ck("乙日酉月=非伤官", f2['shangguan_entry']['is_entry'], False)
ck("note含格成边界", '≠伤官格成' in f1['shangguan_entry']['premise_note'], True)
ck("不判格成", '伤官格成' not in f1, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
