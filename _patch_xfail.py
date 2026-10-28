# -*- coding: utf-8 -*-
"""补XFAIL手续"""
f = 'registries/decisions/L2_closure.md'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

old = '### 已知误判(XFAIL在押)\n- #035-③: 子行无救应判定缺失(库根救应)'
new = '''### 已知误判(XFAIL在押)
- #035-③: 子行无救应判定缺失(库根救应) — 押盘1: 卯寅卯戌+癸甲甲甲(丙)
- #035-③: 木多火熄盘边界函数暴露 — 押盘2: 癸卯甲寅丁卯甲辰(丁) — 1.5→库档→不判熄, ③实现后转PASS'''

c = c.replace(old, new)

# 同步改总账
c = c.replace('| XFAIL在押 | 1个(#035-③) |', '| XFAIL在押 | 2个(#035-③) |')

with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
