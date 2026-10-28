# -*- coding: utf-8 -*-
"""第一批例盘人工判(不碰引擎)"""
cases = [
    # 专旺格
    ('辛巳酉丑申', '从革?', '金局全'),
    ('己巳午辰戌', '稼穑?', '土局'),
    ('癸申子辰亥', '润下?', '水局'),
    ('丁巳午寅戌', '炎上?', '火局'),
]

print('=== 第一批例盘人工判(引擎不打开) ===')
print()
for i, (bz, guess, note) in enumerate(cases):
    print(f'盘{i+1}: {bz}')
    print(f'  初步判断: {guess} ({note})')
    print()
