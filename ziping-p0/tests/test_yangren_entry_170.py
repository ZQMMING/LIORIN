# -*- coding: utf-8 -*-
"""PATCH-170 阳刃格入口 golden(仅五阳干)"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
f1 = build({'year':['甲','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['丁','亥']})  # 甲日卯月=刃
f2 = build({'year':['甲','子'],'month':['丙','午'],'day':['丙','寅'],'hour':['丁','亥']})  # 丙日午月=刃
f3 = build({'year':['甲','子'],'month':['甲','寅'],'day':['乙','卯'],'hour':['丁','亥']})  # 乙日阴干->非
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("甲日卯月=刃入口", f1['yangren_entry']['is_entry'], True)
ck("丙日午月=刃入口", f2['yangren_entry']['is_entry'], True)
ck("乙日阴干=非刃", f3['yangren_entry']['is_entry'], False)
# 五阳全矩阵 + 错位/阴干 False
cases5 = [
    ('戊日午月=刃', '戊','午', True),
    ('庚日酉月=刃', '庚','酉', True),
    ('壬日子月=刃', '壬','子', True),
    ('庚日午月=非刃(庚午错位)', '庚','午', False),
    ('丁日午月=阴干非刃', '丁','午', False),
]
for name,d,mz,exp in cases5:
    fx = build({'year':['甲','子'],'month':[d,mz],'day':[d,'寅'],'hour':['丁','亥']})
    ck(name, fx['yangren_entry']['is_entry'], exp)
ck("note含五阳干边界", '五阳干' in f1['yangren_entry']['premise_note'], True)
ck("不判格成", '刃格成' not in f1, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
