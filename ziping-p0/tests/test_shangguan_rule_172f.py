# -*- coding: utf-8 -*-
"""PATCH-172-F 伤官格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.shangguan_rule_contract import shangguan_rule_input
f = build({'year':['甲','子'],'month':['丙','巳'],'day':['乙','卯'],'hour':['丁','亥']})
r = shangguan_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("required含伤官有根", '伤官有根' in r['bucket']['required'], True)
ck("伤官旺在unknown", '伤官旺' in r['bucket']['unknown_pending'], True)
ck("不判成格", '格成' not in r['state'], True)
ck("boundary含非成格", '非成格' in r['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
