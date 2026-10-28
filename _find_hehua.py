# -*- coding: utf-8 -*-
"""查三命通会: 三合局全时月令取格规则"""
f = 'registries/source/raw/SMTH_三命通会_原文.md'
with open(f, 'r', encoding='utf-8') as fp:
    text = fp.read()

# 找"合化"相关段
keywords = ['合化', '化气', '三合局全', '取格', '月令']
for kw in keywords:
    lines = [i+1 for i, line in enumerate(text.split('\n')) if kw in line]
    print(f'{kw}: {len(lines)}行, 行号{lines[:5]}')
