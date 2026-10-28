# -*- coding: utf-8 -*-
"""PATCH-190 刑合 Structural Entry golden (癸日+甲寅时+无申+天干无戊己)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

def entry(pillars):
    return build(pillars).get('xinghe_entry', {})

# G1 正例: 癸日+甲寅时+无申+天干无戊己
p1 = {'year': ['癸', '亥'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['甲', '寅']}
ck("G1 正例", entry(p1)['is_entry'], True)

# G2 非癸日(丁日)
p2 = {'year': ['丁', '亥'], 'month': ['乙', '卯'], 'day': ['丁', '卯'], 'hour': ['甲', '寅']}
ck("G2 非癸日", entry(p2)['is_entry'], False)

# G3 非甲寅时(乙卯时)
p3 = {'year': ['癸', '亥'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['乙', '卯']}
ck("G3 非甲寅时", entry(p3)['is_entry'], False)

# G4 命中地支申(申冲寅)
p4 = {'year': ['壬', '申'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['甲', '寅']}
ck("G4 地支见申", entry(p4)['is_entry'], False)

# G5 天干见戊(官)
p5 = {'year': ['戊', '子'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['甲', '寅']}
ck("G5 天干见戊", entry(p5)['is_entry'], False)

# G5b 天干见己(杀)
p5b = {'year': ['己', '丑'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['甲', '寅']}
ck("G5b 天干见己", entry(p5b)['is_entry'], False)

# G6 排除项与主体共存(有申+天干戊)
p6 = {'year': ['戊', '申'], 'month': ['乙', '卯'], 'day': ['癸', '卯'], 'hour': ['甲', '寅']}
ck("G6 排除项共存", entry(p6)['is_entry'], False)

# G7/G8 原则锁: 纯结构层无信息缺失, 排除项为确定Fact; note不压not_authorized
r7 = entry(p1)
ck("G7/G8 note明确排除为确定Fact", '确定Fact' in r7.get('note', ''), True)
ck("G8 未定格局无祸福", not any(w in str(r7) for w in ['成格', '吉凶', '喜忌']), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
