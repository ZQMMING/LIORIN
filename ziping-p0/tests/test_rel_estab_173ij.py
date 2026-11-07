# -*- coding: utf-8 -*-
"""PATCH-173-I/J 阳刃财印配合/食伤泄刃 golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.relation_established_173 import (caiyin_peiyangren_established,
    shishang_xieren_established)
# 甲日卯月阳刃; 财=戊己, 印=壬癸, 食伤=丙丁
# I: 年壬印+时戊财 -> 财印配合
fI = build({'year':['壬','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['戊','辰']})
# J: 时干丁=伤官 -> 泄刃
fJ = build({'year':['甲','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['丁','卯']})
rI=caiyin_peiyangren_established(fI); rJ=shishang_xieren_established(fJ)
print(rI['state'], rJ['state'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("阳刃+财+印=配合", rI['state'], 'SATISFIED')
ck("阳刃+食伤=泄刃", rJ['state'], 'SATISFIED')
ck("I note含不相碍后续", '不相碍' in rI.get('note',''), True)
ck("J note含刃旺后续", '刃' in rJ.get('note',''), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
