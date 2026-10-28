# -*- coding: utf-8 -*-
"""P160 相神静态配对候选 · 第四刀 Golden
边界: 只枚举格神→相神角色配对+存在性; 不判成相/破相/有情/成格/格局高低。
"""
import sys, json, copy
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.xiang_shen_candidates import build_xiang_shen_candidates

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def strip_notes(o):
    if isinstance(o, dict):
        return {k: strip_notes(v) for k, v in o.items() if k not in ('boundary_note', 'note', 'explanation')}
    if isinstance(o, list):
        return [strip_notes(x) for x in o]
    return o


p = {'year': ['己', '巳'], 'month': ['戊', '辰'], 'day': ['甲', '寅'], 'hour': ['丙', '寅']}
r = build_xiang_shen_candidates(build(p))

# G1 输出结构
check('含相神候选列表', 'xiang_shen_candidates' in r)
check('候选数>0', r['candidate_count'] > 0, 'n=%d' % r['candidate_count'])
check('namespace=PZZQ.use_god', r['namespace'] == 'PZZQ.use_god')
check('judgment=XIANG_ROLE_CANDIDATE_ONLY', r['judgment_status'] == 'XIANG_ROLE_CANDIDATE_ONLY')

# G2 配对正确: 偏财格 -> 食神/伤官/正官
roles = sorted(c['xiang_role'] for c in r['xiang_shen_candidates'])
check('偏财格配对=食神/伤官/正官', roles == ['伤官', '正官', '食神'], str(roles))

# G3 存在性: 本盘丙火透干 -> 食神 stem_present=True; 伤官/正官 absent
shishen = [c for c in r['xiang_shen_candidates'] if c['xiang_role'] == '食神'][0]
shang = [c for c in r['xiang_shen_candidates'] if c['xiang_role'] == '伤官'][0]
check('食神透干存在', shishen['stem_present'] is True and shishen['present_in_chart'] is True)
check('伤官不在盘', shang['present_in_chart'] is False)

# G4 evidence 绑定
check('evidence含PZZQ-007-004', 'PZZQ-007-004' in r['evidence_refs'])
check('evidence含PZZQ-005-007', 'PZZQ-005-007' in r['evidence_refs'])

# G5 不选唯一相神
for k in ['selected', 'winner', 'best', 'primary_xiang', 'final_xiang']:
    check('无裁决字段 %s' % k, r.get(k, 'ABSENT') == 'ABSENT')

# G6 不越界: 剔除说明文本后无成格/破格/有情有力
text = json.dumps(strip_notes(r), ensure_ascii=False)
for bad in ['已成格', '破格', '败格', '有情', '无情', '有力', '无力', '身强', '身弱']:
    check('不含越界词: %s' % bad, bad not in text)

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
