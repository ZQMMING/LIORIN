# -*- coding: utf-8 -*-
"""验收基线 diff v2: 旧(901a5040^ 纯版) vs 新(当前)。special 判定分层: 公式 vs 引擎判定。"""
import json, collections

old = {}
for l in open('_ys_old.jsonl', encoding='utf-8'):
    r = json.loads(l)
    old[r['id']] = r
new = {}
for l in open('_ys_new.jsonl', encoding='utf-8'):
    r = json.loads(l)
    new[r['id']] = r

agree_old = sum(1 for k in old if old[k]['verdict'] in ('good', 'bad') and old[k]['verdict'] == old[k]['label'])
agree_new = sum(1 for k in new if new[k]['verdict'] in ('good', 'bad') and new[k]['verdict'] == new[k]['label'])
print('OLD: agree=%d (%.1f%%)  NEW: agree=%d (%.1f%%)  delta=%d' % (
    agree_old, 100 * agree_old / 1459, agree_new, 100 * agree_new / 1459, agree_new - agree_old))


def spsig(r):
    s = r.get('sp') or {}
    return (s.get('cong_type'), s.get('cong_state'), s.get('zhuanwang'), s.get('zhuanwang_state'),
            s.get('hua_qi'), s.get('hua_qi_state'), s.get('mu_mie'), s.get('mu_mie_state'), bool(s.get('liangqi')))


def cat(k):
    vo, vn = old[k]['verdict'], new[k]['verdict']
    if vo in ('good', 'bad') and vn in ('good', 'bad'):
        if vo != vn:
            return 'GB' if vo == 'good' else 'BG'
        return 'SAME'
    if vo in ('good', 'bad') and vn not in ('good', 'bad', 'CRASH'):
        return 'GP' if vo == 'good' else 'BP'
    return 'OTHER'

cnt = collections.Counter(cat(k) for k in old)
print('类别: good->bad=%d bad->good=%d good->PENDING=%d bad->PENDING=%d 其余=%d' % (
    cnt['GB'], cnt['BG'], cnt['GP'], cnt['BP'], cnt['OTHER']))

# GB 盘: special 判定同/异 -> 公式 vs 判定
gb_same = [k for k in old if cat(k) == 'GB' and spsig(old[k]) == spsig(new[k])]
gb_diff = [k for k in old if cat(k) == 'GB' and spsig(old[k]) != spsig(new[k])]
print()
print('good->bad %d 盘: special判定同=%d(纯公式变化) special判定异=%d(引擎判定变化)' % (cnt['GB'], len(gb_same), len(gb_diff)))
for k in sorted(gb_diff):
    o, n = old[k], new[k]
    print('  [判定异]', k, 'label=%s' % o['label'], '| OLD sp=%s verdict=%s' % (spsig(o), o['verdict']),
          '| NEW sp=%s verdict=%s' % (spsig(n), n['verdict']))
print()
print('--- good->bad 全盘: label 分布 ---')
lbl = collections.Counter(old[k]['label'] for k in old if cat(k) == 'GB')
print('  label:', dict(lbl))
print('  label-good(一致损失):', sorted(k for k in old if cat(k) == 'GB' and old[k]['label'] == 'good'))
print('  label-bad(转对):', sorted(k for k in old if cat(k) == 'GB' and old[k]['label'] == 'bad'))

# BP( bad->PENDING ): special 判定异同
bp_same = [k for k in old if cat(k) == 'BP' and spsig(old[k]) == spsig(new[k])]
bp_diff = [k for k in old if cat(k) == 'BP' and spsig(old[k]) != spsig(new[k])]
print()
print('bad->PENDING %d 盘: special判定同=%d special判定异=%d' % (cnt['BP'], len(bp_same), len(bp_diff)))
for k in sorted(bp_diff)[:25]:
    o, n = old[k], new[k]
    print('  [判定异]', k, 'label=%s' % o['label'], '| OLD sp=%s' % spsig(o), '| NEW sp=%s verdict=%s' % (spsig(n), n['verdict']))
print()
print('--- bad->PENDING label 分布 ---', dict(collections.Counter(old[k]['label'] for k in old if cat(k) == 'BP')))
print('--- good->PENDING label 分布 ---', dict(collections.Counter(old[k]['label'] for k in old if cat(k) == 'GP')))

# GP 盘: special 判定异同
gp_same = [k for k in old if cat(k) == 'GP' and spsig(old[k]) == spsig(new[k])]
gp_diff = [k for k in old if cat(k) == 'GP' and spsig(old[k]) != spsig(new[k])]
print('good->PENDING %d 盘: special判定同=%d(纯公式) special判定异=%d' % (cnt['GP'], len(gp_same), len(gp_diff)))
