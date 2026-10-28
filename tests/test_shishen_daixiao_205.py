# -*- coding: utf-8 -*-
"""PATCH-205 食神格食带煞而无财(supported)+食神逢枭(blocked) golden"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.shishen_rule_contract import shishen_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 丁日午月: 午本气己=丁食神. 丁日七杀=癸, 财=庚辛, 偏印=乙
# G1 食带煞而无财: 有七杀癸 + 天干藏干均无庚辛
p1 = {'year': ['癸', '亥'], 'month': ['丙', '午'], 'day': ['丁', '亥'], 'hour': ['壬', '寅']}
c1 = shishen_rule_input(build(p1))
ck("G1 食带煞而无财->SAT", c1['conditions']['食带煞而无财'], 'SATISFIED')
ck("G1b 食神逢枭UNSAT", c1['conditions']['食神逢枭'], 'UNSATISFIED')

# G2 食神逢枭: 日支卯藏乙=偏印(藏干)
p2 = {'year': ['癸', '亥'], 'month': ['丙', '午'], 'day': ['丁', '卯'], 'hour': ['壬', '寅']}
c2 = shishen_rule_input(build(p2))
ck("G2 见偏印乙(藏干)->逢枭SAT", c2['conditions']['食神逢枭'], 'SATISFIED')

# G3 无七杀无偏印 -> 两项都UNSAT
p3 = {'year': ['甲', '寅'], 'month': ['丙', '午'], 'day': ['丁', '亥'], 'hour': ['壬', '寅']}
c3 = shishen_rule_input(build(p3))
ck("G3 无七杀->食带煞UNSAT", c3['conditions']['食带煞而无财'], 'UNSATISFIED')
ck("G3b 无偏印->逢枭UNSAT", c3['conditions']['食神逢枭'], 'UNSATISFIED')

# G4 state仍CANDIDATE非FAILED
ck("G4 state仍CANDIDATE", c2['state'], 'CANDIDATE')
# G5 blocked含食神逢枭
ck("G5 blocked含逢枭", '食神逢枭' in c2['bucket']['blocked'], True)
# G6 supported含食带煞
ck("G6 supported含食带煞", '食带煞而无财' in c1['bucket']['supported'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
