# -*- coding: utf-8 -*-
"""完整八字引擎输出"""
import sys
sys.path.insert(0, '.')

from engines.common.l0_fact_builder import build as l0b
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.mumie_checker import check_mumie
from engines.common.root_grade_boundary import to_root_grade

pillars = {
    'year': ['癸', '亥'],
    'month': ['壬', '戌'],
    'day': ['乙', '未'],
    'hour': ['壬', '午'],
}

facts = l0b(pillars)
wp = build_wuxing_power(pillars, facts)
th = build_tian_he(pillars, facts)
sp = build_special_patterns(pillars, facts, wp, th)

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
dm = '乙'

dz = calc_dangzhong(branches, stems)
mumie = check_mumie(branches, stems, dm)

print('=' * 50)
print('八字: 癸亥 壬戌 乙未 壬午 (男, 中山)')
print('=' * 50)
print()

print('【一、党众】')
for wx, val in sorted(dz.items(), key=lambda x: -x[1]):
    grade = to_root_grade(val)
    print(f'  {wx}: {val:.1f} ({grade})')
print()

print('【二、旺衰】')
dm_val = dz['木']
print(f'  日主乙木: {dm_val:.1f} ({to_root_grade(dm_val)})')
print(f'  印星水: {dz["水"]:.1f} ({to_root_grade(dz["水"])})')
print(f'  官杀金: {dz["金"]:.1f} ({to_root_grade(dz["金"])})')
print(f'  财土: {dz["土"]:.1f} ({to_root_grade(dz["土"])})')
print(f'  食伤火: {dz["火"]:.1f} ({to_root_grade(dz["火"])})')
print()

print('【三、母灭】')
print(f'  status: {mumie["status"] or "无"}')
print(f'  taishi: {mumie.get("taishi", "无")}')
print(f'  ratio: {mumie.get("ratio", 0):.1f}')
print()

print('【四、特殊格局】')
print(f'  cong_type: {sp.get("cong_type") or "无"}')
print(f'  cong_state: {sp.get("cong_state") or "无"}')
print(f'  zhuanwang: {sp.get("zhuanwang") or "无"}')
print(f'  mu_mie: {sp.get("mu_mie") or "无"}')
print(f'  liangqi: {sp.get("liangqi") or "无"}')
print()

print('【五、patterns】')
if sp.get('patterns'):
    for p in sp['patterns']:
        print(f'  {p.get("name")} ({p.get("state")})')
else:
    print('  空')
print()

print('【六、判定状态】')
print(f'  judgment_status: {sp.get("judgment_status")}')
