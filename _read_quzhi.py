# -*- coding: utf-8 -*-
"""读三命通会曲直格章节"""
f = 'registries/source/raw/SMTH_三命通会_原文.md'
with open(f, 'r', encoding='utf-8') as fp:
    lines = fp.readlines()

# line 6859是1-indexed, python是0-indexed
start = 6858
end = 6920
for i in range(start, min(end, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')
