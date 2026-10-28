# -*- coding: utf-8 -*-
p = 'tests/test_transit_power_golden.py'
c = open(p, encoding='utf-8').read()

# 恢复month_element路径（我之前改错了）
c = c.replace("tp5['month_element']", "tp5['wuxing_power']['month_element']")

# 改judgment_status期望值（案1改成了PURE_RULE）
c = c.replace("judgment_status == '结构only'", "judgment_status == 'TRANSIT_POWER_PURE_RULE'")

open(p, 'w', encoding='utf-8').write(c)
print('done')
