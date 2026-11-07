# -*- coding: utf-8 -*-
"""P160 QTBJ 调候干盘中存在性投影 · 第五刀 Golden
边界: 只读对照调候应取干×盘中位置(透干/藏支/全无); 不判得力/成败/吉凶; 并列不裁; 不接生产。
"""
import sys, json, copy
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.qtbj_climate_presence import build_climate_presence

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def pillars(mb, day_gz, hour_gz, year_gz=('己', '巳')):
    return {'year': list(year_gz), 'month': ['戊', mb], 'day': list(day_gz), 'hour': list(hour_gz)}


def by_stem(r):
    return {c['stem']: c for c in r['climate_presence_candidates']}


# 盘A: 甲日寅月调候[丙,癸]; 时柱丙寅 => 丙透干, 癸全无
rA = build_climate_presence(build(pillars('寅', ('甲', '寅'), ('丙', '寅'))))
m = by_stem(rA)
check('盘A module', rA['module'] == 'QTBJ_CLIMATE_PRESENCE')
check('盘A 丙=TRANSPARENT', m['丙']['present_status'] == 'TRANSPARENT', str(m['丙']))
check('盘A 丙透干柱含hour', 'hour' in m['丙']['transparent_pillars'], str(m['丙']['transparent_pillars']))
check('盘A 癸=ABSENT', m['癸']['present_status'] == 'ABSENT', str(m['癸']))
check('盘A 并列保持原序', [c['stem'] for c in rA['climate_presence_candidates']] == ['丙', '癸'])
check('盘A state=CANDIDATE_ONLY', rA['judgment_status'] == 'CLIMATE_PRESENCE_ONLY')
check('盘A namespace=QTBJ.climate_use', rA['namespace'] == 'QTBJ.climate_use')

# 盘B: 同时柱癸酉 => 癸透干; 丙仅藏于巳/寅 => HIDDEN
rB = build_climate_presence(build(pillars('寅', ('甲', '寅'), ('癸', '酉'))))
mB = by_stem(rB)
check('盘B 癸=TRANSPARENT', mB['癸']['present_status'] == 'TRANSPARENT', str(mB['癸']))
check('盘B 丙=HIDDEN', mB['丙']['present_status'] == 'HIDDEN', str(mB['丙']))
check('盘B 丙藏柱含month', 'month' in mB['丙']['hidden_pillars'], str(mB['丙']['hidden_pillars']))

# 盘C: 调候干皆藏支(无透干) => HIDDEN
# 戊日午月调候[壬,甲]; 造天干不见壬甲、藏干见甲(午藏丁己) 调整: 用甲藏、壬藏
rC = build_climate_presence(build(pillars('午', ('戊', '午'), ('丙', '辰'))))
mC = by_stem(rC)
check('盘C 候选数=2', rC['candidate_count'] == 2, str(rC['candidate_count']))
check('盘C 壬非TRANSPARENT', mC['壬']['present_status'] != 'TRANSPARENT', str(mC['壬']['present_status']))

# 不越权: 无裁决字段
for k in ['selected', 'winner', 'best', 'final', 'use', 'use_stem', 'effective', 'power']:
    check('无裁决字段 %s' % k, rA.get(k, 'ABSENT') == 'ABSENT')

# 硬禁区(剔除boundary_note): 不得含成败/吉凶/得力/评分
blob = copy.deepcopy(rA)
blob.pop('boundary_note', None)
text = json.dumps(blob, ensure_ascii=False)
banned = ['得力', '无力', '无效', '调候成', '调候败', '富贵', '吉凶', 'score',
          'weight', 'threshold', 'winner', 'selected', '寒甚', '凶']
for bad in banned:
    check('禁区词不出现: %s' % bad, bad not in text)

# 全表健康: 十干×十二月 120 键均可跑不抛错, 状态非异常
TEN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRS = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
err = 0
for dm in TEN:
    for mb in BRS:
        rr = build_climate_presence(build(pillars(mb, (dm, '寅'), ('丙', '寅'))))
        if rr.get('base_state') != 'REGISTERED':
            err += 1
check('全表120键REGISTERED', err == 0, 'err=%d' % err)

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
