# -*- coding: utf-8 -*-
"""PATCH-198 官格伤官克官 blocked结构 golden (非直接FAILED)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.guange_rule_contract import guange_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 乙日申月: 申本气庚=乙正官
# G1 天干无伤官 -> 伤官克官 UNSAT
p1 = {'year': ['癸', '亥'], 'month': ['甲', '申'], 'day': ['乙', '酉'], 'hour': ['戊', '子']}
c1 = guange_rule_input(build(p1))
ck("G1 天干无伤官->UNSAT", c1['conditions']['伤官克官'], 'UNSATISFIED')

# G2 天干见丙(伤官) -> 伤官克官 SATISFIED
p2 = {'year': ['丙', '寅'], 'month': ['甲', '申'], 'day': ['乙', '酉'], 'hour': ['戊', '子']}
c2 = guange_rule_input(build(p2))
ck("G2 天干见伤官丙->SAT", c2['conditions']['伤官克官'], 'SATISFIED')

# G3 伤官在藏干(日支寅藏丙)不在天干 -> UNSAT (只查天干)
p3 = {'year': ['癸', '亥'], 'month': ['甲', '申'], 'day': ['乙', '寅'], 'hour': ['戊', '子']}
c3 = guange_rule_input(build(p3))
ck("G3 伤官藏干不在天干->UNSAT", c3['conditions']['伤官克官'], 'UNSATISFIED')

# G4 关键: 不直接OFFICER_FAILED, 只是blocked结构SATISFIED
ck("G4 state仍CANDIDATE非FAILED", c2['state'], 'CANDIDATE')

# G5 blocked bucket含伤官克官
ck("G5 blocked含伤官克官", '伤官克官' in c2['bucket']['blocked'], True)

# G6 note明确财印救应后续
ck("G6 note注明救应后续", '救应后续' in c2['boundary_note'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
