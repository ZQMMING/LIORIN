# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from engines.common.daymaster_root_class import classify_root
import engines.common.l0_fact_builder as m
H = m.HIDDEN

CASES = [
    # 阳干
    ('甲', '亥', 'HEAVY_LONGSHENG', '阳长生'),
    ('甲', '寅', 'HEAVY_LU', '阳禄'),
    ('甲', '卯', 'HEAVY_WANG', '阳帝旺=刃'),
    ('甲', '未', 'LIGHT_MU_KU', '阳墓库(藏乙)'),
    ('甲', '辰', 'LIGHT_YU_QI', '阳余气(辰藏乙)'),
    # 阴干
    ('乙', '午', 'SPECIAL_LONGSHENG_YIN', '阴长生'),
    ('乙', '卯', 'HEAVY_LU', '阴禄'),
    ('乙', '寅', 'HEAVY_WANG', '阴干帝旺位(不论羊刃, 但作重根)'),
    ('乙', '戌', 'NONE', '阴墓库无本气'),
    ('乙', '辰', 'LIGHT_YU_QI', '阴余气(辰藏乙)'),
    # 特殊
    ('己', '丑', 'LIGHT_MU_KU', '阴墓库有本气己'),
    ('丁', '丑', 'NONE', '阴墓库无火'),
    ('丙', '戌', 'LIGHT_MU_KU', '阳火墓库藏丁'),
    ('壬', '辰', 'LIGHT_MU_KU', '阳水墓库藏癸'),
    ('庚', '酉', 'HEAVY_WANG', '阳金帝旺(酉藏辛)'),
    ('甲', '子', 'LIGHT_YU_QI', '甲沐浴子位印根轻根(TONG_GEN.001)'),
    # 四库本气通根(非本干墓): 本气比肩/劫财坐本气=重根 HEAVY_BEN
    ('戊', '辰', 'HEAVY_BEN', '戊见辰本气戊(非墓,墓在戌)'),
    ('戊', '未', 'HEAVY_BEN', '戊见未本气己劫财(非墓)'),
    ('己', '戌', 'HEAVY_BEN', '己见戌本气戊劫财(非墓,墓在丑)'),
    ('己', '未', 'HEAVY_BEN', '己见未本气己(非墓)'),
    ('己', '辰', 'HEAVY_BEN', '己见辰本气戊劫财(非墓)'),
    ('戊', '戌', 'LIGHT_MU_KU', '戊逢本墓戌=墓库轻根(非HEAVY_BEN)'),
]

fails = 0
for dg, z, expect, desc in CASES:
    r = classify_root(dg, z, list(H[z]))
    rc = r['root_class']
    ok = rc == expect
    if not ok:
        fails += 1
    tag = 'PASS' if ok else 'FAIL'
    print(tag, dg + '逢' + z, '[' + desc + '] ->', rc,
          '' if ok else '(期望' + expect + ')', '|', r['basis'])

print()
print('TOTAL', len(CASES), 'FAILS', fails)
sys.exit(1 if fails else 0)
