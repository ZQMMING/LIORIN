# -*- coding: utf-8 -*-
p = 'tests/test_climate_structure_golden.py'
c = open(p, encoding='utf-8').read()

# 炎上专旺破格裁决：代码对，golden错（财透辛金破格）
c = c.replace(
    "check('己巳辛未 炎上专旺保持', sp['zhuanwang'] == '炎上格')",
    "check('己巳辛未 炎上专旺破格（财透辛金）', sp['zhuanwang'] is None)  # 裁决：专旺忌财透，代码对golden错"
)

open(p, 'w', encoding='utf-8').write(c)
print('climate golden updated')
