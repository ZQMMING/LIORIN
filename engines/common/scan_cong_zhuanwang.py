# -*- coding: utf-8 -*-
"""從殺格(1980-2005, 放宽刑冲) + 曲直格 + 炎上格 扫描"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN  # 已 wrap stdout

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
            'shi_shang': [s for s in GAN if ELEM[s] == gen[de]],
            'sha_elem': me_ke}


def dm_rootless(day, br):
    de = ELEM[day]
    return all(ELEM[h] != de for b in br for h in HIDDEN[b])


def no_shengfu(day, stems):
    de = ELEM[day]
    yin = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[de]
    return all(ELEM[s] not in (de, yin) for s in stems)


def cong_sha(c):
    day = c['dm']; stems = c['stems']; br = c['br']
    tl = ten_lists(day)
    if not dm_rootless(day, br):
        return None
    if not no_shengfu(day, stems):
        return None
    benqi = BENQI[c['month']]
    if not (benqi in tl['sha'] or benqi in tl['guan']):
        return None
    shang_vis = any(s in tl['shi_shang'] for s in stems)
    if shang_vis:
        return None
    # 放宽：官杀局内部允许刑冲，只要求官杀有根
    sha_root = any(ELEM[h] == tl['sha_elem'] for b in br for h in HIDDEN[b])
    if sha_root:
        return True
    return None


SAN_HE = {'木局': ['亥', '卯', '未'], '火局': ['寅', '午', '戌'],
          '金局': ['巳', '酉', '丑'], '水局': ['申', '子', '辰']}
SAN_HUI = ['寅卯辰', '巳午未', '申酉戌', '亥子丑']


def has_sanhe(br_set, ju):
    return all(x in br_set for x in SAN_HE[ju])


def has_sanhui(br_set, hui):
    return all(x in br_set for x in hui)


if __name__ == '__main__':
    sha_hits, quzhi, yan_shang = [], [], []
    for y in range(1980, 2006):
        for m in range(1, 13):
            for h in range(0, 24, 2):
                p = paipan(y, m, 15, h)
                dm = p['day_master']
                stems = [p['stems']['年'], p['stems']['月'], p['stems']['时']]
                br = list(p['branches'].values())
                br_set = set(br)
                c = {'dm': dm, 'stems': stems, 'br': br, 'month': p['month_order']}
                # 從殺
                if cong_sha(c):
                    sha_hits.append((y, m, h, p['pillars'], dm))
                # 曲直：甲乙日 + 木局/木方 + 不见庚辛
                if ELEM[dm] == '木':
                    ju_ok = has_sanhe(br_set, '木局') or has_sanhui(br_set, '寅卯辰')
                    no_gengxin = not any(s in ('庚', '辛') for s in stems)
                    if ju_ok and no_gengxin:
                        quzhi.append((y, m, h, p['pillars'], dm))
                # 炎上：丙丁日 + 火局/火方
                if ELEM[dm] == '火':
                    ju_ok = has_sanhe(br_set, '火局') or has_sanhui(br_set, '巳午未')
                    if ju_ok:
                        yan_shang.append((y, m, h, p['pillars'], dm))

    print('==== 從殺格候選(1980-2005) ====')
    for y, m, h, pl, dm in sha_hits[:8]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(sha_hits)}\n')
    print('==== 曲直格候選 ====')
    for y, m, h, pl, dm in quzhi[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(quzhi)}\n')
    print('==== 炎上格候選 ====')
    for y, m, h, pl, dm in yan_shang[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(yan_shang)}')
