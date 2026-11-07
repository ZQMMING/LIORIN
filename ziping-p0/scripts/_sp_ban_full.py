# -*- coding: utf-8 -*-
"""核3 BAN 186 全量断语反查: regex前置(拦因特征词) + 断语全文输出, 逐盘人工核支持/反对/待核。"""
import json, glob, re, sys
sys.path.insert(0, '.')

def case_lookup():
    m = {}
    for f in glob.glob('p0_v2/case_audit/*_clean.jsonl'):
        for l in open(f, encoding='utf-8'):
            d = json.loads(l)
            m[d['case_id']] = d
    return m

CASES = case_lookup()
NEW = json.load(open('scripts/_sp_audit_new.json', encoding='utf-8'))

def bans(d):
    out = []
    for p in d.get('pats', []):
        if p and p[0] == 'ZP-SPECIAL-CONG-BAN':
            out.append((p[1], p[3] if len(p) > 3 else ''))
    return out

rows = []
for cid, d in NEW.items():
    for reason, note in bans(d):
        c = CASES.get(cid, {})
        rows.append((cid, reason, c.get('label'), c.get('analysis', '')[:140], c.get('bazi', '')))

# 按拦因分组输出
from collections import defaultdict
groups = defaultdict(list)
for r in rows:
    groups[r[1]].append(r)

print("BAN 全量 %d 盘, 分组:\n" % len(rows))
for reason, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print("### %s (%d 盘)" % (reason, len(items)))
    for cid, reason, label, ana, bz in items:
        ana1 = ana.replace('\n', ' ').strip()
        print("  %s [%s] %s | %s" % (cid, label, bz, ana1))
    print()
