# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

case = '丙子己亥乙丑壬午'
p = gp(case)
f = l0build(p)
cfc = f.get('combination_facts', {})

print('=== combination_facts keys ===')
for k in cfc.keys():
    v = cfc[k]
    print(f'{k}: {v}')
