# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B3: 六合化神
裁决#001: 化神当令 或 化神透干(双条件)
引擎现状: 只验透干, 缺当令即化分支
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch, LIUHE_HUA

PASS = 0
FAIL = 0
SKIP = 0

print('=== B3 六合化神 ===')
print()

# 六合6组:
# 子丑合土 / 寅亥合木 / 卯戌合火 / 辰酉合金 / 巳申合水 / 午未合火
LIUHE_TESTS = [
    # (合支1, 合支2, 化神, 天干(验透干), 预期)
    ('子', '丑', '土', ['甲','己','丙','丁'], '土'),  # 己透干
    ('寅', '亥', '木', ['甲','丙','戊','丁'], '木'),  # 甲透干
    ('卯', '戌', '火', ['丙','丁','甲','戊'], '火'),  # 丙透干
    ('辰', '酉', '金', ['庚','辛','甲','丙'], '金'),  # 庚透干
    ('巳', '申', '水', ['壬','癸','甲','丙'], '水'),  # 壬透干
    ('午', '未', '火', ['丙','丁','甲','戊'], '火'),  # 丁透干
]

print('--- 化神透干档 ---')
for b1, b2, hua, stems, expected in LIUHE_TESTS:
    all_branches = [b1, b2]
    result = _get_hehua_branch(b1, all_branches, stems)
    ok = result == expected
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {b1}{b2}合{hua}: got={result} exp={expected}')
    print(f'  OK {b1}{b2}合{hua}: {result}')

print()
print('--- 化神不透干(应合而不化) ---')
for b1, b2, hua, stems, expected in LIUHE_TESTS:
    all_branches = [b1, b2]
    # 换天干: 不透化神
    non_hua_stems = ['甲' if hua != '木' else '丙', '乙' if hua != '木' else '丁']
    result = _get_hehua_branch(b1, all_branches, non_hua_stems)
    ok = result == ''
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {b1}{b2}不透{hua}: got={result} exp=""')
    print(f'  OK {b1}{b2}不透{hua}: {result}')

print()
print(f'B3结果: {PASS} PASS / {FAIL} FAIL / {SKIP} SKIP(当令档待补)')
print(f'备注: 当令即化分支待实现(裁决#001另一半)')
print()
