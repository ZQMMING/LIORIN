# -*- coding: utf-8 -*-
"""PATCH-141C golden: 透干 evaluator 三态"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.transparent_condition_evaluator import eval_transparent

gc001 = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
tou = build({'year': ['甲','子'], 'month': ['辛','酉'], 'day': ['乙','卯'], 'hour': ['丁','亥']})
# 酉藏辛透 -> 乙日辛=七杀 -> 杀透 SATISFIED

cases = [
    ("GC001 财透", eval_transparent('财透', gc001)['status'], 'UNSATISFIED'),
    ("GC001 官透", eval_transparent('官透', gc001)['status'], 'UNSATISFIED'),
    ("透辛 杀透", eval_transparent('杀透', tou)['status'], 'SATISFIED'),
    ("透辛 财透", eval_transparent('财透', tou)['status'], 'UNSATISFIED'),
    ("多目标", eval_transparent('财官双透', gc001)['status'], 'UNKNOWN'),
    ("未注册", eval_transparent('火星', gc001)['status'], 'UNKNOWN'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
