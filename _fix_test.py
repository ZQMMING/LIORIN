# -*- coding: utf-8 -*-
p = 'tests/test_transit_power_golden.py'
c = open(p, encoding='utf-8').read()

# 七档→四档映射
c = c.replace("order = ['衰极','太衰','衰','中和','旺','太旺','旺极']",
              "order = ['衰', '平', '旺', '强']")
c = c.replace("tp0['spectrum']['spectrum'] == '衰极'",
              "tp0['spectrum']['spectrum'] == '衰'")
c = c.replace("order.index('衰极')", "order.index('衰')")
c = c.replace("tp['spectrum']['spectrum'] == '太旺'",
              "tp['spectrum']['spectrum'] == '强'")
c = c.replace("tp5['wuxing_power']['month_element']", "tp5['month_element']")

open(p, 'w', encoding='utf-8').write(c)
print('done, replacements applied')
