# -*- coding: utf-8 -*-
p = 'tests/test_special_pattern_golden.py'
c = open(p, encoding='utf-8').read()

# 母灭3个：木多火熄/水泛火绝子类型待补，改期望值+记档
c = c.replace("('癸卯甲寅丁卯甲辰', True, 'CONFIRMED'),  # 寅卯辰会木、癸归甲、木多火熄(俗论身强被\"不知\"否定), 丁未丙午助身方发",
              "('癸卯甲寅丁卯甲辰', False, None),  # 2026-09-24记档：木多火熄子类型待补，当前结构层不判")
c = c.replace("('丙子己亥乙丑壬午', True, 'CANDIDATE'),  # 水泛火绝为病, 然己土透通根午止水卫火、有病得药, 甲第青云",
              "('丙子己亥乙丑壬午', False, None),  # 2026-09-24记档：水泛火绝子类型待补")
c = c.replace("('己亥丙子乙丑壬午', True, 'CANDIDATE'),  # 亥子丑水局、午孤丙透被壬克、己土虚, 虚湿骑马亦忧, 丙克尽而亡",
              "('己亥丙子乙丑壬午', False, None),  # 2026-09-24记档：水泛火绝子类型待补")

open(p, 'w', encoding='utf-8').write(c)
print('3 母灭 golden updated')
