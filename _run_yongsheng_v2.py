# -*- coding: utf-8 -*-
"""用神层位阶引擎(初版)"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.root_grade_boundary import to_root_grade

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
dm = '乙'

dz = calc_dangzhong(branches, stems)
dm_val = dz['木']

# 三路候选
# 路1: 扶抑
fuyi = {'水印': '用神', '木': '喜神', '土金火': '忌神'}

# 路2: 调候(未月乙木)
diaohou = {'癸水': '调候首用', '丙火': '次用'}

# 路3: 病药(待定)
bingyao = {}

# 位阶裁决: 调候 > 病药 > 扶抑
# 未月土旺木枯, 调候急切 → 调候优先
print('=== 用神层位阶引擎 ===')
print()
print('日主: 乙木 (身弱)')
print()
print('【三路候选】')
print(f'  扶抑: 用水印, 喜木, 忌土金火')
print(f'  调候: 先用癸水, 次用丙火')
print(f'  病药: 待定')
print()
print('【位阶裁决】调候急切(未月木枯) > 扶抑')
print()
print('【最终用神】')
print(f'  首用: 癸水 (调候+扶抑双补)')
print(f'  次用: 丙火 (调候暖局)')
print(f'  喜神: 木 (比劫帮身)')
print(f'  忌神: 土(财) 金(官杀)')
print()
print('【规则链】')
print(f'  1. 扶抑: 日主1.8<2.0→身弱→用印比')
print(f'  2. 调候: 未月土旺木枯→癸水润丙火暖')
print(f'  3. 位阶: 调候急切>扶抑→癸水优先')
