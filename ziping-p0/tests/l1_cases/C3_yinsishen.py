# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目C3: 寅巳申三重关系
寅巳=刑+害, 巳申=合, 寅申=冲
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch, _is_chong

PASS = 0
FAIL = 0

print('=== C3 寅巳申三重关系 ===')
print()

# 验1: 巳申合
print('--- 巳申合 ---')
branches1 = ['巳', '申']
stems1 = ['壬']  # 水透干
he1 = _get_hehua_branch('巳', branches1, stems1)
print(f'  巳申合化水: {he1}')
if he1 == '水':
    PASS += 1
    print(f'  OK: 巳申合成立')
else:
    FAIL += 1
    print(f'  FAIL: 期望巳申合化水')

# 验2: 寅申冲
print()
print('--- 寅申冲 ---')
chong1 = _is_chong('寅', '申')
print(f'  寅申冲: {chong1}')
if chong1 == True:
    PASS += 1
    print(f'  OK: 寅申冲成立')
else:
    FAIL += 1
    print(f'  FAIL: 期望寅申冲')

# 验3: 寅巳(刑+害, 引擎暂无检测, 只验合不成立)
print()
print('--- 寅巳(刑+害, 暂无检测) ---')
branches3 = ['寅', '巳']
he3 = _get_hehua_branch('寅', branches3, ['甲'])
print(f'  寅巳合: {he3} (应为空)')
if he3 == '':
    PASS += 1
    print(f'  OK: 寅巳无合(刑害记录待实现)')
else:
    FAIL += 1
    print(f'  FAIL: 期望寅巳无合')

print()
print(f'C3结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 刑害检测待实现, 当前只验合冲')
print()
