# -*- coding: utf-8 -*-
"""找三命通会里的命例"""
import re

f = 'registries/source/raw/SMTH_三命通会_原文.md'
with open(f, 'r', encoding='utf-8') as fp:
    text = fp.read()

# 找四柱格式: XXXX XXXX XXXX XXXX
pattern = r'[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]{4}'
matches = re.findall(pattern, text)
print(f'找到{len(matches)}个四柱格式')
for m in matches[:20]:
    print(f'  {m}')
