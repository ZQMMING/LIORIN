# -*- coding: utf-8 -*-
"""作用有效性审计 - 精读抽取(只读): 按判词打印原文+evidence_id."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from audit_effectiveness_scan import load, text_of, FILES

# 用法: python audit_effectiveness_dump.py <book> <kw1,kw2,...> [limit]
book = sys.argv[1]
kws = sys.argv[2].split(',')
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 6

rows = load(book)
n = 0
for r in rows:
    t = text_of(r)
    if any(k in t for k in kws):
        q = (r.get('quotation', '') or '').replace('\n', ' ')
        print('[' + r.get('evidence_id', '?') + '] ' + r.get('chapter', ''))
        print(q[:380])
        print('-' * 60)
        n += 1
        if n >= limit:
            break
print('(共显示', n, '条)')
