# -*- coding: utf-8 -*-
"""用神专题开审对齐 - 六经典口径证据地图(只读)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from audit_effectiveness_scan import load, text_of

GROUPS = {
    'A_用神总名': ['用神', '相神', '喜神', '忌神', '仇神'],
    'B_月令定格取用': ['專求月令', '月令', '定格', '格神', '司令', '立格'],
    'C_体用': ['體用', '體', '為用', '所用'],
    'D_调候': ['調候', '寒暖', '燥濕', '寒', '暖', '潤', '燠'],
    'E_病药': ['病藥', '去病', '藥', '病在', '無病'],
    'F_DTS取用方式': ['通關', '源流', '從化', '順局', '反局', '扶抑', '抑強', '衆寡'],
    'G_扶抑身强弱取用': ['身強', '身弱', '身旺', '身衰', '扶身', '抑', '損益', '補瀉'],
}


def main():
    books = ['PZZQ', 'DTS', 'YHZP', 'SMTH', 'SFTK', 'QTBJ']
    corpus = {b: load(b) for b in books}
    print('证据条数:', {b: len(corpus[b]) for b in books})
    for gname, kws in GROUPS.items():
        print('=' * 72)
        print('【' + gname + '】', '/'.join(kws))
        for b in books:
            n = sum(1 for r in corpus[b] if any(k in text_of(r) for k in kws))
            print('  %-5s %3d 条' % (b, n))
        print()


if __name__ == '__main__':
    main()
