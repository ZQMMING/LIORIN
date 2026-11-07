# -*- coding: utf-8 -*-
"""PATCH-162 root_type Signal golden: 两档HEAVY/LIGHT, 禁数值"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日: 禄=卯(HEAVY), 墓余气=未(LIGHT)
f = build({'year':['甲','未'],'month':['戊','寅'],'day':['乙','卯'],'hour':['丁','亥']})
rt = f['root_weight_class_facts']
print(rt)
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("卯=禄HEAVY", rt.get('day',{}).get('root_type'), '禄')
ck("卯=HEAVY", rt.get('day',{}).get('class'), 'HEAVY')
ck("未=余气LIGHT", rt.get('year',{}).get('class'), 'LIGHT')
# 禁数值: class只有HEAVY/LIGHT
vals=set(x['class'] for x in rt.values())
ck("只两档无数值", vals <= {'HEAVY','LIGHT'}, True)
# 不直出身强
ck("无身强字段", 'daymaster_strong' not in f and 'root_score' not in f, True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
