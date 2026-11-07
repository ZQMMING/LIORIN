# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from engines.common.daymaster_tou_cang import (
    build_tou_cang, TOU_CANG_BOTH, TOU_ONLY, CANG_ONLY, ABSENT)


def mem(tg, mtype, pillar='year', branch='子', qi=None):
    return {'pillar': pillar, 'type': mtype, 'stem': 'X', 'branch': branch,
            'hidden_index': 0 if mtype == 'hidden' else None,
            'qi_position': qi, 'ten_god': tg}


def state_of(tc, group):
    return tc['groups'][group]['state']


fails = 0


def check(name, got, expect):
    global fails
    ok = got == expect
    if not ok:
        fails += 1
    print(('PASS' if ok else 'FAIL'), name, '->', got, '' if ok else '(期望' + expect + ')')


# 1. 透藏俱备: 正官既透天干又藏支
f1 = {'ten_god_members': [mem('正官', 'stem', 'year'), mem('正官', 'hidden', 'month', '卯', '本气')]}
check('透藏俱备 BOTH', state_of(build_tou_cang(f1), 'GUANSHA'), TOU_CANG_BOTH)

# 2. 只透不藏: 正财透天干, 支中无财
f2 = {'ten_god_members': [mem('正财', 'stem', 'hour')]}
check('只透不藏 TOU_ONLY', state_of(build_tou_cang(f2), 'CAI'), TOU_ONLY)

# 3. 只藏不透: 偏印藏支, 天干无印
f3 = {'ten_god_members': [mem('偏印', 'hidden', 'hour', '寅', '中气')]}
check('只藏不透 CANG_ONLY', state_of(build_tou_cang(f3), 'YIN'), CANG_ONLY)

# 4. 俱不现
f4 = {'ten_god_members': [mem('比肩', 'stem', 'month')]}
check('食伤俱不现 ABSENT', state_of(build_tou_cang(f4), 'SHISHANG'), ABSENT)

# 5. 大类合并: 食神藏 + 伤官透 -> SHISHANG 透藏俱备
f5 = {'ten_god_members': [mem('伤官', 'stem', 'year'), mem('食神', 'hidden', 'day', '巳', '本气')]}
check('正偏合并 BOTH', state_of(build_tou_cang(f5), 'SHISHANG'), TOU_CANG_BOTH)

# 6. 边界: 判定字段(groups)不出现有力/无力/虚浮/旺衰/STRONG/WEAK
#    boundary_note 为自我说明文本("不判X"), 不纳入判定字段检查
import json
tc1 = build_tou_cang(f1)
judge_blob = json.dumps(tc1['groups'], ensure_ascii=False)
for bad in ['有力', '无力', '虚浮', '旺', '衰', 'STRONG', 'WEAK', 'score', 'weight']:
    ok = bad not in judge_blob
    if not ok:
        fails += 1
    print(('PASS' if ok else 'FAIL'), '判定字段禁用词缺席:', bad)

# state 取值只能是四态
allowed = {TOU_CANG_BOTH, TOU_ONLY, CANG_ONLY, ABSENT}
states_ok = all(g['state'] in allowed for g in tc1['groups'].values())
if not states_ok:
    fails += 1
print(('PASS' if states_ok else 'FAIL'), 'state 仅四态')

print()
print('FAILS', fails)
sys.exit(1 if fails else 0)
