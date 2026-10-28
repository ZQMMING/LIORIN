# -*- coding: utf-8 -*-
"""读取格相关原文"""
f = 'registries/source/raw/SMTH_三命通会_原文.md'
with open(f, 'r', encoding='utf-8') as fp:
    lines = fp.readlines()

# 取格行号: 2264, 11608, 23597
for ln in [2264, 11608, 23597]:
    print(f'--- line {ln} ---')
    for i in range(max(0, ln-2), min(len(lines), ln+3)):
        print(f'{i+1}: {lines[i]}', end='')
    print()
