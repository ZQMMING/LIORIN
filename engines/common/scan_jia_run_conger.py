# -*- coding: utf-8 -*-
"""稼穡/潤下/從兒 三格扫描"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
gen = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

if __name__ == '__main__':
    jiase, runxia, conger = [], [], []
    for y in range(1980, 2006):
        for m in range(1, 13):
            for h in range(0, 24, 2):
                p = paipan(y, m, 15, h)
                dm = p['day_master']
                stems = [p['stems']['年'], p['stems']['月'], p['stems']['时']]
                br = list(p['branches'].values())
                br_set = set(br)
                # 稼穡：戊己日 + 辰戌丑未四库全
                if ELEM[dm] == '土':
                    if all(x in br_set for x in ['辰', '戌', '丑', '未']):
                        jiase.append((y, m, h, p['pillars'], dm))
                # 潤下：壬癸日 + 申子辰三合 或 亥子丑三会
                if ELEM[dm] == '水':
                    sanhe = all(x in br_set for x in ['申', '子', '辰'])
                    sanhui = all(x in br_set for x in ['亥', '子', '丑'])
                    if sanhe or sanhui:
                        runxia.append((y, m, h, p['pillars'], dm))
                # 從兒：日主所生五行(食伤)成局/成方；土日主食伤=金，走金局
                er_elem = gen[ELEM[dm]]
                ju_map = {'火': ['寅', '午', '戌'], '水': ['申', '子', '辰'],
                          '金': ['巳', '酉', '丑'], '木': ['亥', '卯', '未'],
                          '土': ['巳', '酉', '丑']}
                hui_map = {'火': ['巳', '午', '未'], '水': ['亥', '子', '丑'],
                           '金': ['申', '酉', '戌'], '木': ['寅', '卯', '辰'],
                           '土': ['申', '酉', '戌']}
                sanhe = ju_map[er_elem] and all(x in br_set for x in ju_map[er_elem])
                sanhui = hui_map[er_elem] and all(x in br_set for x in hui_map[er_elem])
                if sanhe or sanhui:
                    conger.append((y, m, h, p['pillars'], dm, er_elem))

    print('==== 稼穡格候選(戊己日四库全) ====')
    for y, m, h, pl, dm in jiase[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(jiase)}\n')
    print('==== 潤下格候選(壬癸日水局) ====')
    for y, m, h, pl, dm in runxia[:6]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}')
    print(f'  共 {len(runxia)}\n')
    print('==== 從兒格候選(食伤成局) ====')
    for y, m, h, pl, dm, er in conger[:8]:
        print(f'  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm} 兒={er}')
    print(f'  共 {len(conger)}')
