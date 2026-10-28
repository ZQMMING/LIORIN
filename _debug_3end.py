# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
SHENG_ME = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}

cases = [
    ('癸卯甲寅丁卯甲辰', '木多火熄'),
    ('丙子己亥乙丑壬午', '水多木漂'),
    ('己亥丙子乙丑壬午', '水多木漂'),
    ('戊戌丙辰辛丑戊戌', '土重金埋(已绿)'),
]

for case, desc in cases:
    p = gp(case)
    f = l0build(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    pw = wp['wuxing_power']
    dm_wx = wp['daymaster_element']
    
    yin_wx = SHENG_ME[dm_wx]  # 印
    ss_wx = SHENG[dm_wx]      # 食伤
    gs_wx = KE[dm_wx]         # 官杀
    cai_wx = KE[yin_wx]       # 财（印之克=财）
    
    yin = pw.get(yin_wx, {})
    ss = pw.get(ss_wx, {})
    gs = pw.get(gs_wx, {})
    cai = pw.get(cai_wx, {})
    
    yin_ben = int(yin.get('ben_n', 0))
    yin_ju = int(yin.get('ju_n', 0))
    yin_stem = int(yin.get('stem_n', 0))
    ss_ben = int(ss.get('ben_n', 0))
    ss_stem = int(ss.get('stem_n', 0))
    gs_stem = int(gs.get('stem_n', 0))
    cai_ben = int(cai.get('ben_n', 0))
    cai_stem = int(cai.get('stem_n', 0))
    
    print(f'=== {case} ({desc}) ===')
    print(f'  日主{dm_wx}: 印={yin_wx}, 食伤={ss_wx}, 官杀={gs_wx}, 财={cai_wx}')
    print(f'  印: ben={yin_ben}, ju={yin_ju}, stem={yin_stem}')
    print(f'  食伤: ben={ss_ben}, stem={ss_stem}')
    print(f'  官杀: stem={gs_stem}')
    print(f'  财: ben={cai_ben}, stem={cai_stem}')
    print()
