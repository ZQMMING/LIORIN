# -*- coding: utf-8 -*-
"""PATCH-207 七杀格杀混官 supported结构 golden (正官非七杀)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.qisha_rule_contract import qisha_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 甲日申月: 申本气庚=甲七杀. 甲日正官=辛, 七杀=庚
# G1 天干见辛(正官) -> 杀混官 SAT
p1 = {'year': ['辛', '酉'], 'month': ['壬', '申'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}
c1 = qisha_rule_input(build(p1))
ck("G1 天干见正官辛->杀混官SAT", c1['conditions']['杀混官'], 'SATISFIED')

# G2 天干见庚(七杀)不见辛 -> UNSAT (七杀非正官)
p2 = {'year': ['庚', '申'], 'month': ['壬', '申'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}
c2 = qisha_rule_input(build(p2))
ck("G2 天干见七杀庚->UNSAT", c2['conditions']['杀混官'], 'UNSATISFIED')

# G3 正官藏干(酉藏辛)天干无辛 -> UNSAT (只查天干)
p3 = {'year': ['癸', '酉'], 'month': ['壬', '申'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}
c3 = qisha_rule_input(build(p3))
ck("G3 正官藏干不在天干->UNSAT", c3['conditions']['杀混官'], 'UNSATISFIED')

# G4 state仍CANDIDATE
ck("G4 state仍CANDIDATE", c1['state'], 'CANDIDATE')
# G5 supported含杀混官
ck("G5 supported含杀混官", '杀混官' in c1['bucket']['supported'], True)
# G6 note注明逢财无制HOLD
ck("G6 note注明逢财无制HOLD", '无制HOLD' in c1['boundary_note'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
