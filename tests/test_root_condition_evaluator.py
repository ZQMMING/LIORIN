# -*- coding: utf-8 -*-
"""PATCH-141B-REPAIR golden: root evaluator 三态回归 + 防回归断言"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.root_condition_evaluator import eval_root

gc001 = {'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']}
facts = build(gc001)  # 日支未藏乙=日主有根
no_root = build({'year': ['甲','子'], 'month': ['丙','子'], 'day': ['丁','亥'], 'hour': ['己','酉']})

cases = [
    ("GC001 有根", eval_root('有根', facts)['status'], 'SATISFIED'),
    ("GC001 无根", eval_root('无根', facts)['status'], 'UNSATISFIED'),
    ("GC001 通根", eval_root('通根', facts)['status'], 'SATISFIED'),
    ("GC001 根深", eval_root('根深', facts)['status'], 'UNKNOWN'),
    ("GC001 根浅", eval_root('根浅', facts)['status'], 'UNKNOWN'),
    ("GC001 财有根", eval_root('财有根', facts)['status'], 'SATISFIED'),
    ("GC001 身有根", eval_root('身有根', facts)['status'], 'SATISFIED'),
    ("GC001 官有根", eval_root('官有根', facts)['status'], 'SATISFIED'),
    ("GC001 印有根", eval_root('印有根', facts)['status'], 'SATISFIED'),
    ("GC001 无气", eval_root('无气', facts)['status'], 'UNKNOWN'),
    ("GC001 未注册", eval_root('火星撞地球', facts)['status'], 'UNKNOWN'),
    ("无root case 有根", eval_root('有根', no_root)['status'], 'UNSATISFIED'),
]
fails = 0
for name, got, exp in cases:
    ok = got == exp
    fails += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {got} (期望{exp})")
print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
