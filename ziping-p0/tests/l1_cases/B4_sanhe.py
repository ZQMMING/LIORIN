# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B4: 三合局
裁决#015: 半局不分级(生旺=旺墓同效)
裁决#016: 拱局三档
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch, SANHE

PASS = 0
FAIL = 0

print('=== B4 三合局 ===')
print()

# 全局4局
SANHE_FULL = [
    (('申','子','辰'), '水'),
    (('亥','卯','未'), '木'),
    (('寅','午','戌'), '火'),
    (('巳','酉','丑'), '金'),
]

print('--- 全局(三支全) ---')
for members, hua in SANHE_FULL:
    all_branches = list(members)
    stems = ['甲', hua[0]] if hua == '木' else ['壬', hua[0]] if hua == '水' else ['丙', hua[0]] if hua == '火' else ['庚', hua[0]]
    result = _get_hehua_branch(members[0], all_branches, stems)
    ok = result == hua
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(members)}合{hua}: got={result} exp={hua}')
    print(f'  OK {"".join(members)}合{hua}: {result}')

print()
print('--- 半局(生旺半局) ---')
# 生旺半局: 申子(水)/亥卯(木)/寅午(火)/巳酉(金)
BANHE_SHENGWANG = [
    (('申','子'), '水'),
    (('亥','卯'), '木'),
    (('寅','午'), '火'),
    (('巳','酉'), '金'),
]
for members, hua in BANHE_SHENGWANG:
    all_branches = list(members)
    stems = ['壬' if hua == '水' else '甲' if hua == '木' else '丙' if hua == '火' else '庚']
    result = _get_hehua_branch(members[0], all_branches, stems)
    ok = result == hua
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(members)}半合{hua}: got={result} exp={hua}')
    print(f'  OK {"".join(members)}半合{hua}: {result}')

print()
print('--- 旺墓半局 ---')
# 旺墓半局: 子辰(水)/卯未(木)/午戌(火)/酉丑(金)
BANHE_WANGMU = [
    (('子','辰'), '水'),
    (('卯','未'), '木'),
    (('午','戌'), '火'),
    (('酉','丑'), '金'),
]
for members, hua in BANHE_WANGMU:
    all_branches = list(members)
    stems = ['壬' if hua == '水' else '甲' if hua == '木' else '丙' if hua == '火' else '庚']
    result = _get_hehua_branch(members[0], all_branches, stems)
    ok = result == hua
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(members)}半合{hua}: got={result} exp={hua}')
    print(f'  OK {"".join(members)}半合{hua}: {result}')

print()
print('--- 纯拱(生墓两支, 不成局) ---')
# 生墓两支: 申辰(水)/亥未(木)/寅戌(火)/巳丑(金)
GONG_PURE = [
    (('申','辰'), '水'),
    (('亥','未'), '木'),
    (('寅','戌'), '火'),
    (('巳','丑'), '金'),
]
for members, hua in GONG_PURE:
    all_branches = list(members)
    # 不透化神: 应不成局
    stems = ['甲' if hua != '木' else '丙']
    result = _get_hehua_branch(members[0], all_branches, stems)
    ok = result == ''
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(members)}拱{hua}: got={result} exp=""')
    print(f'  OK {"".join(members)}拱{hua}: {result}')

print()
print(f'B4结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 透干补中神档(B5)下一轮验')
print()
