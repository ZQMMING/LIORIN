# -*- coding: utf-8 -*-
"""PATCH-168 七煞格入口 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日酉月: 酉本气辛=七杀 -> 七煞格入口
f1 = build({'year':['甲','子'],'month':['辛','酉'],'day':['乙','卯'],'hour':['丁','亥']})
f2 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['丁','亥']})
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("乙日酉月=七煞入口", f1['qisha_entry']['is_entry'], True)
ck("乙日午月=非七煞", f2['qisha_entry']['is_entry'], False)
ck("note含身强逢制后续", '身强' in f1['qisha_entry']['premise_note'], True)
ck("不判格成", '煞格成' not in f1, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
