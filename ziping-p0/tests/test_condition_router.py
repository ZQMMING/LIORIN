# -*- coding: utf-8 -*-
"""PATCH-141F golden: condition router 接线"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition

gc001 = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
tou = build({'year': ['甲','子'], 'month': ['辛','酉'], 'day': ['乙','卯'], 'hour': ['丁','亥']})

cases = [
    ("有根", route_condition('有根', gc001)['status'], 'SATISFIED'),
    ("财有根(target_root)", route_condition('财有根', gc001)['status'], 'SATISFIED'),
    ("根深", route_condition('根深', gc001)['status'], 'UNKNOWN'),
    ("财透(GC未透)", route_condition('财透', gc001)['status'], 'UNSATISFIED'),
    ("杀透(酉透辛)", route_condition('杀透', tou)['status'], 'SATISFIED'),
    ("午未合", route_condition('午未合', gc001)['status'], 'SATISFIED'),
    ("子丑合", route_condition('子丑合', gc001)['status'], 'UNSATISFIED'),
    ("合化木", route_condition('合化木', gc001)['status'], 'UNKNOWN'),
    ("身强(禁止)", route_condition('身强', gc001)['status'], 'UNKNOWN'),
    ("得令(乙戌不supports)", route_condition('得令', gc001)['status'], 'UNSATISFIED'),
    ("未注册", route_condition('火星撞地球', gc001)['status'], 'UNKNOWN'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
