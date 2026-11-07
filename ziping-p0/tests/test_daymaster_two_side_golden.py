# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, '.')
from engines.common import l0_fact_builder as l0
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side, DAYMASTER_SIDE, OPPOSING_SIDE

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


P = {'year': ['甲', '申'], 'month': ['丙', '寅'], 'day': ['甲', '辰'], 'hour': ['丙', '子']}
facts = l0.build(P)
rc = build_root_classes(P, l0.HIDDEN)
tc = build_tou_cang(facts)
rr = build_root_relations(rc, facts['combination_facts'])
ts = build_two_side(rc, tc, rr)

dm_members = {m['member']: m for m in ts['sides'][DAYMASTER_SIDE]['members']}
op_members = {m['member']: m for m in ts['sides'][OPPOSING_SIDE]['members']}

# 1. 阵营归属
check('比劫归日主端', 'BIJIE' in dm_members and 'YIN' in dm_members)
check('食伤财官杀归反方', all(x in op_members for x in ['SHISHANG', 'CAI', 'GUANSHA']))
check('日主端无反方成员', not any(x in dm_members for x in ['SHISHANG', 'CAI', 'GUANSHA']))

# 2. present 布尔(真实盘)
check('比劫 present(甲透+寅藏)', dm_members['BIJIE']['present'] is True)
check('比劫透藏BOTH', dm_members['BIJIE']['tou_cang_state'] == 'TOU_CANG_BOTH')
check('印 present(水藏支)', dm_members['YIN']['present'] is True)
check('印藏而不透CANG_ONLY', dm_members['YIN']['tou_cang_state'] == 'CANG_ONLY')
check('食伤 present(丙透)', op_members['SHISHANG']['present'] is True)
check('官杀 present(申藏庚)', op_members['GUANSHA']['present'] is True)

# 3. root block
root = ts['sides'][DAYMASTER_SIDE]['root']
check('根 present(寅禄辰余气)', root['present'] is True)
check('根柱位含月日时(甲子特例TONG_GEN.001: 子亦为印根轻根)', set(root['root_pillars']) == {'month', 'day', 'hour'})
check('struck 根(寅被申冲)', root['struck_root_pillars'] == ['month'])
check('combined 根(辰入三合; 甲子特例下子亦入申子辰三合/半合)', root['combined_root_pillars'] == ['day', 'hour'])

# 4. 边界: 无众寡/成势/胜负/去取/计数/STRONG/WEAK
blob = json.dumps(ts, ensure_ascii=False)
# 判定字段(排除 boundary_note 自我说明)
judge = json.dumps({'sides': ts['sides'], 'judgment_status': ts['judgment_status']}, ensure_ascii=False)
for bad in ['众', '寡', '成势', '得势', '胜负', 'STRONG', 'WEAK', 'count', 'score', 'winner', 'dominant']:
    ok = bad not in judge
    if not ok:
        fails += 1
    check('判定字段禁用词缺席:' + bad, ok)

# 5. 空盘安全(无十神)
empty_tc = {'groups': {g: {'tou': False, 'cang': False, 'state': 'ABSENT',
                           'stem_pillars': [], 'hidden_pillars': []}
                       for g in ['BIJIE', 'YIN', 'SHISHANG', 'CAI', 'GUANSHA']}}
empty_rc = {'has_root': False, 'root_pillars': [], 'per_pillar': {}}
ts2 = build_two_side(empty_rc, empty_tc, None)
check('空盘成员均 not present',
      all(m['present'] is False for side in ts2['sides'].values() for m in side['members'])
      and ts2['sides'][DAYMASTER_SIDE]['root']['present'] is False)

print()
print('FAILS', fails)
sys.exit(1 if fails else 0)
