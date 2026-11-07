# -*- coding: utf-8 -*-
"""PATCH-172-H 阳刃格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.yangren_rule_contract import yangren_rule_input
f = build({'year':['甲','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['丁','亥']})
r = yangren_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("无required", len(r['bucket']['required'])==0, True)
ck("官杀制刃为premise", '官杀制刃' in r['bucket']['supported_premise'], True)
ck("刃格成在unknown", '刃格成' in r['bucket']['unknown_pending'], True)
ck("不判成格", '格成' not in r['state'], True)
ck("boundary含财印并见不等于成格", '不相碍' in r['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
