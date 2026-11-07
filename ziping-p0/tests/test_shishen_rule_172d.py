# -*- coding: utf-8 -*-
"""PATCH-172-D 食神格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.shishen_rule_contract import shishen_rule_input
# 乙日午月: 本气丁=食神 -> 食神格
f = build({'year':['甲','子'],'month':['丁','午'],'day':['乙','卯'],'hour':['戊','辰']})
r = shishen_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("required含食神有根", '食神有根' in r['bucket']['required'], True)
ck("食带煞而无财在supported(205)", '食带煞而无财' in r['bucket']['supported'], True)
ck("不判成格", '格成' not in r['state'], True)
ck("boundary含非成格", '非成格' in r['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
