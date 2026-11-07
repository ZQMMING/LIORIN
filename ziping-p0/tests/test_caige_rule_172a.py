# -*- coding: utf-8 -*-
"""PATCH-172-A 财格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.caige_rule_contract import caige_rule_input
# 乙日戌月: 月令本气戊=正财 -> 财格
f = build({'year':['甲','子'],'month':['戊','戌'],'day':['乙','卯'],'hour':['丁','亥']})
r = caige_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("财太露保持UNKNOWN", r['conditions']['财太露'], 'UNKNOWN')
ck("不判成格", 'is_success' not in r and '格成' not in r['state'], True)
ck("boundary含财透≠财旺", '财透≠财旺' in r['boundary_note'], True)
# required三桶齐全
ck("required含财有根", '财有根' in r['bucket']['required'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
