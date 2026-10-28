# -*- coding: utf-8 -*-
"""核5: 4f 化根判据变化盘全量断语核验（不抽样）. 复用 _pf_probe 判据, 逐盘输出断语全文。"""
import json, glob, sys
sys.path.insert(0, '.')

_ROOT_TAGS = ('BEN', 'ZHONG', 'YU')
_KEI = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

def branch_hidden(branch):
    T = {
        '子': [('癸', 'BEN')], '丑': [('己', 'BEN'), ('癸', 'ZHONG'), ('辛', 'YU')],
        '寅': [('甲', 'BEN'), ('丙', 'ZHONG'), ('戊', 'YU')], '卯': [('乙', 'BEN')],
        '辰': [('戊', 'BEN'), ('乙', 'ZHONG'), ('癸', 'YU')], '巳': [('丙', 'BEN'), ('庚', 'ZHONG'), ('戊', 'YU')],
        '午': [('丁', 'BEN'), ('己', 'ZHONG')], '未': [('己', 'BEN'), ('丁', 'ZHONG'), ('乙', 'YU')],
        '申': [('庚', 'BEN'), ('壬', 'ZHONG'), ('戊', 'YU')], '酉': [('辛', 'BEN')],
        '戌': [('戊', 'BEN'), ('辛', 'ZHONG'), ('丁', 'YU')], '亥': [('壬', 'BEN'), ('甲', 'ZHONG')],
    }
    return T.get(branch, [])

WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
BRANCH_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
             '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
JUS = {'申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金',
       '寅卯辰': '木', '巳午未': '火', '申酉戌': '金', '亥子丑': '水'}

def calc(bazi):
    pillars = bazi.split()
    if len(pillars) != 4:
        return None
    dm = pillars[2][0]
    dm_wx = WX[dm]
    sheng = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    yin_wx = sheng[dm_wx]
    branches = [p[1] for p in pillars]
    ju_wx = None
    for names, wx in JUS.items():
        if set(names) <= set(branches):
            ju_wx = wx
            break
    if not ju_wx:
        return None, None, None
    old_dm = any(BRANCH_WX[br] == dm_wx for br in branches if br in ''.join(JUS))
    old_yin = any(BRANCH_WX[br] == yin_wx for br in branches if br in ''.join(JUS))
    new_dm = any(_KEI.get(ju_wx) == dm_wx for br in branches for gan, tag in branch_hidden(br)
                 if tag in _ROOT_TAGS and _KEI.get(ju_wx) == WX[gan])
    new_yin = any(_KEI.get(ju_wx) == yin_wx for br in branches for gan, tag in branch_hidden(br)
                  if tag in _ROOT_TAGS and _KEI.get(ju_wx) == WX[gan])
    return dm_wx, yin_wx, (old_dm, old_yin, new_dm, new_yin, ju_wx)

diff = []
dm_diff = yin_diff = both = 0
total = 0
for f in glob.glob('p0_v2/case_audit/*_clean.jsonl'):
    for l in open(f, encoding='utf-8'):
        d = json.loads(l)
        r = calc(d.get('bazi', ''))
        if not r or r[2] is None:
            continue
        total += 1
        dm_wx, yin_wx, (od, oy, nd, ny, ju) = r
        if od != nd or oy != ny:
            diff.append((d['case_id'], d.get('bazi', ''), dm_wx, yin_wx, od, oy, nd, ny, ju, d.get('analysis', '')))
            if od != nd:
                dm_diff += 1
            if oy != ny:
                yin_diff += 1
            if (od != nd) and (oy != ny):
                both += 1

print("有合局盘: %d; 4f 化根判据变化盘: %d (日主根变 %d / 印根变 %d / 双变 %d)" % (total, len(diff), dm_diff, yin_diff, both))
for cid, bz, dm, yin, od, oy, nd, ny, ju, ana in diff:
    print("=== %s %s dm=%s印=%s 局=%s 旧(%s,%s)->新(%s,%s)" % (cid, bz, dm, yin, ju, od, oy, nd, ny))
    print("  断语: " + (ana[:220] if ana else "(无)"))
