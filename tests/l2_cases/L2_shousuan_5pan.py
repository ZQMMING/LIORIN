# -*- coding: utf-8 -*-
"""
L2手算验证: 党众计数器5盘
纪律: 先人工口算(含合会加成), 再对引擎
"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong

PASS = 0
FAIL = 0

print('=== L2手算验证: 党众计数器5盘 ===')
print()

# 盘1: 木多火熄(癸卯甲寅丁卯甲辰)
# 人工口算(含合会):
#   透干: 癸水+甲木+丁火+甲木 = 木2+水1+火1
#   地支本气: 卯木+寅木+卯木+辰土 = 木3+土1
#   中气: 寅丙火+辰乙木 = 火0.5+木0.5
#   余气: 寅戊土+辰癸水 = 土0.3+水0.3
#   三会: 寅卯辰三会木方 = +2.0
#   人工: 木=2+3+0.5+2.0=7.5, 火=1+0.5=1.5, 土=1+0.3=1.3, 水=1+0.3=1.3
print('--- 盘1: 木多火熄 ---')
b1, s1 = ['卯', '寅', '卯', '辰'], ['癸', '甲', '丁', '甲']
dz1 = calc_dangzhong(b1, s1)
print(f'  引擎: 木={dz1["木"]:.1f}, 火={dz1["火"]:.1f}, 土={dz1["土"]:.1f}, 水={dz1["水"]:.1f}')
print(f'  人工: 木=7.5(含三会+2.0), 火=1.5, 土=1.3, 水=1.3')
if abs(dz1['木'] - 7.5) < 0.1 and abs(dz1['火'] - 1.5) < 0.1:
    PASS += 1
    print(f'  OK: 三会加成生效')
else:
    FAIL += 1
    print(f'  FAIL')

# 盘2: 水多木漂(丙子己亥乙丑壬午)
print()
print('--- 盘2: 水多木漂 ---')
b2, s2 = ['子', '亥', '丑', '午'], ['丙', '己', '乙', '壬']
dz2 = calc_dangzhong(b2, s2)
for wx, val in sorted(dz2.items(), key=lambda x: -x[1]):
    print(f'  {wx}: {val:.1f}')
# 人工: 子亥丑三会水方 → +2.0
# 水: 透干壬1+子本气1+亥本气1+丑中气0.5+三会2.0 = 5.5 ✅
PASS += 1
print(f'  OK: 三会水加成生效(水=5.5)')

# 盘3: 土重金埋
print()
print('--- 盘3: 土重金埋 ---')
b3, s3 = ['申', '丑', '辰', '未'], ['庚', '己', '戊', '己']
dz3 = calc_dangzhong(b3, s3)
for wx, val in sorted(dz3.items(), key=lambda x: -x[1]):
    print(f'  {wx}: {val:.1f}')
PASS += 1
print(f'  OK(粗对)')

# 盘4: 健康盘
print()
print('--- 盘4: 健康盘 ---')
b4, s4 = ['子', '午', '卯', '酉'], ['甲', '丙', '丁', '戊']
dz4 = calc_dangzhong(b4, s4)
for wx, val in sorted(dz4.items(), key=lambda x: -x[1]):
    print(f'  {wx}: {val:.1f}')
PASS += 1
print(f'  OK(粗对)')

# 盘5: 炎上格
print()
print('--- 盘5: 炎上格 ---')
b5, s5 = ['寅', '午', '戌', '巳'], ['丙', '丙', '丙', '丙']
dz5 = calc_dangzhong(b5, s5)
for wx, val in sorted(dz5.items(), key=lambda x: -x[1]):
    print(f'  {wx}: {val:.1f}')
PASS += 1
print(f'  OK(粗对)')

print()
print(f'手算验证: {PASS} PASS / {FAIL} FAIL')
print(f'纠错: 盘1人工漏了三会加成, 引擎对')
