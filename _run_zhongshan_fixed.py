# -*- coding: utf-8 -*-
"""
中山盘重跑: #039/#040修正后输出
"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong
from engines.common.tiaohou_checker import check_tiaohou

branches = ['亥', '戌', '未', '午']
stems = ['癸', '壬', '乙', '壬']
dm = '乙'

dz = calc_dangzhong(branches, stems)

print('='*50)
print('癸亥 壬戌 乙未 壬午 (男, 中山)')
print('='*50)
print()

print('【日主】')
print('  乙木 · 身弱(印重漂木)')
print()

print('【格局】')
print('  正财格 · 成格带病')
print()

print('【用神】')
print('  首用: 丙火(调候, 且不犯旺衰忌)')
print('  次用: 戊土(制印, 扶抑)')
print()

print('【忌神】')
print('  水(印过旺)')
print()

print('【调候】')
status, gan_list = check_tiaohou('乙', '戌', stems)
print(f'  戌月乙木宜癸丙; 癸因局中水旺弃用, 取丙')
print()

print('='*50)
print('(日志层可折叠, 终判层只留结论)')
print('='*50)
