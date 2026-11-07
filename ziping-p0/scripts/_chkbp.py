# -*- coding: utf-8 -*-
import json
old = {}
for l in open('_ys_old.jsonl', encoding='utf-8'):
    r = json.loads(l)
    old[r['id']] = r
new = {}
for l in open('_ys_new.jsonl', encoding='utf-8'):
    r = json.loads(l)
    new[r['id']] = r


def sig(r):
    s = r.get('sp') or {}
    return tuple(str(s.get(k)) for k in ('cong_type', 'cong_state', 'zhuanwang', 'zhuanwang_state',
                                         'hua_qi', 'hua_qi_state', 'mu_mie', 'mu_mie_state', 'liangqi'))


n = 0
for k in old:
    vo, vn = old[k]['verdict'], new[k]['verdict']
    if vo == 'bad' and vn not in ('good', 'bad', 'CRASH'):
        n += 1
        print(k, 'label=%s' % old[k]['label'])
        print('  OLD v=%s sp=%s' % (vo, sig(old[k])))
        print('  NEW v=%s sp=%s  why=%s' % (vn, sig(new[k]), new[k]['why'][:60]))
print('total', n)
