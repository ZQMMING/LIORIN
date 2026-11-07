# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目C2: 合解刑黄金盘
裁决#027: 合可解刑
原文: 真诠"丙生子月,逢卯则刑,而或支中有戌,则与戌合而不刑"
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch, _is_chong

PASS = 0
FAIL = 0

print('=== C2 合解刑黄金盘 ===')
print()

# 原文盘: 丙生子月 + 卯 + 戌
# 子卯刑, 卯戌合 → 合解刑
branches = ['子', '卯', '戌']
stems = ['丙']

# 验1: 卯戌合成立
he_result = _get_hehua_branch('卯', branches, stems)
print(f'  卯戌合化火: {he_result}')
# 期望: 合化火(丙透干)
if he_result == '火':
    PASS += 1
    print(f'  OK: 卯戌合成立')
else:
    FAIL += 1
    print(f'  FAIL: 期望卯戌合化火')

# 验2: 子卯刑记录
# 引擎暂无刑检测函数, 只验合成立
print()
print(f'C2结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 刑检测函数待实现, 当前只验合成立')
print()
