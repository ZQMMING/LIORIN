# -*- coding: utf-8 -*-
"""PATCH-216 自刑(YHZP-010-001) Golden: 辰午酉亥同支重复 -> SELF_PUNISHMENT 结构Fact.
仅结构存在, 不判吉凶/成立/强弱."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

fails = 0
def ck(n, ok):
    global fails
    fails += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}")

def branches(r):
    return [x['branch'] for x in r['combination_facts']['self_punishment']]

# G1-G4: 辰辰/午午/酉酉/亥亥
r1 = build({'year': ['甲','辰'], 'month': ['丙','寅'], 'day': ['甲','辰'], 'hour': ['丙','寅']})
ck('G1 辰辰命中自刑', '辰' in branches(r1))
r2 = build({'year': ['甲','午'], 'month': ['丙','寅'], 'day': ['甲','午'], 'hour': ['丙','寅']})
ck('G2 午午命中自刑', '午' in branches(r2))
r3 = build({'year': ['甲','酉'], 'month': ['丙','寅'], 'day': ['甲','酉'], 'hour': ['丙','寅']})
ck('G3 酉酉命中自刑', '酉' in branches(r3))
r4 = build({'year': ['甲','亥'], 'month': ['丙','寅'], 'day': ['甲','亥'], 'hour': ['丙','寅']})
ck('G4 亥亥命中自刑', '亥' in branches(r4))

# G5: 非自刑支重复(子子)不产生
r5 = build({'year': ['甲','子'], 'month': ['丙','寅'], 'day': ['甲','子'], 'hour': ['丙','寅']})
ck('G5 子子不产自刑', branches(r5) == [])

# G6: 单支不产
r6 = build({'year': ['甲','辰'], 'month': ['丙','寅'], 'day': ['甲','子'], 'hour': ['丙','寅']})
ck('G6 单辰不产自刑', branches(r6) == [])

# G7: 既有三刑不破坏
r7 = build({'year': ['甲','寅'], 'month': ['丙','巳'], 'day': ['甲','申'], 'hour': ['丙','寅']})
ck('G7 寅巳申三刑保留', '寅巳申三刑' in r7['combination_facts']['sanxing'])

# G8: 自刑输出本身无强弱二值(176 changsheng_direction的WEAK是已授权方向标签, 不在此检查)
ck('G8 自刑输出无STRONG/WEAK', 'STRONG' not in str(r1['combination_facts']['self_punishment']) and 'WEAK' not in str(r1['combination_facts']['self_punishment']))

if fails:
    sys.exit(1)
print('216 自刑 Golden: ALL PASS')
sys.exit(0)
