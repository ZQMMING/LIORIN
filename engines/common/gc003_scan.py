# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
GAN = '甲乙丙丁戊己庚辛壬癸'
BENQI = {k: v[0] for k, v in HIDDEN.items()}

# 地支关系表（两支即论）
CHONG = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), ('辰', '戌'), ('巳', '亥')]
XING = [('寅', '巳', '申'), ('丑', '戌', '未'), ('子', '卯')]        # 三刑（子卯两支论）
HAI = [('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'), ('申', '亥'), ('酉', '戌')]
PO = [('子', '酉'), ('午', '卯'), ('巳', '申'), ('寅', '亥'), ('辰', '丑'), ('戌', '未')]


def rel_sets(*pairs):
    return {frozenset(p) for p in pairs}


CHONG_S, XING_S, HAI_S, PO_S = (
    rel_sets(*CHONG), rel_sets(*XING), rel_sets(*HAI), rel_sets(*PO))


def xingchong_pohai(branches):
    """返回四支中的刑冲破害关系列表；三刑按三支齐论，子卯两支论"""
    bs = list(branches.values())
    hits = []
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = bs[i], bs[j]
            s = frozenset((a, b))
            if s in CHONG_S: hits.append(f"{a}{b}冲")
            if s in HAI_S: hits.append(f"{a}{b}害")
            if s in PO_S: hits.append(f"{a}{b}破")
    for g in XING:
        if len(g) == 3 and all(x in bs for x in g):
            hits.append("".join(g) + "三刑")
    if '子' in bs and '卯' in bs:
        hits.append("子卯刑")
    return hits


def is_guan(bq, dm):
    me_ke = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}[ELEM[dm]]
    if ELEM[bq] != me_ke:
        return False
    return (GAN.index(bq) % 2) != (GAN.index(dm) % 2)


found = []
for y in range(1990, 1996):
    for m in range(1, 13):
        for h in range(0, 24, 2):
            p = paipan(y, m, 15, h)
            if not is_guan(BENQI[p['month_order']], p['day_master']):
                continue
            hits = xingchong_pohai(p['branches'])
            if not hits:
                found.append((y, m, h, p))
for y, m, h, p in found[:8]:
    print(f"{y}-{m}-15 {h:02d}:00  {p['pillars']}  日主={p['day_master']} 月={p['month_order']}"
          f"（本气{BENQI[p['month_order']]}=正官）→ 官格，四支零刑冲破害 ✓")
print(f"\n零刑冲破害官格共 {len(found)} 个")
