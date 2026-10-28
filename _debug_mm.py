# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

# 3个母灭FAIL用例
cases = [
    ('癸卯甲寅丁卯甲辰', '木多火熄'),
    ('丙子己亥乙丑壬午', '水多木漂'),
    ('己亥丙子乙丑壬午', '水多木漂'),
]

SHENG_ME = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}

for case, desc in cases:
    p = gp(case)
    f = l0build(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    pw = wp['wuxing_power']
    dm_wx = wp['daymaster_element']
    yin_wx = SHENG_ME[dm_wx]
    
    yin = pw.get(yin_wx, {})
    yin_ben = int(yin.get('ben_n', 0))
    yin_stem = int(yin.get('stem_n', 0))
    yin_ju = int(yin.get('ju_n', 0))
    
    print(f'=== {case} ({desc}) ===')
    print(f'  日主: {dm_wx}, 印: {yin_wx}')
    print(f'  印 ben_n={yin_ben}, stem_n={yin_stem}, ju_n={yin_ju}')
    print(f'  yin_dom = 印成势? (yin_ben>=2 or yin_ju>=1)')
    print()
