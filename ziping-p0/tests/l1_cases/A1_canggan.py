# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目A: 数据表穷举
A1 藏干: 12支×3位 = 36用例
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import BRANCH_CANGGAN

# 渊海·地支藏遁歌原文钉死表
EXPECTED_CANGGAN = {
    '子': ('癸', '', ''),
    '丑': ('己', '癸', '辛'),
    '寅': ('甲', '丙', '戊'),
    '卯': ('乙', '', ''),
    '辰': ('戊', '乙', '癸'),
    '巳': ('丙', '庚', '戊'),  # 裁决#006
    '午': ('丁', '己', ''),
    '未': ('己', '丁', '乙'),
    '申': ('庚', '壬', '戊'),
    '酉': ('辛', '', ''),
    '戌': ('戊', '辛', '丁'),
    '亥': ('壬', '甲', ''),
}

PASS = 0
FAIL = 0

print('=== A1 藏干表 36格穷举 ===')
for branch, expected in EXPECTED_CANGGAN.items():
    got = BRANCH_CANGGAN[branch]
    for i, role in enumerate(['本', '中', '余']):
        exp_val = expected[i]
        got_val = got[i]
        if exp_val == '':
            ok = (got_val == '')
        else:
            ok = (got_val == exp_val)
        if ok:
            PASS += 1
        else:
            FAIL += 1
            print(f'  FAIL {branch}{role}: got={got_val} exp={exp_val}')

print(f'A1结果: {PASS} PASS / {FAIL} FAIL')
print()
