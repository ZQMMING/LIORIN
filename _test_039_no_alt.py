# -*- coding: utf-8 -*-
"""
#039无替代药分支验证盘
冬金枯寒, 调候需丙, 丙藏巳被亥冲
"""
import sys
sys.path.insert(0, '.')

from engines.common.tiaohou_checker import check_tiaohou
from engines.common.dangzhong_counter import calc_dangzhong

# 造盘: 庚子 己丑 辛巳 壬辰
# 冬金(子月/丑月), 调候需丙
# 丙藏巳中, 但巳被亥冲?
# 地支: 子 丑 巳 辰 → 无亥
# 改: 庚子 丁亥 辛巳 壬辰
# 地支: 子 亥 巳 辰 → 巳亥冲
branches = ['子', '亥', '巳', '辰']
stems = ['庚', '丁', '辛', '壬']
dm = '辛'

dz = calc_dangzhong(branches, stems)

print('=== #039无替代药分支验证盘 ===')
print('庚子 丁亥 辛巳 壬辰')
print()
print('【党众】')
for wx, val in sorted(dz.items(), key=lambda x: -x[1]):
    print(f'  {wx}: {val:.1f}')
print()

print('【调候】')
status, gan_list = check_tiaohou('辛', '亥', stems)
print(f'  亥月辛金调候: {gan_list}')
print(f'  调候干有无: {status}')
print()

print('【#039分支】')
print('  调候需丙 → 丙藏巳中')
print('  巳亥冲 → 丙根被冲?')
print('  → 调候所需=丙, 丙根被冲')
print('  → 无替代药? → 踩#039无替代药分支')
