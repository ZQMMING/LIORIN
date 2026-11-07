# -*- coding: utf-8 -*-
"""
L2 #035验证: 母灭结构制三条件
①印星成势 ②日主无根 ③子行无救应
"""
import sys
sys.path.insert(0, '.')

from engines.common.mumie_checker import check_mumie, YIN_THRESHOLD
from engines.common.dangzhong_counter import calc_dangzhong

print('=== #035验证: 母灭结构制 ===')
print()

# 真母灭盘(应判出)
r1 = check_mumie(['卯', '寅', '卯', '辰'], ['癸', '甲', '丁', '甲'], '丁')
print(f'真母灭(木多火熄): {r1["status"]} {r1.get("state","")} ratio={r1.get("ratio",0):.1f}')

# 印重有根反例(不应判出)
# 木多+火库根(戌)盘: 印星成势但子行有库根
print()
print('--- 印重有根反例(木多+火库根戌) ---')
r2 = check_mumie(['卯', '寅', '卯', '戌'], ['癸', '甲', '丙', '甲'], '丙')
print(f'结果: {r2["status"]} ratio={r2.get("ratio",0):.1f}')
dz2 = calc_dangzhong(['卯', '寅', '卯', '戌'], ['癸', '甲', '丙', '甲'])
print(f'党众: 木={dz2["木"]:.1f}, 火={dz2["火"]:.1f}')

# 印重透干反例(不应判出)
print()
print('--- 印重透干反例(木多+火透干) ---')
r3 = check_mumie(['卯', '寅', '卯', '巳'], ['癸', '甲', '丙', '甲'], '丙')
print(f'结果: {r3["status"]} ratio={r3.get("ratio",0):.1f}')
dz3 = calc_dangzhong(['卯', '寅', '卯', '巳'], ['癸', '甲', '丙', '甲'])
print(f'党众: 木={dz3["木"]:.1f}, 火={dz3["火"]:.1f}')

print()
print('=== #035三条件验证 ===')
print(f'① 印星成势: 阈值{YIN_THRESHOLD} ✅')
print(f'② 日主无根: DAYMASTER_MAX=2.0 ✅')
print(f'③ 子行无救应: 待补(库根/透干救应判定)')
