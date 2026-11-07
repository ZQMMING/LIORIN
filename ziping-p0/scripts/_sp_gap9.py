# -*- coding: utf-8 -*-
import json, collections
n901 = json.load(open('scripts/_sp_audit_new.json', encoding='utf-8'))
cur = json.load(open('scripts/_sp_audit_cur.json', encoding='utf-8'))

def pid(p):
    return p[0] if isinstance(p, list) else str(p)

def classify(r):
    pats = r.get('pats') or []
    if any(str(pid(x)).startswith('ZP-SPECIAL-CONG-BAN') for x in pats):
        return 'BAN'
    if r.get('cong_type') is not None or pats:
        return 'NONBAN'
    return 'NONE'

banc = [k for k in n901 if classify(n901[k]) == 'BAN' and n901[k].get('cong_type')]
print('901 BAN且cong_type非None:', len(banc))
for k in sorted(banc)[:20]:
    print(' ', k, n901[k].get('cong_type'), n901[k].get('cong_state'),
          [pid(x) for x in (n901[k].get('pats') or [])])

cf901 = set(k for k in n901 if n901[k].get('cong_type') == '从儿格' and n901[k].get('cong_state') == 'CONFIRMED')
cfcur = set(k for k in cur if cur[k].get('cong_type') == '从儿格' and cur[k].get('cong_state') == 'CONFIRMED')
print('901从儿CF', len(cf901), 'cur从儿CF', len(cfcur))
print('cur有901无:', sorted(cfcur - cf901))
print('901有cur无:', sorted(cf901 - cfcur))
for k in sorted(cfcur - cf901):
    print('  cur:', k, [pid(x) for x in (cur[k].get('pats') or [])],
          '| 901:', n901[k].get('cong_type'), n901[k].get('cong_state'),
          [pid(x) for x in (n901[k].get('pats') or [])])

# 双向完整 diff: 901 vs cur 的 cong_type 变化
diff = collections.Counter()
for k in n901:
    a = (n901[k].get('cong_type'), n901[k].get('cong_state'))
    b = (cur[k].get('cong_type'), cur[k].get('cong_state'))
    if a != b:
        diff[(a, b)] += 1
print('901->cur cong_type 变化:', dict(diff))
