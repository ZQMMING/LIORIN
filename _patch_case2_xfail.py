# -*- coding: utf-8 -*-
"""盘②打XFAIL标记"""
f = 'tests/test_special_pattern_golden.py'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

old = "('丁亥壬寅丙午丁酉', '炎上', 'CANDIDATE'),   # 寅亥合木(寅月化神当令), 亥杀化印 — 挂单：六合化神归化分支待补"
new = "('丁亥壬寅丙午丁酉', '炎上', 'CANDIDATE'),   # XFAIL #037双CAND并存逻辑未实现, 当前只判从杀单CAND"

c = c.replace(old, new)
with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
