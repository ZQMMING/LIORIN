# -*- coding: utf-8 -*-
"""P160 用神两刀 namespace 收口对齐 · 只读校验 Golden
断言: 两刀输出挂对 namespace门牌, 不碰对方 forbidden, 不串领域, 无裁决词。
对齐 namespace_registry PATCH-023C: PZZQ.use_god(pattern) / QTBJ.climate_use(climate)。
"""
import sys, json, copy
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.yongshen_geju import build_yongshen_geju
from engines.common.qtbj_climate_candidates import build_climate_candidates

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def mk(mg):
    return {'year': ['己', '巳'], 'month': list(mg), 'day': ['甲', '寅'], 'hour': ['丙', '寅']}


# 同一命盘: 甲日辰月 -> PZZQ 格神(偏财) + QTBJ 调候(先庚后壬)
facts = build(mk('戊辰'))
gz = build_yongshen_geju(facts)
qt = build_climate_candidates(facts)

# G1 namespace 门牌挂对
check('PZZQ 输出 namespace=PZZQ.use_god', gz.get('namespace') == 'PZZQ.use_god')
check('PZZQ 输出 namespace_type=pattern', gz.get('namespace_type') == 'pattern')
check('QTBJ 输出 namespace=QTBJ.climate_use', qt.get('namespace') == 'QTBJ.climate_use')
check('QTBJ 输出 namespace_type=climate', qt.get('namespace_type') == 'climate')

# G2 两刀不串领域: 各自不该出现对方的结构键
check('PZZQ 视图无 climate_candidates 键', 'climate_candidates' not in gz)
check('QTBJ 视图无 ge_shen_candidates 键', 'ge_shen_candidates' not in qt)
check('QTBJ 视图无 shun_ni_yong 字段', 'shun_ni_yong' not in json.dumps(qt, ensure_ascii=False))
check('PZZQ 视图无调候 order 字段', not any('order' in c for c in gz['ge_shen_candidates']))

# G3 判定字段(剔除 boundary_note)不碰 forbidden: strength/wang/qiang/强弱/评分
def strip_note(r):
    b = copy.deepcopy(r)
    b.pop('boundary_note', None)
    return json.dumps(b, ensure_ascii=False)


gz_text = strip_note(gz)
qt_text = strip_note(qt)
forbidden = ['strength_state', 'wang_state', 'qiang_state', 'STRONG', 'WEAK',
             '身强', '身弱', '旺衰', 'score', 'weight', 'threshold']
for bad in forbidden:
    check('PZZQ 判定字段不含 %s' % bad, bad not in gz_text)
    check('QTBJ 判定字段不含 %s' % bad, bad not in qt_text)

# G4 两刀均无裁决词(不 selected/winner/final/use)
for k in ['selected', 'winner', 'best', 'final', 'use', 'use_god_final']:
    check('PZZQ 无裁决字段 %s' % k, gz.get(k, 'ABSENT') == 'ABSENT')
    check('QTBJ 无裁决字段 %s' % k, qt.get(k, 'ABSENT') == 'ABSENT')

# G5 两刀各自仍是 CANDIDATE_ONLY, 未越界成 JUDGMENT
check('PZZQ judgment=CANDIDATE_ONLY', gz['judgment_status'] == 'GEJU_CANDIDATE_ONLY')
check('QTBJ judgment=CANDIDATE_ONLY', qt['judgment_status'] == 'CLIMATE_CANDIDATE_ONLY')

# G6 未注册调候条也仍挂对 namespace、不越界
qt_no = build_climate_candidates(build(mk('丁卯')))
check('未注册仍挂 QTBJ namespace', qt_no.get('namespace') == 'QTBJ.climate_use')
check('未注册不碰 forbidden', all(b not in strip_note(qt_no) for b in ['STRONG', 'WEAK', 'score']))

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
