# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.transit_power import _build_pure_power

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

case = '丙子己亥乙丑壬午'
p = gp(case)
f = l0build(p)
cfc = f.get('combination_facts', {})
result = _build_pure_power(p, f, cfc, [])

print('=== wuxing_power各五行 ===')
for wx in ('木', '火', '土', '金', '水'):
    d = result['wuxing_power'][wx]
    print(f'{wx}: ben_n={d.get("ben_n")}, ju_n={d.get("ju_n")}, stem_n={d.get("stem_n")}, banhe_n={d.get("banhe_n")}')
