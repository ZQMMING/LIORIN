# -*- coding: utf-8 -*-
from spec.root_qi import BRANCH_CANGGAN, STEM_WUXING

def build_root_detail(pillars):
    """逐地支藏干 → 每五行的root_detail字典"""
    all_branches = []
    for k in ('year', 'month', 'day', 'hour'):
        if k in pillars:
            all_branches.append(pillars[k][1])
    # extra_pillars的支也加上
    rd = {wx: {} for wx in ('木', '火', '土', '金', '水')}
    for b in all_branches:
        cg = BRANCH_CANGGAN.get(b, ('', '', ''))
        if cg[0] and STEM_WUXING.get(cg[0]):
            rd[STEM_WUXING[cg[0]]][b] = 'BEN'
        if cg[1] and STEM_WUXING.get(cg[1]):
            rd[STEM_WUXING[cg[1]]].setdefault(b, 'ZHONG')
        if cg[2] and STEM_WUXING.get(cg[2]):
            rd[STEM_WUXING[cg[2]]].setdefault(b, 'YU')
    return rd

# 测试
if __name__ == '__main__':
    p = {'year': ['庚', '辰'], 'month': ['己', '丑'], 'day': ['己', '亥'], 'time': ['壬', '申']}
    rd = build_root_detail(p)
    for wx, branches in rd.items():
        if branches:
            print(f'{wx}: {branches}')
