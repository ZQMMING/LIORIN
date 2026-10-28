# -*- coding: utf-8 -*-
"""完整输出: 调候+用神"""
import sys
sys.path.insert(0, '.')

from engines.common.tiaohou_checker import check_tiaohou
from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.root_grade_boundary import to_root_grade

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
dm = '乙'

dz = calc_dangzhong(branches, stems)

print('='*50)
print('癸亥 壬戌 乙未 壬午 (男, 中山)')
print('='*50)
print()

print('【日主】')
print(f'  乙木: {dz["木"]:.1f} ({to_root_grade(dz["木"])})')
print()

print('【调候】')
status, gan_list = check_tiaohou('乙', '戌', stems)
print(f'  戌月乙木调候: {gan_list}')
print(f'  调候干有无: {status}')
print()

print('【用神(扶抑)】')
dm_val = dz['木']
if dm_val < 2.0:
    print('  身弱 → 用神: 水印(印星)')
    print('  喜神: 木(比劫)')
    print('  忌神: 土(财) 金(官杀) 火(食伤)')
print()

print('【用神(调候)】')
print(f'  戌月乙木: {gan_list}')
print(f'  调候干: {status}')
print()

print('【位阶裁决】')
print('  调候急切 > 扶抑')
print('  → 首用: 癸水(调候+扶抑双补)')
print('  → 次用: 丙火(调候暖局)')
