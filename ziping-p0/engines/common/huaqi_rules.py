# -*- coding: utf-8 -*-
"""PATCH-049 化气五格规则（YHZP-121-003 B级注层）"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

HE = {'甲': ('己', '土', '甲己化土'), '己': ('甲', '土', '甲己化土'),
      '乙': ('庚', '金', '乙庚化金'), '庚': ('乙', '金', '乙庚化金'),
      '丙': ('辛', '水', '丙辛化水'), '辛': ('丙', '水', '丙辛化水'),
      '丁': ('壬', '木', '丁壬化木'), '壬': ('丁', '木', '丁壬化木'),
      '戊': ('癸', '火', '戊癸化火'), '癸': ('戊', '火', '戊癸化火')}
HUA_MONTH = {
    '土': ['辰', '戌', '丑', '未'], '金': ['申', '酉', '戌'],
    '水': ['亥', '子', '丑'], '木': ['寅', '卯', '辰'], '火': ['巳', '午', '未']
}


def huaqi_rule(c):
    day = c['dm']; stems = c['stems']
    if day not in HE:
        return None
    partner, hua_elem, hua_name = HE[day]
    he_vis = any(s == partner for s in stems)
    if not he_vis:
        return None
    if c['month'] not in HUA_MONTH[hua_elem]:
        return None
    return {'pattern_state': f'DETERMINED({hua_name})',
            'pattern_success_state': 'SUCCESS(化氣真)',
            'condition_context': f'{day}{partner}合化{hua_elem}，月令化神生旺',
            'evidence': ['YHZP-121-003'], 'note': f'{hua_name}成：化氣則棄原局；B級注層'}


if __name__ == '__main__':
    cases = [
        ('GC-016 甲己化土', 1960, 7, 10),
        ('GC-017 乙庚化金', 1960, 8, 0),
        ('GC-018 丁壬化木', 1960, 3, 14),
        ('GC-019 戊癸化火', 1960, 5, 12),
    ]
    for name, y, m, h in cases:
        p = paipan(y, m, 15, h)
        c = {'dm': p['day_master'], 'stems': [p['stems']['年'], p['stems']['月'], p['stems']['时']],
             'month': p['month_order']}
        r = huaqi_rule(c)
        print(f'{name}: {p["pillars"]} 日主={p["day_master"]}')
        print(f'  → {r}')
