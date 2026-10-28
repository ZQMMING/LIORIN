# -*- coding: utf-8 -*-
"""PATCH-163 刑破害 Relation Fact golden: 仅结构存在, 不判吉凶"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 子未害, 子酉破, 子卯刑, 寅巳申三刑
f = build({'year':['甲','未'],'month':['庚','酉'],'day':['乙','卯'],'hour':['丙','子']})
c = f['combination_facts']
print("liuhai:", c['liuhai'], "liupo:", c['liupo'], "sanxing:", c['sanxing'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("子未相害", '子未相害' in c['liuhai'], True)
ck("子酉相破", '子酉相破' in c['liupo'], True)
ck("子卯相刑", '子卯相刑' in c['sanxing'], True)
# 寅巳申: 此盘有巳但无寅申, 不应出三刑
ck("寅巳申不全不判三刑", '寅巳申三刑' in c['sanxing'], False)
# 不判吉凶/身强弱
ck("无吉凶字段", not any(k in f for k in ['punished','injury','strong']), True)
# 干净盘无刑破害
f2 = build({'year':['甲','子'],'month':['丙','寅'],'day':['乙','卯'],'hour':['丁','亥']})
ck("干净盘无liuhai", len(f2['combination_facts']['liuhai'])==0, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
