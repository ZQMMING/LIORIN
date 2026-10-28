# -*- coding: utf-8 -*-
"""化气五格扫描：日干合干相邻+月令化神生旺"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
BENQI = {k: v[0] for k, v in HIDDEN.items()}

# 五合化
HE = {'甲': ('己', '土'), '己': ('甲', '土'), '乙': ('庚', '金'), '庚': ('乙', '金'),
      '丙': ('辛', '水'), '辛': ('丙', '水'), '丁': ('壬', '木'), '壬': ('丁', '木'),
      '戊': ('癸', '火'), '癸': ('戊', '火')}
# 化神生旺月令（土旺四季月/火午/水子/木卯/金酉）
HUA_MONTH = {
    '土': ['辰', '戌', '丑', '未'], '金': ['申', '酉', '戌'],
    '水': ['亥', '子', '丑'], '木': ['寅', '卯', '辰'], '火': ['巳', '午', '未']
}

if __name__ == '__main__':
    hits = []
    for y in range(1960, 2011):
        for m in range(1, 13):
            for h in range(0, 24, 2):
                p = paipan(y, m, 15, h)
                dm = p['day_master']
                stems = [p['stems']['年'], p['stems']['月'], p['stems']['时']]
                if dm not in HE:
                    continue
                partner, hua_elem = HE[dm]
                # 合干在月干或时干（相邻）
                he_vis = [i for i, s in enumerate(stems) if s == partner]
                if not he_vis:
                    continue
                # 月令化神生旺
                if p['month_order'] not in HUA_MONTH[hua_elem]:
                    continue
                # 无克破：天干无克化神之干透出（简化：不深查）
                hits.append((y, m, h, p['pillars'], dm, partner, hua_elem))

    print('==== 化气格候選 ====')
    for y, m, h, pl, dm, partner, hua in hits[:12]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  {dm}{partner}化{hua}')
    print(f'  共 {len(hits)}')
