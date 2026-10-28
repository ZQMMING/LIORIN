# -*- coding: utf-8 -*-
"""改盘①期望"""
f = 'tests/test_special_pattern_golden.py'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

old = "('甲寅乙亥乙卯癸未', '从旺格', 'CANDIDATE'),  # 2026-09-24裁决：从旺格CANDIDATE"
new = "('甲寅乙亥乙卯癸未', '曲直格', 'CONFIRMED'),  # 2026-09-24裁决#036：全局无金透无金藏, 亥卯未+寅卯辰, 曲直成立"

c = c.replace(old, new)
with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
