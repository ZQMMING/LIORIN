# -*- coding: utf-8 -*-
"""跑八字: 癸亥壬戌乙未壬午"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.mumie_checker import check_mumie
from engines.common.root_grade_boundary import to_root_grade

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
day_master = '乙'

print('=== 八字: 癸亥 壬戌 乙未 壬午 (男, 中山) ===')
print()

dz = calc_dangzhong(branches, stems)
print('党众:')
for wx, val in sorted(dz.items(), key=lambda x: -x[1]):
    grade = to_root_grade(val)
    print(f'  {wx}: {val:.1f} ({grade})')
print()

mumie = check_mumie(branches, stems, day_master)
print(f'母灭: {mumie["status"]} {mumie.get("taishi","")}')
print()

dm_val = dz['木']
dm_grade = to_root_grade(dm_val)
print(f'日主乙木: {dm_val:.1f} ({dm_grade})')
print(f'印星水: {dz["水"]:.1f} ({to_root_grade(dz["水"])})')
