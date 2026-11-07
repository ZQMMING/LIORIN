# -*- coding: utf-8 -*-
"""验收基线 diff: 旧(901a5040^) vs 新(当前)。分类输出 good->bad / bad->good 等。"""
import json, collections

old = {}
for l in open('_ys_old.jsonl', encoding='utf-8'):
    r = json.loads(l)
    old[r['id']] = r
new = {}
for l in open('_ys_new.jsonl', encoding='utf-8'):
    r = json.loads(l)
    new[r['id']] = r

assert set(old) == set(new), 'id set mismatch'
agree_old = sum(1 for k in old if old[k]['verdict'] in ('good', 'bad') and old[k]['verdict'] == old[k]['label'])
agree_new = sum(1 for k in new if new[k]['verdict'] in ('good', 'bad') and new[k]['verdict'] == new[k]['label'])
pend_old = sum(1 for k in old if old[k]['verdict'] not in ('good', 'bad', 'CRASH'))
pend_new = sum(1 for k in new if new[k]['verdict'] not in ('good', 'bad', 'CRASH'))
print('OLD: agree=%d pend=%d' % (agree_old, pend_old))
print('NEW: agree=%d pend=%d  delta=%d' % (agree_new, pend_new, agree_new - agree_old))

def v(d, k):
    return d[k]['verdict']

# 变化分类
gb = [k for k in old if v(old, k) == 'good' and v(new, k) == 'bad']          # good->bad
bg = [k for k in old if v(old, k) == 'bad' and v(new, k) == 'good']          # bad->good
gp = [k for k in old if v(old, k) == 'good' and v(new, k) not in ('good', 'bad', 'CRASH')]
bp = [k for k in old if v(old, k) == 'bad' and v(new, k) not in ('good', 'bad', 'CRASH')]
pg = [k for k in old if v(old, k) not in ('good', 'bad', 'CRASH') and v(new, k) == 'good']
pb = [k for k in old if v(old, k) not in ('good', 'bad', 'CRASH') and v(new, k) == 'bad']
print('good->bad %d | bad->good %d | good->PENDING %d | bad->PENDING %d | PENDING->good %d | PENDING->bad %d' % (len(gb), len(bg), len(gp), len(bp), len(pg), len(pb)))

print()
print('=== good->bad（label good 一致→bad，真回退）===')
for k in sorted(gb):
    print(' ', k, 'label=%s' % old[k]['label'], '| OLD: %s' % old[k]['why'][:60], '| NEW: %s' % new[k]['why'][:60])
print()
print('=== bad->good（不一致→一致，转对）===')
for k in sorted(bg):
    print(' ', k, 'label=%s' % old[k]['label'], '| OLD: %s' % old[k]['why'][:60], '| NEW: %s' % new[k]['why'][:60])
print()
print('=== good->PENDING 明细（label 分布）===')
gc = collections.Counter(old[k]['label'] for k in gp)
print(' label:', dict(gc), ' total', len(gp))
print('=== bad->PENDING 明细 ===')
bc = collections.Counter(old[k]['label'] for k in bp)
print(' label:', dict(bc), ' total', len(bp))
