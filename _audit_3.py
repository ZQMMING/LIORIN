# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.climate_structure import build_climate_structure

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

# 高危3个用例
cases = [
    ('丁亥壬寅丙午丁酉', '炎上CANDIDATE→从杀格CANDIDATE'),
    ('己卯丁卯壬午癸卯', '化木CONFIRMED→从财格CANDIDATE'),
    ('甲寅乙亥乙卯癸未', '曲直None→从旺格CANDIDATE'),
    ('戊午丙辰戊辰辛酉', '稼穑CONFIRMED→从旺格CANDIDATE'),
]

for case, desc in cases:
    p = gp(case)
    f = l0build(p)
    th = build_tian_he(p, f)
    wp = build_wuxing_power(p, f, th)
    cls = build_climate_structure(p, f, th)
    sp = build_special_patterns(p, f, wp, th, cls)
    
    print(f'=== {case} ({desc}) ===')
    print(f'  日主: {p["day"][0]} ({wp["daymaster_element"]})')
    print(f'  cong_type: {sp.get("cong_type")}')
    print(f'  cong_state: {sp.get("cong_state")}')
    print(f'  zhuanwang: {sp.get("zhuanwang")}')
    print(f'  zhuanwang_state: {sp.get("zhuanwang_state")}')
    print(f'  hua_qi: {sp.get("hua_qi")}')
    
    # 看wp计数
    pw = wp['wuxing_power']
    dm_wx = wp['daymaster_element']
    print(f'  日主{dm_wx}: ben_n={pw[dm_wx]["ben_n"]}, stem_n={pw[dm_wx]["stem_n"]}, ju_n={pw[dm_wx]["ju_n"]}')
    print(f'  官杀: ben_n={pw.get(pw_wx := {"木":"金","火":"水","土":"木","金":"火","水":"土"}[dm_wx], {}).get("ben_n",0)}, stem_n={pw[pw_wx].get("stem_n",0)}')
    print()
