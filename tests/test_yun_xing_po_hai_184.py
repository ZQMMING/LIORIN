# -*- coding: utf-8 -*-
"""PATCH-184 运支参与命局三刑/六害/六破 golden (仅结构, 非作用非吉凶)"""
import sys; sys.path.insert(0, '.')
from engines.common.relation_178 import yun_natal_relations

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 命局: 年寅 月巳 日子 时戌
pillars = {'year': ['甲', '寅'], 'month': ['丙', '巳'], 'day': ['甲', '子'], 'hour': ['戊', '戌']}

# G1 命局有子, 运卯 -> 子卯相刑
r1 = yun_natal_relations({'year': ['丁', '卯']}, pillars)
ck("G1 运卯+命子 -> 子卯相刑",
   any(x['relation'] == '三刑' and x['branches'] == ['子', '卯'] for x in r1), True)

# G2 命局有未? 命局有子, 运未 -> 子未相害 (子在命局)
pillars2 = {'year': ['甲', '寅'], 'month': ['丙', '巳'], 'day': ['甲', '子'], 'hour': ['戊', '戌']}
r2 = yun_natal_relations({'year': ['己', '未']}, pillars2)
ck("G2 运未+命子 -> 子未相害",
   any(x['relation'] == '六害' and set(x['branches']) == {'子', '未'} for x in r2), True)

# G3 命局有巳申? 命局有巳, 运申 -> 巳申相破
r3 = yun_natal_relations({'year': ['庚', '申']}, pillars)
ck("G3 运申+命巳 -> 巳申相破",
   any(x['relation'] == '六破' and set(x['branches']) == {'巳', '申'} for x in r3), True)

# G4 命局有巳申, 运寅 -> 寅巳申三刑齐
pillars4 = {'year': ['甲', '寅'], 'month': ['丙', '巳'], 'day': ['壬', '申'], 'hour': ['戊', '戌']}
r4 = yun_natal_relations({'year': ['甲', '寅']}, pillars4)
ck("G4 运寅+命巳申 -> 寅巳申三刑",
   any(x['relation'] == '三刑' and set(x['branches']) == {'寅', '巳', '申'} for x in r4), True)

# G5 命局无对应支, 运卯只碰到命寅 -> 不构成子卯刑
pillars5 = {'year': ['甲', '寅'], 'month': ['丙', '巳'], 'day': ['甲', '午'], 'hour': ['戊', '戌']}
r5 = yun_natal_relations({'year': ['丁', '卯']}, pillars5)
ck("G5 命无子, 运卯不构子卯刑",
   not any(x['relation'] == '三刑' for x in r5), True)

# 锁死: 结构note含"非吉凶"但relation/semantic层无吉凶
ck("锁死 relation层无吉凶词",
   not any(('吉' in x['relation'] or '凶' in x['relation']) for x in r1 + r4), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
