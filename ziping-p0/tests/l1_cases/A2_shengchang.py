# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目A2: 长生/禄/库穷举
引擎TONGGEN_TABLE只存这三项，不是完整十二宫
"""
import sys
sys.path.insert(0, '.')

from spec.yinyang_system import TONGGEN_TABLE, get_tonggen_strength

# 五行墓库（裁决#010: 墓库不分阴阳）
# 木墓未 / 火墓戌 / 土墓戌(戊)/丑(己) / 金墓丑 / 水墓辰
EXPECTED = {
    '甲': {'禄': '寅', '长生': '亥', '库': '未'},
    '乙': {'禄': '卯', '长生': '午', '库': '未'},
    '丙': {'禄': '巳', '长生': '寅', '库': '戌'},
    '丁': {'禄': '午', '长生': '酉', '库': '戌'},
    '戊': {'禄': '巳', '长生': '寅', '库': '戌'},  # 裁决#009
    '己': {'禄': '午', '长生': '酉', '库': '丑'},  # 裁决#009
    '庚': {'禄': '申', '长生': '巳', '库': '丑'},
    '辛': {'禄': '酉', '长生': '子', '库': '丑'},
    '壬': {'禄': '亥', '长生': '申', '库': '辰'},
    '癸': {'禄': '子', '长生': '卯', '库': '辰'},
}

PASS = 0
FAIL = 0

print('=== A2 长生/禄/库 30格穷举 ===')
for stem, exp in EXPECTED.items():
    # 验禄
    result = get_tonggen_strength(stem, exp['禄'])
    ok = result == '禄刃'
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {stem}禄: got={result} exp=禄刃')
    # 验长生
    result = get_tonggen_strength(stem, exp['长生'])
    ok = result == '长生'
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {stem}长生: got={result} exp=长生')
    # 验库
    result = get_tonggen_strength(stem, exp['库'])
    ok = result == '库'
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {stem}库: got={result} exp=库')

print(f'A2结果: {PASS} PASS / {FAIL} FAIL')
print()
