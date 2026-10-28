# -*- coding: utf-8 -*-
"""找母灭阈值的健康盘上限"""
import sys
sys.path.insert(0, '.')

from engines.common.dangzhong_counter import calc_dangzhong

# 误判盘(期望母灭=False/None, 实际判出母灭)
wrong = [
    (['戌', '子', '子', '辰'], ['壬', '壬', '甲', '戊'], '甲', '健康盘1'),
    (['亥', '亥', '卯', '卯'], ['癸', '癸', '丁', '癸'], '丁', '健康盘2'),
    (['辰', '申', '子', '子'], ['戊', '庚', '甲', '甲'], '甲', '健康盘3'),
    (['未', '子', '辰', '丑'], ['乙', '戊', '庚', '丁'], '庚', '健康盘4'),
    (['子', '亥', '亥', '子'], ['壬', '辛', '乙', '丙'], '乙', '健康盘5'),
    (['子', '亥', '亥', '子'], ['丙', '己', '乙', '丙'], '乙', '健康盘6'),
    (['辰', '酉', '申', '子'], ['壬', '己', '甲', '甲'], '甲', '健康盘7'),
]

# 真母灭盘(期望母灭=True)
right = [
    (['卯', '寅', '卯', '辰'], ['癸', '甲', '丁', '甲'], '丁', '木多火熄'),
    (['子', '亥', '丑', '午'], ['丙', '己', '乙', '壬'], '乙', '水多木漂'),
]

print('=== 误判盘党众比(健康盘) ===')
for b, s, dm, name in wrong:
    dz = calc_dangzhong(b, s)
    # 找母行/子行比
    from engines.common.mumie_checker import MUMIE_TAISHI
    best_ratio = 0
    best_pair = ''
    for mu, zi in MUMIE_TAISHI.items():
        if dz[zi] > 0:
            ratio = dz[mu] / dz[zi]
            if ratio > best_ratio:
                best_ratio = ratio
                best_pair = f'{mu}/{zi}'
    print(f'  {name}: {best_pair} = {best_ratio:.1f}')

print()
print('=== 真母灭盘党众比 ===')
for b, s, dm, name in right:
    dz = calc_dangzhong(b, s)
    from engines.common.mumie_checker import MUMIE_TAISHI
    best_ratio = 0
    best_pair = ''
    for mu, zi in MUMIE_TAISHI.items():
        if dz[zi] > 0:
            ratio = dz[mu] / dz[zi]
            if ratio > best_ratio:
                best_ratio = ratio
                best_pair = f'{mu}/{zi}'
    print(f'  {name}: {best_pair} = {best_ratio:.1f}')
