# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B1: 六冲6组×2(直接对冲+隔位)
裁决#032: 六冲无位置限定(真诠"本宫之对"无位置字样)
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_chong, LIU_CHONG

PASS = 0
FAIL = 0

print('=== B1 六冲12盘 ===')
print()

# 直接对冲6盘
print('--- 直接对冲 ---')
for c1, c2 in LIU_CHONG:
    result = _is_chong(c1, c2)
    ok = result == True
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {c1}-{c2}: got={result} exp=True')
    print(f'  OK {c1}-{c2}: {result}')

print()
print('--- 隔位对冲(仍应True, 无位置限定) ---')
# 隔一支: 子_午(隔丑)、丑_未(隔寅)、寅_申(隔卯)、卯_酉(隔辰)、辰_戌(隔巳)、巳_亥(隔午)
# 注意: 隔位只是说明, _is_chong只判断两支本身, 隔不隔位不影响
# 这里验: 六冲组内任意两支都应识别
for c1, c2 in LIU_CHONG:
    # 反向也验
    result = _is_chong(c2, c1)
    ok = result == True
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {c2}-{c1}: got={result} exp=True')
    print(f'  OK {c2}-{c1}: {result}')

print()
print('--- 非冲组(应False) ---')
NON_CHONG = [('子','丑'), ('寅','卯'), ('辰','巳'), ('午','未'), ('申','酉'), ('戌','亥')]
for b1, b2 in NON_CHONG:
    result = _is_chong(b1, b2)
    ok = result == False
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {b1}-{b2}: got={result} exp=False')
    print(f'  OK {b1}-{b2}: {result}')

print()
print(f'B1结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 隔位不影响_is_chong判定(只看两支组合, 不看位置)')
print()
