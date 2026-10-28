# -*- coding: utf-8 -*-
"""PATCH-185 运干x命干五行生克 golden (纯五行事实, 不作祸福)"""
import sys; sys.path.insert(0, '.')
from engines.common.relation_178 import yun_natal_relations

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

pillars = {'year': ['丙', '寅'], 'month': ['戊', '戌'], 'day': ['甲', '子'], 'hour': ['壬', '寅']}

# G1 运干甲(木) 生 命干丙(火) -> 运干生命干
r1 = yun_natal_relations({'year': ['甲', '辰']}, pillars)
ck("G1 运甲木生命丙火 -> 运干生命干",
   any(x['relation'] == '运干生命干' and x['stems'] == ['甲', '丙'] for x in r1), True)

# G2 运干甲(木) 克 命干戊(土) -> 运干克命干
ck("G2 运甲木克命戊土 -> 运干克命干",
   any(x['relation'] == '运干克命干' and x['stems'] == ['甲', '戊'] for x in r1), True)

# G3 同类(运甲木 vs 命甲木日干? 天干排除日干? 这里day干甲) 不记比和
ck("G3 同类不比和",
   not any(x['relation'] in ('比和', '同类') for x in r1), True)

# G4 运干壬(水) 克 命干丙(火)
r4 = yun_natal_relations({'year': ['壬', '午']}, pillars)
ck("G4 运壬水克命丙火 -> 运干克命干",
   any(x['relation'] == '运干克命干' and set(x['stems']) == {'壬', '丙'} for x in r4), True)

# 锁死 relation 层无祸福词
ck("锁死 relation层无吉凶祸福词",
   not any(any(w in x['relation'] for w in ['吉', '凶', '祸', '福', '喜', '忌']) for x in r1 + r4), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
