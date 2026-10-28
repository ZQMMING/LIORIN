# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

for case in ['庚辰己丑己亥壬申', '壬辰辛亥戊子癸丑', '己巳辛未丙午丁酉']:
    p = gp(case)
    f = l0build(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    sp = build_special_patterns(p, f, wp)
    print(f'=== {case} ===')
    print('  cong_type:', sp.get('cong_type'))
    print('  cong_state:', sp.get('cong_state'))
    print('  zhuanwang:', sp.get('zhuanwang'))
    print('  judgment_status:', sp.get('judgment_status'))
    print()
