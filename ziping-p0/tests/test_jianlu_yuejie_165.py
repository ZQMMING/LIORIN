# -*- coding: utf-8 -*-
"""PATCH-165 建禄月劫格入口Fact golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日卯月: 卯本气乙=比肩 -> 建禄
f1 = build({'year':['甲','子'],'month':['乙','卯'],'day':['乙','卯'],'hour':['丁','亥']})
# 乙日寅月: 寅本气甲=劫财 -> 月劫
f2 = build({'year':['甲','子'],'month':['甲','寅'],'day':['乙','卯'],'hour':['丁','亥']})
# 乙日戌月: 非建禄月劫
f3 = build({'year':['甲','子'],'month':['戊','戌'],'day':['乙','卯'],'hour':['丁','亥']})
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("乙日卯月=建禄", f1['jianlu_yuejie_entry']['type'], '建禄')
ck("乙日寅月=月劫", f2['jianlu_yuejie_entry']['type'], '月劫')
ck("乙日戌月=非入口", f3['jianlu_yuejie_entry']['is_entry'], False)
ck("取用入口复用财官印", '财' in f1['jianlu_yuejie_keystone'], True)
ck("不判身强", 'daymaster_strong' not in f1, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
