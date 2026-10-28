# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, '.')
from engines.common.daymaster_root_relations import build_root_relations

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def mock_rc(pillars):
    return {'per_pillar': {p: {'branch': b, 'root_class': rc} for p, (b, rc) in pillars.items()}}


# 1. 根支逢冲: 甲禄在寅(月根), 申寅冲; 年支申非根不记
rc = mock_rc({'month': ('寅', 'HEAVY_LU'), 'day': ('辰', 'NONE'),
              'year': ('申', 'NONE'), 'hour': ('子', 'NONE')})
comb = {'liuchong': [['申', '寅']]}
r = build_root_relations(rc, comb)
mr = r['root_branch_relations']['month']['relations']
check('根支寅逢冲->CLASH', len(mr) == 1 and mr[0]['relation'] == 'CLASH' and mr[0]['with_branches'] == ['申'])
check('冲归入struck', 'month' in r['struck_root_pillars'])
check('非根支申不记录关系', r['root_branch_relations']['year']['relations'] == [])

# 2. 根支逢三合(合会组, 非struck)
rc2 = mock_rc({'day': ('辰', 'LIGHT_YU_QI'), 'month': ('寅', 'NONE'),
               'year': ('申', 'NONE'), 'hour': ('子', 'NONE')})
comb2 = {'sanhe': ['申子辰合水']}
r2 = build_root_relations(rc2, comb2)
dr = r2['root_branch_relations']['day']['relations']
check('根支辰逢三合->TRIPLE_COMBINE', len(dr) == 1 and dr[0]['relation'] == 'TRIPLE_COMBINE'
      and set(dr[0]['with_branches']) == {'申', '子'})
check('三合归入combined', 'day' in r2['combined_root_pillars'])
check('三合不入struck', 'day' not in r2['struck_root_pillars'])

# 3. 根支逢六害(字符串形态)
rc3 = mock_rc({'month': ('寅', 'HEAVY_LU')})
r3 = build_root_relations(rc3, {'liuhai': ['寅巳相害']})
rel3 = r3['root_branch_relations']['month']['relations']
check('根支寅逢害->HARM', len(rel3) == 1 and rel3[0]['relation'] == 'HARM' and rel3[0]['with_branches'] == ['巳'])

# 4. 根支逢破(字符串)
rc4 = mock_rc({'day': ('辰', 'LIGHT_YU_QI')})
r4 = build_root_relations(rc4, {'liupo': ['丑辰相破']})
rel4 = r4['root_branch_relations']['day']['relations']
check('根支辰逢破->BREAK', len(rel4) == 1 and rel4[0]['relation'] == 'BREAK')

# 5. 根支自刑(对象形态)
rc5 = mock_rc({'day': ('辰', 'LIGHT_YU_QI'), 'hour': ('辰', 'LIGHT_YU_QI')})
r5 = build_root_relations(rc5, {'self_punishment': [{'branch': '辰', 'positions': ['day', 'hour']}]})
check('日根辰自刑', any(x['relation'] == 'SELF_PUNISH' for x in r5['root_branch_relations']['day']['relations']))

# 6. 根支逢六合
rc6 = mock_rc({'hour': ('丑', 'LIGHT_YU_QI')})
r6 = build_root_relations(rc6, {'liuhe': [['子', '丑']]})
rel6 = r6['root_branch_relations']['hour']['relations']
check('根支丑逢六合->SIX_COMBINE', len(rel6) == 1 and rel6[0]['relation'] == 'SIX_COMBINE')

# 7. 根支逢三刑
rc7 = mock_rc({'month': ('寅', 'HEAVY_LU')})
r7 = build_root_relations(rc7, {'sanxing': ['寅巳申三刑']})
rel7 = r7['root_branch_relations']['month']['relations']
check('根支寅逢三刑->TRIPLE_PUNISH', len(rel7) == 1 and rel7[0]['relation'] == 'TRIPLE_PUNISH'
      and set(rel7[0]['with_branches']) == {'巳', '申'})

# 8. 无根支不参与
rc8 = mock_rc({'month': ('午', 'NONE')})
r8 = build_root_relations(rc8, {'liuchong': [['子', '午']]})
check('无根支午不挂关系', r8['root_branch_relations']['month']['relations'] == [])

# 9. 边界: 判定字段无 根拔/失效/增强/STRONG/WEAK/score
judge = json.dumps(r['root_branch_relations'], ensure_ascii=False)
for bad in ['根拔', '拔', '失效', '增强', '化神', 'STRONG', 'WEAK', 'score']:
    ok = bad not in judge
    if not ok:
        fails += 1
    check('判定字段禁用词缺席:' + bad, ok)

print()
print('FAILS', fails)
sys.exit(1 if fails else 0)
