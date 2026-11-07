# -*- coding: utf-8 -*-
"""补: good->bad 中 special判定同12盘的 label 分布; GP 判定异5盘 label。"""
import json, collections
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


def cat(k):
    vo, vn = old[k]['verdict'], new[k]['verdict']
    if vo in ('good', 'bad') and vn in ('good', 'bad'):
        return 'GB' if vo == 'good' else ('BG' if vn == 'good' else 'SAME')
    if vo in ('good', 'bad'):
        return 'GP' if vo == 'good' else 'BP'
    return 'OTHER'

gb_same = [k for k in old if cat(k) == 'GB' and sig(old[k]) == sig(new[k])]
gb_diff = [k for k in old if cat(k) == 'GB' and sig(old[k]) != sig(new[k])]
print('GB同12 label:', dict(collections.Counter(old[k]['label'] for k in gb_same)))
print('GB异28 label:', dict(collections.Counter(old[k]['label'] for k in gb_diff)))
print('GB同12 明细:')
for k in sorted(gb_same):
    print(' ', k, 'label=%s' % old[k]['label'], '| OLD sp=%s %s' % (sig(old[k]), old[k]['why'][:30]),
          '| NEW %s' % new[k]['why'][:45])
gp_diff = [k for k in old if cat(k) == 'GP' and sig(old[k]) != sig(new[k])]
print('GP判定异5 label:', dict(collections.Counter(old[k]['label'] for k in gp_diff)))
for k in sorted(gp_diff):
    print(' ', k, 'label=%s' % old[k]['label'], '| OLD sp=%s %s' % (sig(old[k]), old[k]['why'][:30]),
          '| NEW sp=%s %s' % (sig(new[k]), new[k]['why'][:40]))
