# -*- coding: utf-8 -*-
"""PATCH-141D golden: 合冲 evaluator"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.combination_condition_evaluator import eval_combination

gc001 = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
chong = build({'year': ['甲','子'], 'month': ['丙','午'], 'day': ['丁','亥'], 'hour': ['己','酉']})
# 子午冲

cases = [
    ("GC001 午未合", eval_combination('午未合', gc001)['status'], 'SATISFIED'),
    ("GC001 子丑合", eval_combination('子丑合', gc001)['status'], 'UNSATISFIED'),
    ("GC001 辰戌冲", eval_combination('辰戌冲', gc001)['status'], 'UNSATISFIED'),
    ("子午冲 存在", eval_combination('子午冲', chong)['status'], 'SATISFIED'),
    ("子午冲 无", eval_combination('子丑合', chong)['status'], 'UNSATISFIED'),
    ("合化木", eval_combination('合化木', gc001)['status'], 'UNKNOWN'),
    ("子未害", eval_combination('子未害', gc001)['status'], 'UNKNOWN'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
