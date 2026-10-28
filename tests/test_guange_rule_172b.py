# -*- coding: utf-8 -*-
"""PATCH-172-B 官格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.guange_rule_contract import guange_rule_input
# 乙日申月: 本气庚=正官 -> 官格
f = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
r = guange_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("官有根三态", r['conditions']['官有根'] in ('SATISFIED','UNSATISFIED','UNKNOWN'), True)
ck("官星受冲已接", '官星受冲' in r['conditions'], True)
ck("不判成格", '格成' not in r['state'] and 'is_success' not in r, True)
ck("boundary含见财非阻断", '见财≠' in r['boundary_note'] or '见财为' in r['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
