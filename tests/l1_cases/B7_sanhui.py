# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B7: 三会方
裁决#020: 三支全即成方, 不需透干
裁决#025: 方局三支须相邻(挂待验SKIP)
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_sanhui

PASS = 0
FAIL = 0
SKIP = 0

print('=== B7 三会方 ===')
print()

# 正例4: 四方连排成方
print('--- 正例: 四方成方 ---')
SI_FANG = [
    (['寅','卯','辰'], '木'),
    (['巳','午','未'], '火'),
    (['申','酉','戌'], '金'),
    (['亥','子','丑'], '水'),
]
for branches, hua in SI_FANG:
    result = _is_sanhui(branches[0], branches)
    ok = result == hua
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(branches)}方{hua}: got={result} exp={hua}')
    print(f'  OK {"".join(branches)}方{hua}: {result}')

print()
print('--- 边界: 两支不成方 ---')
TWO_ZHI = [
    (['寅','卯'], '木'),
    (['巳','午'], '火'),
    (['申','酉'], '金'),
    (['亥','子'], '水'),
]
for branches, hua in TWO_ZHI:
    result = _is_sanhui(branches[0], branches)
    ok = result == ''
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(branches)}方{hua}: got={result} exp=""')
    print(f'  OK {"".join(branches)}不成方: {result}')

print()
print('--- 反例: 半局不是方 ---')
BANHE_NOT_FANG = [
    (['巳','酉'], '金'),  # 巳酉半合金, 不是金方
    (['亥','卯'], '木'),  # 亥卯半合木, 不是木方
]
for branches, hua in BANHE_NOT_FANG:
    result = _is_sanhui(branches[0], branches)
    ok = result == ''
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(branches)}半合非方{hua}: got={result} exp=""')
    print(f'  OK {"".join(branches)}半合非方: {result}')

print()
print('--- SKIP: 隔位盘(裁决#025待验) ---')
GEWEI = [
    (['寅','子','卯','戌'], '木'),  # 寅卯隔子
]
for branches, hua in GEWEI:
    SKIP += 1
    print(f'  SKIP {"".join(branches)}隔位方{hua}: 待#025验')

print()
print(f'B7结果: {PASS} PASS / {FAIL} FAIL / {SKIP} SKIP')
print(f'备注: 相邻判定(#025)挂待验, 当前只判三支全')
print()
