# -*- coding: utf-8 -*-
"""用神层初判(扶抑法)"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.root_grade_boundary import to_root_grade

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
dm = '乙'

dz = calc_dangzhong(branches, stems)
dm_val = dz['木']

print('=== 用神层初判(扶抑法) ===')
print()

# 日主强弱
print(f'日主乙木: {dm_val:.1f} ({to_root_grade(dm_val)})')
print()

# 扶抑: 身弱用印比
if dm_val < 2.0:
    print('【扶抑法】身弱')
    print(f'  用神: 水印(印星) 木(比劫)')
    print(f'  忌神: 土(财) 金(官杀) 火(食伤)')
else:
    print('【扶抑法】身强')
    print(f'  用神: 土(财) 金(官杀) 火(食伤)')
    print(f'  忌神: 水(印星) 木(比劫)')
print()

# 调候(穷通)
print('【调候法】未月乙木')
print('  未月土旺, 木枯, 先用癸水润')
print('  次用丙火暖局')
print('  → 调候: 癸水+丙火')
print()

# 病药(神峰)
print('【病药法】')
print('  病: 水多土荡(戌未土被水浸)')
print('  药: 木克土? 不对——药是去病之物')
print('  → 待定')
print()

print('【综合】扶抑+调候')
print('  用神: 水印(扶身+调候双补)')
print('  喜神: 木(比劫帮身)')
print('  忌神: 土(财多身弱) 金(官杀克身)')
