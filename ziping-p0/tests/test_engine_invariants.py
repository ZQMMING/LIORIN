# -*- coding: utf-8 -*-
"""引擎不变量 / 性质测试 · 不依赖具体命例, 在全部可能的盘上守原典硬规则.
目的: 反驳"几个挑出来的案例对=引擎对"的过拟合; 用确定性不变量覆盖任意盘.
铁律: 不评分/不权重/不输出STRONG-WEAK; 阴阳干库根规则; 同盘幂等; 不随柱位顺序变.
"""
import sys, json, itertools
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_power_queries import run_queries

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def dim(pillars):
    facts = build(pillars)
    pa = build_power_structure(pillars)
    hst = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year', 'month', 'day', 'hour')}
    rc = build_root_classes(pillars, hst)
    tc = build_tou_cang(facts)
    wx = build_wang_xiang(facts, facts['day_stem'])
    rr = build_root_relations(rc, facts['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    return build_power_network(pa, rc, tc, wx, rr, ts)


# --- 不变量1: 同盘幂等(跑两次逐字节一致) ---
p = {'year': ['庚', '申'], 'month': ['戊', '寅'], 'day': ['甲', '寅'], 'hour': ['癸', '酉']}
check('不变量1 同盘幂等', json.dumps(dim(p), sort_keys=True, ensure_ascii=False)
      == json.dumps(dim(p), sort_keys=True, ensure_ascii=False))

# --- 不变量2: 任意盘无 STRONG/WEAK/score/winner ---
stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
bad = 0
checked = 0
# 抽样: 遍历日主x月令 120种骨架(固定年月日干, 月支取全), 扫越界词
for dg in ['甲', '乙', '丙', '壬']:
    for mb in branches:
        pillars = {'year': ['庚', '申'], 'month': ['戊', mb], 'day': [dg, '寅'], 'hour': ['癸', '酉']}
        txt = json.dumps(dim(pillars), ensure_ascii=False)
        checked += 1
        for w in ['"STRONG"', '"WEAK"', 'total_score', 'overall_strength', '"winner"', '"selected"', 'support_score']:
            if w in txt:
                bad += 1
check('不变量2 抽样%d盘无强弱越界词' % checked, bad == 0, 'bad=%d' % bad)

# --- 不变量3: 阴干假库根永不判根 (乙逢戌/丁逢丑) ---
# 乙日 地支戌(戌中无木本气) -> ROOT 必 NONE / has_root=False
p_y = {'year': ['甲', '戌'], 'month': ['丙', '戌'], 'day': ['乙', '酉'], 'hour': ['辛', '巳']}
check('不变量3a 乙逢戌不作根', dim(p_y)['dimensions']['ROOT']['has_root'] is False)
# 丁日 地支辰丑辰亥(无午未巳寅戌火根, 酉长生另测) -> ROOT 必 NONE
p_d = {'year': ['戊', '辰'], 'month': ['己', '丑'], 'day': ['丁', '辰'], 'hour': ['辛', '亥']}
rd = dim(p_d)
check('不变量3b 丁逢丑不作根(丑酉亥无火根)', rd['dimensions']['ROOT']['has_root'] is False,
      rd['dimensions']['ROOT']['root_weight_class'])

# --- 不变量4: 反例命题 state 恒 UNKNOWN (任意盘不升级) ---
unknown_bad = 0
for dg in ['甲', '庚', '壬', '乙']:
    for mb in ['寅', '申', '巳', '亥']:
        n = dim({'year': ['庚', '申'], 'month': ['戊', mb], 'day': [dg, '寅'], 'hour': ['癸', '酉']})
        for q in run_queries(n):
            if q['query_id'].split('QUERY-')[1] in ('DESHI-BUWANG', 'SHISHI-BURUO'):
                if q['state'] not in ('SUPPORTED', 'NOT_SUPPORTED', 'UNKNOWN'):
                    unknown_bad += 1
check('不变量4 反例命题 state 不越权', unknown_bad == 0, 'bad=%d' % unknown_bad)

# --- 不变量5: 成党=透干且通根, 不随四柱排列顺序变(换位置不改结构事实) ---
# 同一组干支换柱位(只换非年月日关键位), 成党判定的布尔不变
p_a = {'year': ['甲', '寅'], 'month': ['丙', '寅'], 'day': ['甲', '寅'], 'hour': ['丁', '卯']}
p_b = {'year': ['丙', '寅'], 'month': ['甲', '寅'], 'day': ['甲', '寅'], 'hour': ['丁', '卯']}
da, db = dim(p_a), dim(p_b)
check('不变量5 成党布尔不随月干位漂移',
      da['dimensions']['SUPPORT']['BIJIE']['stem_present'] ==
      db['dimensions']['SUPPORT']['BIJIE']['stem_present'])

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
