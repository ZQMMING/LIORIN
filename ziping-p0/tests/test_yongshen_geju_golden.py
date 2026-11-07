# -*- coding: utf-8 -*-
"""P160 PZZQ 格局用神结构视图 · 第一刀 Golden
边界: 只读投影/候选枚举; 顺逆用仅分类; 多候选并列不裁; 相神/有情有力/成格/吉凶/扶抑/身强弱全禁。
"""
import sys, json, copy
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.yongshen_geju import build_yongshen_geju

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


# 盘: (说明, pillars)
def mk(yg, mg, dg, hg):
    return {'year': list(yg), 'month': list(mg), 'day': list(dg), 'hour': list(hg)}


# G1/G2 顺逆用分类覆盖
p_sha = mk('甲子', '辛酉', '乙卯', '丁亥')      # 乙酉透辛 -> 七杀(逆用)
p_duo = mk('甲子', '甲寅', '甲寅', '丙寅')      # 甲日寅月透甲丙 -> 建禄(逆)+食神(顺) 并列
p_benqi = mk('壬子', '丁酉', '甲寅', '丙寅')    # 甲酉月丁不透辛 -> 正官(顺, 本气)
p_shang = mk('甲子', '丙午', '甲X'.replace('X', '寅'), '丙寅')  # 甲午月丁 -> 伤官(逆)
p_yin = mk('甲子', '壬申', '甲寅', '丙寅')      # 甲日申月透壬 -> 壬=偏印(顺)
p_cai = mk('甲子', '戊辰', '甲寅', '丙寅')      # 甲辰月戊 -> 偏财(顺)

r_sha = build_yongshen_geju(build(p_sha))
r_duo = build_yongshen_geju(build(p_duo))
r_benqi = build_yongshen_geju(build(p_benqi))
r_shang = build_yongshen_geju(build(p_shang))
r_yin = build_yongshen_geju(build(p_yin))
r_cai = build_yongshen_geju(build(p_cai))


def only(r, tg):
    return [c for c in r['ge_shen_candidates'] if c['ten_god'] == tg]


# G2 逆用
check('七杀->NI_YONG', only(r_sha, '七杀')[0]['shun_ni_yong'] == 'NI_YONG')
check('伤官->NI_YONG', only(r_shang, '伤官')[0]['shun_ni_yong'] == 'NI_YONG')
check('比肩/建禄->NI_YONG', only(r_duo, '比肩')[0]['shun_ni_yong'] == 'NI_YONG')
# G1 顺用
check('正官->SHUN_YONG', only(r_benqi, '正官')[0]['shun_ni_yong'] == 'SHUN_YONG')
check('偏印->SHUN_YONG', only(r_yin, '偏印')[0]['shun_ni_yong'] == 'SHUN_YONG')
check('偏财->SHUN_YONG', only(r_cai, '偏财')[0]['shun_ni_yong'] == 'SHUN_YONG')
check('食神->SHUN_YONG', only(r_duo, '食神')[0]['shun_ni_yong'] == 'SHUN_YONG')

# G3 多候选并列(用神变化): 甲日寅月透甲+丙 -> 建禄 + 食神 两候选
check('多透并列>=2候选', r_duo['candidate_count'] >= 2, str(r_duo['candidate_count']))
check('多候选未选(无selected/winner键)', 'selected' not in r_duo and 'winner' not in r_duo)

# G4 不透取本气, 月令本气候选存在, source=BENQI (非月令透干候选可并列)
check('不透含本气候选', r_benqi['candidate_count'] >= 1)
_benqi_cand = [c for c in r_benqi['ge_shen_candidates'] if c.get('candidate_source') == 'BENQI']
check('本气来源BENQI存在', len(_benqi_cand) >= 1 and _benqi_cand[0]['ten_god'] == '正官')
check('透干来源TRANSPARENT', r_sha['ge_shen_candidates'][0]['candidate_source'] == 'TRANSPARENT_STEM')

# G5 并列不裁: 无 selected/winner/best/primary/final
for k in ['selected', 'winner', 'best', 'primary', 'final']:
    check('无裁决字段 %s' % k, r_duo.get(k, 'ABSENT') in (None, 'ABSENT'))

# G6 provenance: evidence_refs + source/trigger fact ids + boundary_note
c0 = r_duo['ge_shen_candidates'][0]
check('候选含PZZQ evidence', 'PZZQ-005-007' in c0['evidence_refs'] and 'PZZQ-005-009' in c0['evidence_refs'])
check('候选有source_fact_ids', isinstance(c0['source_fact_ids'], list) and len(c0['source_fact_ids']) > 0)
check('候选有trigger_fact_ids', isinstance(c0['trigger_fact_ids'], list) and len(c0['trigger_fact_ids']) > 0)
check('顶层boundary_note非空', isinstance(r_duo['boundary_note'], str) and len(r_duo['boundary_note']) > 10)

# G8 同源视图: ge_shen_candidates 与 use_god_candidates 同列表
check('格神视图==用神变化候选(同源)', r_duo['ge_shen_candidates'] is r_duo['use_god_candidates'])

# G9 稳定 ID: 同盘重跑一致
r_duo2 = build_yongshen_geju(build(p_duo))
ids1 = [c['candidate_id'] for c in r_duo['ge_shen_candidates']]
ids2 = [c['candidate_id'] for c in r_duo2['ge_shen_candidates']]
check('candidate_id稳定可diff', ids1 == ids2 and all(i.startswith('GE-') for i in ids1))

# G10 judgment_status
check('judgment_status=CANDIDATE_ONLY', r_duo['judgment_status'] == 'GEJU_CANDIDATE_ONLY')

# G7 硬禁区: 剔除 boundary_note 后, 判定字段不得含禁用词
blob = copy.deepcopy(r_duo)
blob.pop('boundary_note', None)
text = json.dumps(blob, ensure_ascii=False)
banned = ['STRONG', 'WEAK', '身强', '身弱', '扶抑', '喜神', '忌神', '有情', '无情',
          '有力', '无力', '格局高低', '成格', '败格', '贵贱', '吉凶', '相神',
          '最终用神', 'score', 'weight', 'threshold', 'winner', 'selected_use_god']
for bad in banned:
    check('禁区词不出现: %s' % bad, bad not in text)

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
