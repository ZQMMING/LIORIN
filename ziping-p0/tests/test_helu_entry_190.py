# -*- coding: utf-8 -*-
"""PATCH-190 合禄 Structural Entry golden (戊/癸日+庚申时+天干不透官)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

def entry(pillars):
    return build(pillars).get('helu_entry', {})

# G1 戊日庚申时+天干无甲乙(官杀)
p1 = {'year': ['戊', '戌'], 'month': ['戊', '午'], 'day': ['戊', '申'], 'hour': ['庚', '申']}
ck("G1 戊日庚申", entry(p1)['is_entry'], True)

# G2 癸日庚申时+天干无戊己
p2 = {'year': ['癸', '卯'], 'month': ['癸', '亥'], 'day': ['癸', '亥'], 'hour': ['庚', '申']}
ck("G2 癸日庚申", entry(p2)['is_entry'], True)

# G3 非戊癸日(辛日)
p3 = {'year': ['辛', '卯'], 'month': ['癸', '亥'], 'day': ['辛', '亥'], 'hour': ['庚', '申']}
ck("G3 非戊癸日", entry(p3)['is_entry'], False)

# G4 非庚申时(辛酉)
p4 = {'year': ['戊', '戌'], 'month': ['戊', '午'], 'day': ['戊', '申'], 'hour': ['辛', '酉']}
ck("G4 非庚申时", entry(p4)['is_entry'], False)

# G5 天干透官(戊日见甲=七杀)
p5 = {'year': ['甲', '戌'], 'month': ['戊', '午'], 'day': ['戊', '申'], 'hour': ['庚', '申']}
ck("G5 天干透七杀甲", entry(p5)['is_entry'], False)

# G6 不推格成/贵贱
r6 = entry(p1)
ck("G6 未定格局", '未定格局' in r6.get('note', ''), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
