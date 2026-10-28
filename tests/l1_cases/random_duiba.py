# -*- coding: utf-8 -*-
"""
L1随机对拍脚本 - 10万四柱双实现独立对拍
实现A: 独立查表实现(硬编码表)
实现B: 引擎实现(import)
固定种子: 42
"""
import sys
sys.path.insert(0, '.')

import random
random.seed(42)

# ========== 实现A: 独立查表 ==========

# 藏干表(独立硬编码)
A_CANGGAN = {
    '子': ['癸', '', ''], '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'], '卯': ['乙', '', ''],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己', ''], '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'], '酉': ['辛', '', ''],
    '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲', ''],
}

# 长生/禄/库表(独立硬编码)
A_TONGGEN = {
    '甲': {'禄': '寅', '长生': '亥', '库': '未'},
    '乙': {'禄': '卯', '长生': '午', '库': '未'},
    '丙': {'禄': '巳', '长生': '寅', '库': '戌'},
    '丁': {'禄': '午', '长生': '酉', '库': '戌'},
    '戊': {'禄': '巳', '长生': '寅', '库': '戌'},
    '己': {'禄': '午', '长生': '酉', '库': '丑'},
    '庚': {'禄': '申', '长生': '巳', '库': '丑'},
    '辛': {'禄': '酉', '长生': '子', '库': '丑'},
    '壬': {'禄': '亥', '长生': '申', '库': '辰'},
    '癸': {'禄': '子', '长生': '卯', '库': '辰'},
}

# 六冲表(独立硬编码)
A_CHONG = {
    ('子', '午'), ('丑', '未'), ('寅', '申'),
    ('卯', '酉'), ('辰', '戌'), ('巳', '亥'),
}

# 天干五行
A_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

# ========== 实现B: 引擎 ==========

from spec.root_qi import BRANCH_CANGGAN, LIU_CHONG, _is_chong
from spec.yinyang_system import TONGGEN_TABLE, get_tonggen_strength

# ========== 对拍逻辑 ==========

BRANCHES = list('子丑寅卯辰巳午未申酉戌亥')
STEMS = list('甲乙丙丁戊己庚辛壬癸')

N = 100000
PASS = 0
FAIL = 0
fail_details = []

print(f'=== 10万随机对拍 (种子42, {N}四柱) ===')
print()

for i in range(N):
    # 随机生成四柱: 4个地支+4个天干
    branches = [random.choice(BRANCHES) for _ in range(4)]
    stems = [random.choice(STEMS) for _ in range(4)]

    # 验1: 藏干表
    for b in branches:
        a = tuple(A_CANGGAN[b])
        eng = BRANCH_CANGGAN[b]
        if a != eng:
            FAIL += 1
            fail_details.append(f'藏干{b}: A={a} B={eng}')

    # 验2: 长生/禄/库
    for s in stems:
        for check in ['禄', '长生', '库']:
            a_val = A_TONGGEN[s][check]
            b_val = TONGGEN_TABLE[s][check][0]
            if a_val != b_val:
                FAIL += 1
                fail_details.append(f'{s}{check}: A={a_val} B={b_val}')

    # 验3: 六冲识别
    for i1 in range(4):
        for i2 in range(i1+1, 4):
            b1, b2 = branches[i1], branches[i2]
            # 实现A: 查表
            a_chong = (b1, b2) in A_CHONG or (b2, b1) in A_CHONG
            # 实现B: 引擎函数
            b_chong = _is_chong(b1, b2)
            if a_chong != b_chong:
                FAIL += 1
                fail_details.append(f'冲{b1}{b2}: A={a_chong} B={b_chong}')

    if FAIL > 100:
        break  # 错100个就停, 防刷屏

    if (i+1) % 10000 == 0:
        print(f'  进度: {i+1}/{N}, 错={FAIL}')

print()
print(f'=== 对拍结果 ===')
print(f'总用例: {N}四柱')
print(f'PASS: {N*4 - FAIL} (约, 按四柱计)')
print(f'FAIL: {FAIL}')
if fail_details:
    print(f'前10错例:')
    for d in fail_details[:10]:
        print(f'  {d}')
else:
    print('全绿, 无差异')
print()
print(f'种子: 42')
print(f'结论: {"双实现一致 ✅" if FAIL == 0 else "有差异, 开单"}')
