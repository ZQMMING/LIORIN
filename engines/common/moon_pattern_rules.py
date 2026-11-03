# -*- coding: utf-8 -*-
"""
L3-2 月令取格规则表(两轮制)
出处: 子平真诠·论用神
"""

# 第一轮: 月令取正格
MOON_PATTERN_RULES = [
    {
        'rule': '①本气透干',
        'condition': '月支本气在天干透出',
        'result': '取本气为格',
        'source': '子平真诠: 月支本气透於天干, 应先取以为格',
    },
    {
        'rule': '②本气不透, 藏干透干',
        'condition': '本气不透, 但中气或余气透干',
        'result': '取透者为格',
        'source': '子平真诠: 未透本气而透月支所藏之神, 即以该神取为格',
    },
    {
        'rule': '③两神并透',
        'condition': '本气+中气/余气 并透',
        'result': '择有力无克合者为格',
        'source': '子平真诠: 支藏两神并透干上, 斟择其一为格',
    },
    {
        'rule': '④皆不透',
        'condition': '本气+藏干皆不透',
        'result': '以人元轻重较量, 择有力者',
        'source': '子平真诠: 月内人元轻重较量, 择有力而无克合者',
    },
    {
        'rule': '⑤比劫不取格',
        'condition': '月令为禄/刃/比肩',
        'result': '不取格, 走第二轮专旺/外格',
        'source': '子平真诠: 比劫不能取格, 禄刃非在八格之内',
    },
]

# 善神/恶神分类
GOOD_SPIRIT = ['正官', '正印', '偏财', '食神']  # 顺用
BAD_SPIRIT = ['七杀', '伤官', '劫财', '羊刃']  # 逆用


if __name__ == '__main__':
    print('=== L3-2月令取格规则表 ===')
    print()
    print('第一轮: 月令取正格')
    for r in MOON_PATTERN_RULES:
        print(f'  {r["rule"]}: {r["result"]}')
        print(f'    条件: {r["condition"]}')
        print(f'    出处: {r["source"]}')
        print()
    print('善神(顺用):', GOOD_SPIRIT)
    print('恶神(逆用):', BAD_SPIRIT)
