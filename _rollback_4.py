# -*- coding: utf-8 -*-
p = 'tests/test_special_pattern_golden.py'
c = open(p, encoding='utf-8').read()

# ① 丁亥壬寅丙午丁酉：回滚——原意对，代码缺六合化神归化逻辑
c = c.replace(
    "('丁亥壬寅丙午丁酉', '从杀格', 'CANDIDATE'),  # 2026-09-24裁决：从杀格CANDIDATE",
    "('丁亥壬寅丙午丁酉', '炎上', 'CANDIDATE'),   # 寅亥合木(寅月化神当令), 亥杀化印 — 挂单：六合化神归化分支待补"
)

# ②③ 母灭3条：回滚——代码缺分支，golden原意对
c = c.replace(
    "('癸卯甲寅丁卯甲辰', False, None),  # 2026-09-24记档：木多火熄子类型待补，当前结构层不判",
    "('癸卯甲寅丁卯甲辰', True, 'CONFIRMED'),  # 寅卯辰会木、癸归甲、木多火熄 — 挂单：母灭分支待补"
)
c = c.replace(
    "('丙子己亥乙丑壬午', False, None),  # 2026-09-24记档：水泛火绝子类型待补",
    "('丙子己亥乙丑壬午', True, 'CANDIDATE'),  # 水泛火绝为病, 然己土透通根午止水卫火 — 挂单：母灭分支待补"
)
c = c.replace(
    "('己亥丙子乙丑壬午', False, None),  # 2026-09-24记档：水泛火绝子类型待补",
    "('己亥丙子乙丑壬午', True, 'CANDIDATE'),  # 亥子丑水局、午孤丙透被壬克、己土虚 — 挂单：母灭分支待补"
)

open(p, 'w', encoding='utf-8').write(c)
print('4 golden rolled back')
