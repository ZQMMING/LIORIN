# -*- coding: utf-8 -*-
"""PATCH-199 财格财逢七杀 blocked结构 golden (非直接FAILED)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.caige_rule_contract import caige_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 乙日辰月: 辰本气戊=乙正财. 乙日七杀=辛
# G1 天干无辛 -> 财逢七杀 UNSAT
p1 = {'year': ['癸', '亥'], 'month': ['甲', '辰'], 'day': ['乙', '酉'], 'hour': ['戊', '子']}
c1 = caige_rule_input(build(p1))
ck("G1 天干无七杀->UNSAT", c1['conditions']['财逢七杀'], 'UNSATISFIED')

# G2 天干见辛(七杀) -> SAT
p2 = {'year': ['辛', '酉'], 'month': ['甲', '辰'], 'day': ['乙', '酉'], 'hour': ['戊', '子']}
c2 = caige_rule_input(build(p2))
ck("G2 天干见七杀辛->SAT", c2['conditions']['财逢七杀'], 'SATISFIED')

# G3 七杀在藏干(日支酉藏辛)不在天干 -> UNSAT (只查天干)
p3 = {'year': ['癸', '亥'], 'month': ['甲', '辰'], 'day': ['乙', '酉'], 'hour': ['戊', '子']}
c3 = caige_rule_input(build(p3))
ck("G3 七杀藏干不在天干->UNSAT", c3['conditions']['财逢七杀'], 'UNSATISFIED')

# G4 不直接FAILED, state仍CANDIDATE
ck("G4 state仍CANDIDATE", c2['state'], 'CANDIDATE')

# G5 blocked bucket含财逢七杀
ck("G5 blocked含财逢七杀", '财逢七杀' in c2['bucket']['blocked'], True)

# G6 note注明救应后续
ck("G6 note注明救应后续", '救应后续' in c2['boundary_note'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
