# -*- coding: utf-8 -*-
"""從勢/從革/稼穡 扫描"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
GAN = '甲乙丙丁戊己庚辛壬癸'
BENQI = {k: v[0] for k, v in HIDDEN.items()}
gen = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def ten_lists(day):
    de = ELEM[day]
    me_ke = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '木'}[de]
    yang_day = GAN.index(day) % 2 == 0
    def li(elem, same):
        return [s for s in GAN if ELEM[s] == elem and (GAN.index(s) % 2 == 0) == same]
    return {'sha': li(me_ke, yang_day), 'guan': li(me_ke, not yang_day),
            'cai': [s for s in GAN if ELEM[s] == ke[de]],
            'shi_shang': [s for s in GAN if ELEM[s] == gen[de]]}


if __name__ == '__main__':
    congshi, conge, jiase = [], [], []
    for y in range(1960, 2011):
        for m in range(1, 13):
            for h in range(0, 24, 2):
                p = paipan(y, m, 15, h)
                dm = p['day_master']
                stems = [p['stems']['年'], p['stems']['月'], p['stems']['时']]
                br = list(p['branches'].values())
                br_set = set(br)
                tl = ten_lists(dm)
                de = ELEM[dm]
                # 稼穡：戊己日四库全
                if ELEM[dm] == '土' and all(x in br_set for x in ['辰', '戌', '丑', '未']):
                    jiase.append((y, m, h, p['pillars'], dm))
                # 從革：庚辛日金局/金方
                if ELEM[dm] == '金':
                    sanhe = all(x in br_set for x in ['巳', '酉', '丑'])
                    sanhui = all(x in br_set for x in ['申', '酉', '戌'])
                    if sanhe or sanhui:
                        conge.append((y, m, h, p['pillars'], dm))
                # 從勢：日主无根 + 财官伤皆透成势
                yin = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[de]
                rootless = all(ELEM[h] != de for b in br for h in HIDDEN[b])
                no_fu = all(ELEM[s] not in (de, yin) for s in stems)
                has_cai = any(s in tl['cai'] for s in stems)
                has_guan = any(s in (tl['guan'] + tl['sha']) for s in stems)
                has_shi = any(s in tl['shi_shang'] for s in stems)
                if rootless and no_fu and has_cai and has_guan and has_shi:
                    congshi.append((y, m, h, p['pillars'], dm))

    print('==== 稼穡格(1960-2010四库全) ====')
    for y, m, h, pl, dm in jiase[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(jiase)}\n')
    print('==== 從革格(庚辛日金局) ====')
    for y, m, h, pl, dm in conge[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(conge)}\n')
    print('==== 從勢格候選 ====')
    for y, m, h, pl, dm in congshi[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(congshi)}')
