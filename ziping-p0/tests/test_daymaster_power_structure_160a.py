# -*- coding: utf-8 -*-
"""PATCH-160-A Golden: Daymaster Power Structure Generator
只验结构 Fact, judgment_status 恒 NOT_AUTHORIZED。不判身强/身弱。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from engines.common.daymaster_power_structure import build_power_structure

fails = []

# G1: 甲日寅月 -> 月令本气甲木==日主木 -> in_season=True
p1 = {'year': ['甲', '子'], 'month': ['丙', '寅'], 'day': ['甲', '辰'], 'hour': ['丙', '寅']}
r1 = build_power_structure(p1)
if not r1['seasonal_axis']['in_season']:
    fails.append('G1 in_season 应为True(甲日寅月同五行)')

# G2: 官杀边方向 = GUANSHA->DAYMASTER, 不是反向
guansha_edge = [e for e in r1['active_edges'] if e['relation'] == '官杀克身']
# p1 辰中藏戊乙癸, 寅藏甲丙戊, 无金->无官杀; 应不在active
if any(e['source'] == 'DAYMASTER' and e['target'] == 'GUANSHA' for e in r1['active_edges']):
    fails.append('G2 官杀边方向错(应为GUANSHA->DAYMASTER)')

# G3: judgment 恒 NOT_AUTHORIZED
if r1['judgment_status'] != 'NOT_AUTHORIZED':
    fails.append('G3 judgment_status 必须 NOT_AUTHORIZED')

# G4: 失时例子 壬日午月, 午本气火, 壬水-> in_season=False
p4 = {'year': ['壬', '子'], 'month': ['丙', '午'], 'day': ['壬', '午'], 'hour': ['甲', '辰']}
r4 = build_power_structure(p4)
if r4['seasonal_axis']['in_season']:
    fails.append('G4 壬日午月 in_season 应为False')

# G5: 比劫存在 — 甲日, 天干见甲(比肩)
p5 = {'year': ['甲', '子'], 'month': ['甲', '寅'], 'day': ['甲', '子'], 'hour': ['甲', '子']}
r5 = build_power_structure(p5)
if not r5['support_group']['BIJIE']['stem_present']:
    fails.append('G5 多甲天干应 stem_present=True')

# G6: 官杀存在且方向正确 — 甲日见庚(七杀)
p6 = {'year': ['甲', '子'], 'month': ['甲', '寅'], 'day': ['甲', '子'], 'hour': ['庚', '午']}
r6 = build_power_structure(p6)
gs_edge = [e for e in r6['active_edges'] if e['relation'] == '官杀克身']
if not gs_edge:
    fails.append('G6 见庚(七杀)应激活官杀克身边')
elif gs_edge[0]['source'] != 'GUANSHA' or gs_edge[0]['target'] != 'DAYMASTER':
    fails.append('G6 官杀边方向应为 GUANSHA->DAYMASTER')

# G7: 传递链边恒 UNAUTHORIZED, 不进 active_edges
if not all(e['authorization'] == 'C' for e in r1['unauthorized_edges']):
    fails.append('G7 传递链边应 authorization=C')
if any(e['relation'] in ('食伤生财', '财生官杀', '官杀生印') for e in r1['active_edges']):
    fails.append('G7 传递链边不应进 active_edges')

# G8: root_weight_class 不直出强弱
if 'STRONG' in str(r1) or 'WEAK' in str(r1):
    fails.append('G8 结构输出不应含 STRONG/WEAK 二值')

if fails:
    for f in fails:
        print('FAIL:', f)
    sys.exit(1)
print('160-A Golden: ALL PASS')
sys.exit(0)
