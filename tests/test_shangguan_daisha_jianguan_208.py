# -*- coding: utf-8 -*-
"""PATCH-208 伤官格伤官带煞而无财(supported)+伤官见官(blocked) golden"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.shangguan_rule_contract import shangguan_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 庚日子月: 子本气癸=庚伤官. 庚日七杀=丙, 正官=丁, 财=甲乙
# G1 伤官带煞而无财: 见丙七杀 + 天干藏干均无甲乙财
p1 = {'year': ['丙', '子'], 'month': ['戊', '子'], 'day': ['庚', '子'], 'hour': ['丙', '子']}
c1 = shangguan_rule_input(build(p1))
ck("G1 伤官带煞而无财->SAT", c1['conditions']['伤官带煞而无财'], 'SATISFIED')
ck("G1b 伤官见官UNSAT", c1['conditions']['伤官见官'], 'UNSATISFIED')

# G2 伤官见官: 天干见丁正官
p2 = {'year': ['丁', '丑'], 'month': ['戊', '子'], 'day': ['庚', '子'], 'hour': ['丙', '子']}
c2 = shangguan_rule_input(build(p2))
ck("G2 见正官丁->伤官见官SAT", c2['conditions']['伤官见官'], 'SATISFIED')

# G3 无七杀无正官无财问题 -> 两项UNSAT
p3 = {'year': ['戊', '子'], 'month': ['戊', '子'], 'day': ['庚', '子'], 'hour': ['戊', '子']}
c3 = shangguan_rule_input(build(p3))
ck("G3 无七杀->带煞UNSAT", c3['conditions']['伤官带煞而无财'], 'UNSATISFIED')
ck("G3b 无正官->见官UNSAT", c3['conditions']['伤官见官'], 'UNSATISFIED')

# G4 state仍CANDIDATE非FAILED
ck("G4 state仍CANDIDATE", c2['state'], 'CANDIDATE')
# G5 blocked含伤官见官
ck("G5 blocked含见官", '伤官见官' in c2['bucket']['blocked'], True)
# G6 supported含带煞
ck("G6 supported含带煞", '伤官带煞而无财' in c1['bucket']['supported'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
