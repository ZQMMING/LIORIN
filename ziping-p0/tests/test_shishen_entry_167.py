# -*- coding: utf-8 -*-
"""PATCH-167 食神格入口 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日午月: 午本气丁=食神 -> 食神格入口
f1 = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['丁','亥']})
# 乙日卯月: 比肩 -> 非入口
f2 = build({'year':['甲','子'],'month':['乙','卯'],'day':['乙','卯'],'hour':['丁','亥']})
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("乙日午月=食神格入口", f1['shishen_entry']['is_entry'], True)
ck("乙日卯月=非入口", f2['shishen_entry']['is_entry'], False)
ck("有note说明非格成", '≠食神格成' in f1['shishen_entry']['premise_note'], True)
ck("不判格成", '格成' not in f1 and 'shishen_ge_cheng' not in f1, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
