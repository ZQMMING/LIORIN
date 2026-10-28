# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目A4: 交叉互证
四阳干长生位藏干含该干
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import BRANCH_CANGGAN
from spec.yinyang_system import TONGGEN_TABLE

PASS = 0
FAIL = 0

print('=== A4 交叉互证: 长生位藏干含该干 ===')
for stem in ['甲', '丙', '戊', '庚', '壬']:
    changsheng_branch = TONGGEN_TABLE[stem]['长生'][0]
    canggan = BRANCH_CANGGAN[changsheng_branch]
    contains = stem in canggan
    if contains:
        PASS += 1
        print(f'  OK {stem}长生{changsheng_branch}藏干{canggan}含{stem}')
    else:
        FAIL += 1
        print(f'  FAIL {stem}长生{changsheng_branch}藏干{canggan}不含{stem}')

print(f'A4结果: {PASS} PASS / {FAIL} FAIL')
print()
