# -*- coding: utf-8 -*-
"""作用有效性原典审计 - 证据地图扫描(只读)
扫描六经典 evidence registry, 按"作用有效性判词群"统计命中并取样例 evidence_id.
不修改任何引擎代码, 不下结论, 只建立证据地图供精读.
"""
import json, glob, os, collections

EVDIR = os.path.join(os.path.dirname(__file__), '..', 'registries', 'evidence')

# 每部经典的全量文件
FILES = {
    'PZZQ': ['pzzq_evidence.jsonl', 'evidence.pzzq.jsonl'],
    'DTS': ['dts_evidence.jsonl', 'evidence.dts.jsonl'],
    'YHZP': ['yhzp_evidence.jsonl', 'evidence.yhzp.jsonl'],
    'SMTH': ['smth_evidence.jsonl', 'evidence.smth.jsonl'],
    'SFTK': ['sftk_evidence.jsonl', 'evidence.sftk.jsonl'],
    'QTBJ': ['qtbj_evidence.jsonl', 'evidence.qtbj.jsonl'],
}

# 判词群(繁体, 按子问题分组)
GROUPS = {
    'A_发动动静': ['發動', '引動', '沖動', '動', '靜'],
    'B_根有效': ['根拔', '通根', '根深', '根氣', '虛浮', '蓋頭', '截腳', '無根', '有根'],
    'C_生克有效': ['通關', '貪生忘克', '克處逢生', '旺不受克', '相生', '相克', '制化'],
    'D_合化有效': ['合化', '合而不化', '爭合', '妒合', '化神', '得化', '不化'],
    'E_透藏得用': ['透出', '透干', '得用', '有力', '無力', '得令', '失令', '得氣', '司令'],
    'F_成势众寡': ['黨眾', '黨', '助寡', '成勢', '成局', '會局', '源頭', '源流', '氣勢'],
    'G_位置阻隔': ['阻隔', '隔位', '遙合', '相鄰', '隔'],
    'H_真假有情': ['有情', '無情', '真假', '真從', '假從', '順逆'],
}


def load(book):
    rows = []
    for fn in FILES[book]:
        p = os.path.join(EVDIR, fn)
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    # 去重 by evidence_id
    seen, uniq = set(), []
    for r in rows:
        eid = r.get('evidence_id', '')
        if eid and eid not in seen:
            seen.add(eid)
            uniq.append(r)
    return uniq


def text_of(r):
    return (r.get('quotation', '') or '') + ' ' + (r.get('context', '') or '')


def main():
    books = list(FILES.keys())
    corpus = {b: load(b) for b in books}
    print('证据条数:', {b: len(corpus[b]) for b in books})
    print()
    # 矩阵: 组 x 书 命中条数
    for gname, kws in GROUPS.items():
        print('=' * 70)
        print('【' + gname + '】 判词:', '/'.join(kws))
        for b in books:
            hits = []
            for r in corpus[b]:
                t = text_of(r)
                if any(k in t for k in kws):
                    hits.append(r)
            print('  %-5s 命中 %3d 条' % (b, len(hits)))
        print()


if __name__ == '__main__':
    main()
