# -*- coding: utf-8 -*-
"""PATCH-172-G 建禄月劫Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.jianlu_rule_contract import jianlu_rule_input
f = build({'year':['甲','子'],'month':['乙','卯'],'day':['乙','卯'],'hour':['戊','辰']})
r = jianlu_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("无required", len(r['bucket']['required'])==0, True)
ck("财官煞食为premise", '财' in r['bucket']['supported_premise'], True)
ck("取何者为用unknown", '取何者为用' in r['bucket']['unknown_pending'], True)
ck("不判成格", '格成' not in r['state'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
