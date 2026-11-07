# -*- coding: utf-8 -*-
"""严格盘级唯一分类：无 / BAN / 非BAN命中。闭合核对 2106。"""
import json, sys, collections

def load(p):
    d = json.load(open(p, encoding='utf-8'))
    return d  # dict keyed by case_id

def pat_id(p):
    return p[0] if isinstance(p, list) else str(p)

def classify(rec):
    pats = rec.get('pats') or []
    ct, cs = rec.get('cong_type'), rec.get('cong_state')
    has_cong = ct is not None
    has_pat = len(pats) > 0
    is_ban = any(str(pat_id(x)).startswith('ZP-SPECIAL-CONG-BAN') for x in pats)
    if is_ban:
        return 'BAN'
    if has_cong or has_pat:
        return 'NONBAN'
    return 'NONE'

old = load('scripts/_sp_audit.json')
new = load('scripts/_sp_audit_new.json')

print('=== 盘级唯一分类 ===')
for tag, d in (('OLD', old), ('NEW', new)):
    c = collections.Counter(classify(d[k]) for k in d)
    tot = sum(c.values())
    print(f'{tag}: {dict(c)}  total={tot}')
    if tot != 2106:
        print(f'  !! total != 2106, diff={tot-2106}')

# BAN 成分：原主从 vs 原追加
print()
print('=== NEW BAN 186: 原主从/原追加 ===')
ban_old_cong = 0; ban_old_add = 0; ban_old_none = 0
ban_pat_hist = collections.Counter()
for k in new:
    if classify(new[k]) != 'BAN':
        continue
    oldr = old.get(k)
    oct_, ocs = (oldr.get('cong_type'), oldr.get('cong_state')) if oldr else (None, None)
    opats = (oldr.get('pats') or []) if oldr else []
    if oct_ is not None:
        ban_old_cong += 1
    elif opats:
        ban_old_add += 1
    else:
        ban_old_none += 1
    for p in new[k].get('pats') or []:
        ban_pat_hist[pat_id(p)] += 1
print(f'BAN∩旧主从={ban_old_cong}  BAN∩旧追加={ban_old_add}  BAN∩旧无={ban_old_none}')
print('BAN pattern 分布:')
for p, n in ban_pat_hist.most_common():
    print(f'  {p}: {n}')

# 差 9 定位：§20.2 报 无1669/非BAN260/BAN186 = 2115
print()
print('=== §20.2 报数 vs 实测 ===')
c = collections.Counter(classify(new[k]) for k in new)
print(f'实测: 无={c["NONE"]} 非BAN={c["NONBAN"]} BAN={c["BAN"]} 合计={c["NONE"]+c["NONBAN"]+c["BAN"]}')
print(f'§20.2 报: 无=1669 非BAN=260 BAN=186 合计=2115')

# 非BAN 260 成分
print()
print('=== NEW 非BAN 成分 ===')
nonban_cong = collections.Counter()
nonban_add = collections.Counter()
for k in new:
    if classify(new[k]) != 'NONBAN':
        continue
    r = new[k]
    if r.get('cong_type'):
        nonban_cong[(r['cong_type'], r.get('cong_state'))] += 1
    for p in r.get('pats') or []:
        nonban_add[pat_id(p)] += 1
print('主从:', dict(nonban_cong), '=', sum(nonban_cong.values()))
print('追加:', dict(nonban_add), '=', sum(nonban_add.values()))

# 静默消 5 盘前后对比
print()
print('=== 静默消 5 盘前后对比 ===')
for k in ('DT-0075', 'DT-0108', 'DT-0332', 'QT-0483', 'YH-0039'):
    o, n = old.get(k), new.get(k)
    def brief(r):
        if not r: return None
        return (r.get('cong_type'), r.get('cong_state'), [str(x) for x in (r.get('pats') or [])])
    print(f'{k}: OLD={brief(o)}  NEW={brief(n)}')
