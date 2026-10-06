# -*- coding: utf-8 -*-
"""补2 PATCH-4f 影响面: 全量对比"旧化根判据(BRANCH_WX本气)" vs "新判据(藏干任意tag+化神克)" 的化根事件差异盘。"""
import json, glob, collections
import sys
sys.path.insert(0, '.')

_ROOT_TAGS = ('BEN', 'ZHONG', 'YU')
_KEI = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

def branch_hidden(branch):
    """藏干表: 支 -> [(干, tag)]"""
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

# 局支 -> 化神 (三合/三会)
JUS = {'申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金',
       '寅卯辰': '木', '巳午未': '火', '申酉戌': '金', '亥子丑': '水'}

def calc(bazi):
    pillars = bazi.split()
    if len(pillars) != 4:
        return None
    dm = pillars[2][0]
    dm_wx = WX[dm]
    # 印 = 生日主
    sheng = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    yin_wx = sheng[dm_wx]
    branches = [p[1] for p in pillars]
    # 找三合/三会局
    ju_wx = None
    for names, wx in JUS.items():
        if set(names) <= set(branches):
            ju_wx = wx
            break
    if not ju_wx:
        return None, None, None
    # 旧判据(4f前): 局支 BRANCH_WX 本气 == 某五行 -> 该五行本气根被化
    # 新判据(4f后): 局支藏干含该五行(任意tag) 且 _KEI[化神]==该五行 -> 该五行根被化
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
        bz = d.get('bazi', '')
        r = calc(bz)
        if not r or r[2] is None:
            continue
        total += 1
        dm_wx, yin_wx, (od, oy, nd, ny, ju) = r
        if od != nd or oy != ny:
            diff.append((d['case_id'], bz, dm_wx, yin_wx, od, oy, nd, ny, ju))
            if od != nd: dm_diff += 1
            if oy != ny: yin_diff += 1
            if (od != nd) and (oy != ny): both += 1

print("有合局盘: %d; 4f 化根判据变化盘: %d (日主根变 %d / 印根变 %d / 双变 %d)" % (total, len(diff), dm_diff, yin_diff, both))
for cid, bz, dm, yin, od, oy, nd, ny, ju in diff:
    print("  %s %s dm=%s印=%s 局=%s 旧日主化%s印化%s -> 新日主化%s印化%s" % (cid, bz, dm, yin, ju, od, oy, nd, ny))
