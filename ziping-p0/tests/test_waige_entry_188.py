# -*- coding: utf-8 -*-
"""PATCH-188 外格A类Structural Entry golden (仅结构存在, 非成格非贵贱)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

def entries(pillars):
    return [x['entry'] for x in build(pillars).get('waige_structural_entries', [])]

# G1 甲日 寅卯辰全 -> 曲直仁寿
p1 = {'year': ['甲', '寅'], 'month': ['甲', '卯'], 'day': ['甲', '辰'], 'hour': ['甲', '子']}
ck("G1 甲日寅卯辰全 -> 曲直仁寿", entries(p1), ['曲直仁寿'])

# G2 丙日 寅午戌全 -> 炎上
p2 = {'year': ['丙', '寅'], 'month': ['甲', '午'], 'day': ['丙', '戌'], 'hour': ['甲', '子']}
ck("G2 丙日寅午戌全 -> 炎上", entries(p2), ['炎上'])

# G3 戊日 辰戌丑未全 -> 稼穑
p3 = {'year': ['戊', '辰'], 'month': ['甲', '戌'], 'day': ['戊', '丑'], 'hour': ['甲', '未']}
ck("G3 戊日辰戌丑未全 -> 稼穑", entries(p3), ['稼穑'])

# G4 庚日 巳酉丑全 -> 从革
p4 = {'year': ['庚', '巳'], 'month': ['甲', '酉'], 'day': ['庚', '丑'], 'hour': ['甲', '子']}
ck("G4 庚日巳酉丑全 -> 从革", entries(p4), ['从革'])

# G5 壬日 申子辰全 -> 润下
p5 = {'year': ['壬', '申'], 'month': ['甲', '子'], 'day': ['壬', '辰'], 'hour': ['甲', '寅']}
ck("G5 壬日申子辰全 -> 润下", entries(p5), ['润下'])

# G6 井栏叉: 庚日庚子+申子辰全
p6 = {'year': ['庚', '申'], 'month': ['甲', '子'], 'day': ['庚', '子'], 'hour': ['甲', '辰']}
e6 = entries(p6)
ck("G6 庚子日申子辰全 -> 井栏叉", '井栏叉' in e6, True)

# G7 反例: 甲日但地支不全(缺辰) -> 无曲直
p7 = {'year': ['甲', '寅'], 'month': ['甲', '卯'], 'day': ['甲', '午'], 'hour': ['甲', '子']}
ck("G7 甲日缺辰 -> 无曲直", entries(p7), [])

# G8 反例: 丙日但缺戌 -> 无炎上
p8 = {'year': ['丙', '寅'], 'month': ['甲', '午'], 'day': ['丙', '子'], 'hour': ['甲', '子']}
ck("G8 丙日缺戌 -> 无炎上", entries(p8), [])

# G9 反例: 庚日申子辰全但日柱不是庚子/庚申/庚辰 -> 无井栏叉(但有从革? 申子辰是水局非金局, 从革要巳酉丑, 所以空)
p9 = {'year': ['庚', '申'], 'month': ['甲', '子'], 'day': ['庚', '寅'], 'hour': ['甲', '辰']}
ck("G9 日柱庚寅不立井栏叉", '井栏叉' not in entries(p9), True)

# 锁死: note不写成格/贵贱
note = build(p1).get('waige_structural_note', '')
ck("锁死 note明确非成格", '非成格' in note and '不证' in note, True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
