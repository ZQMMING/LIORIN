# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B2: 四库冲开库
裁决#012: 四库冲开库(冲则库启, 无条件)
原文: 真诠"冲则库启，如甲用戊财而辰戌冲"
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_chong

PASS = 0
FAIL = 0

print('=== B2 四库冲开库 ===')
print()

# 四库冲2组: 辰戌、丑未
print('--- 四库冲识别 ---')
KU_CHONG = [('辰','戌'), ('丑','未')]
for c1, c2 in KU_CHONG:
    result = _is_chong(c1, c2)
    ok = result == True
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {c1}-{c2}: got={result} exp=True')
    print(f'  OK {c1}-{c2}冲: {result}')

print()
print('--- 非四库冲(四正冲) ---')
SI_ZHENG_CHONG = [('子','午'), ('卯','酉')]
for c1, c2 in SI_ZHENG_CHONG:
    result = _is_chong(c1, c2)
    ok = result == True
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {c1}-{c2}: got={result} exp=True')
    print(f'  OK {c1}-{c2}冲: {result}')

print()
print(f'B2结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 开库逻辑(库中气可用)待L2旺衰层补实现')
print(f'当前只验六冲识别, 开库判定是L2的活')
print()
