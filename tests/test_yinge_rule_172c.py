# -*- coding: utf-8 -*-
"""PATCH-172-C 印格Rule输入契约 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.yinge_rule_contract import yinge_rule_input
# 乙日子月: 本气癸=偏印 -> 印格
f = build({'year':['甲','子'],'month':['壬','子'],'day':['乙','卯'],'hour':['丁','亥']})
r = yinge_rule_input(f)
print(r['conditions'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("state=CANDIDATE", r['state'], 'CANDIDATE')
ck("blocked不含贪财破印", '贪财破印' not in r['bucket']['blocked'], True)
ck("贪财破印在unknown", '贪财破印' in r['bucket']['unknown_pending'], True)
ck("不判成格", '格成' not in r['state'], True)
ck("boundary含财印同现不等于贪财破印", '贪财破印' in r['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
