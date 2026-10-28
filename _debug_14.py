# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.climate_structure import build_climate_structure

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

# 14个FAIL用例
cases = [
    ('戊申己未丙戌己丑', '从儿', 'CONFIRMED'),
    ('己巳辛未丙午丁酉', '炎上', 'CONFIRMED'),
    ('癸巳戊午丙午壬辰', '炎上', 'CANDIDATE'),
    ('甲寅乙亥乙卯癸未', '曲直', None),
    ('庚午壬午丙寅庚寅', '炎上', 'CANDIDATE'),
    ('庚戌壬午丙寅己亥', '炎上', 'CANDIDATE'),
    ('丁亥壬寅丙午丁酉', '炎上', 'CANDIDATE'),
    ('己丑丙子壬辰戊申', '润下', 'CANDIDATE'),
    ('戊午丙辰戊辰辛酉', '稼穑', 'CONFIRMED'),
    ('己卯丁卯壬午癸卯', '化木', 'CONFIRMED'),
    ('己卯甲戌甲子己巳', '化土', 'CANDIDATE'),
    ('癸卯甲寅丁卯甲辰', '母灭', True),
    ('丙子己亥乙丑壬午', '母灭', True),
    ('己亥丙子乙丑壬午', '母灭', True),
]

for case, exp_name, exp_state in cases:
    p = gp(case)
    f = l0build(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    cls = build_climate_structure(p, f, th)
    sp = build_special_patterns(p, f, wp, th, cls)
    
    got = sp['cong_type'] or sp['zhuanwang'] or sp['hua_qi'] or ('母灭' if sp.get('mu_mie') else '无')
    got_state = sp.get('cong_state') or sp.get('zhuanwang_state') or sp.get('mu_mie_state') or '无'
    
    print(f'{case:20s} 期望[{exp_name}/{exp_state}] 得[{got}/{got_state}]')
