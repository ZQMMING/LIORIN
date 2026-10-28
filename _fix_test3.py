# -*- coding: utf-8 -*-
p = 'tests/test_transit_power_golden.py'
c = open(p, encoding='utf-8').read()
c = c.replace("'TRANSIT_POWER_STRUCTURE_ONLY'", "'TRANSIT_POWER_PURE_RULE'")
open(p, 'w', encoding='utf-8').write(c)
print('done')
