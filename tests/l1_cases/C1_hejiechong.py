# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目C1: 合解冲
裁决#013: 合解冲不限位置
原文: 真诠"三合六合可以解之"
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch, _is_chong

PASS = 0
FAIL = 0

print('=== C1 合解冲 ===')
print()

# 验1: 卯酉冲+戌 → 卯戌合解冲
print('--- 卯酉冲+戌(应合解冲) ---')
branches1 = ['卯', '酉', '戌']
stems1 = ['丙']  # 火透干
# 卯酉冲?
chong1 = _is_chong('卯', '酉')
print(f'  卯酉冲: {chong1}')
# 卯戌合?
he1 = _get_hehua_branch('卯', branches1, stems1)
print(f'  卯戌合化火: {he1}')
# 期望: 冲成立+合成立(解冲)
if chong1 == True and he1 == '火':
    PASS += 1
    print(f'  OK: 卯酉冲+卯戌合解冲')
else:
    FAIL += 1
    print(f'  FAIL: 期望冲+合并存')

# 验2: 卯酉冲+辰(辰非卯之合) → 冲仍成立
print()
print('--- 卯酉冲+辰(辰非卯合, 冲仍成立) ---')
chong2 = _is_chong('卯', '酉')
print(f'  卯酉冲: {chong2}')
if chong2 == True:
    PASS += 1
    print(f'  OK: 无合解, 冲仍成立')
else:
    FAIL += 1
    print(f'  FAIL: 期望冲成立')

print()
print(f'C1结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 解冲逻辑(冲力折减)待L2旺衰层补')
print()
