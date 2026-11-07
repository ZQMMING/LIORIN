# -*- coding: utf-8 -*-
"""PATCH-201 印格官印双全 supported结构 golden (正官非七杀)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.yinge_rule_contract import yinge_rule_input

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 乙日子月: 子本气癸=乙偏印. 乙日正官=庚, 七杀=辛
# G1 天干见庚(正官) -> 官印双全 SAT
p1 = {'year': ['庚', '午'], 'month': ['戊', '子'], 'day': ['乙', '酉'], 'hour': ['丁', '丑']}
c1 = yinge_rule_input(build(p1))
ck("G1 天干见正官庚->SAT", c1['conditions']['官印双全'], 'SATISFIED')

# G2 天干见辛(七杀) -> UNSAT (七杀非正官)
p2 = {'year': ['辛', '酉'], 'month': ['戊', '子'], 'day': ['乙', '酉'], 'hour': ['丁', '丑']}
c2 = yinge_rule_input(build(p2))
ck("G2 天干见七杀辛->UNSAT", c2['conditions']['官印双全'], 'UNSATISFIED')

# G3 正官藏干(巳藏庚)天干无庚 -> UNSAT (只查天干)
p3 = {'year': ['甲', '子'], 'month': ['戊', '子'], 'day': ['乙', '巳'], 'hour': ['丁', '丑']}
c3 = yinge_rule_input(build(p3))
ck("G3 正官藏干不在天干->UNSAT", c3['conditions']['官印双全'], 'UNSATISFIED')

# G4 state仍CANDIDATE非印格成
ck("G4 state仍CANDIDATE", c1['state'], 'CANDIDATE')

# G5 blocked仍空(不碰贪财破印)
ck("G5 blocked仍空", c1['bucket']['blocked'], [])

# G6 note明确正官非七杀
ck("G6 note明确正官非七杀", '正官非七杀' in c1['boundary_note'], True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
