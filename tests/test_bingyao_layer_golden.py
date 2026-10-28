# -*- coding: utf-8 -*-
"""病药子层 Golden 测试."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.common.l0_fact_builder import build
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_power_queries import run_queries
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.wuxing_power import build_wuxing_power
from engines.common.ge_jie_layer import build_ge_cheng


def build_full(pillars):
    facts = build(pillars)
    facts['pillars'] = pillars
    try:
        facts['wuxing_power'] = build_wuxing_power(pillars, facts)
    except Exception:
        facts['wuxing_power'] = {}
    try:
        build_ge_cheng(facts)
    except Exception:
        facts['ge_cheng'] = None
    hst = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year','month','day','hour')}
    pa = build_power_structure(pillars)
    rc = build_root_classes(pillars, hst)
    tc = build_tou_cang(facts)
    wx = build_wang_xiang(facts, facts['day_stem'])
    rr = build_root_relations(rc, facts['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(pillars, facts)
    th = build_tian_he(pillars, facts)
    network = build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th, facts=facts)
    queries = run_queries(network)
    # B1修复: 富化facts供病药层识别"财多身弱"(原harness未富化, 导致财多身弱假报为无病)
    facts['root_weight_class_facts'] = {
        pos: {'branch': pillars[pos][1],
              'class': 'HEAVY' if rc['per_pillar'][pos]['root_class'].startswith('HEAVY')
              else ('LIGHT' if rc['per_pillar'][pos]['root_class'].startswith('LIGHT') else 'NONE')}
        for pos in ('year', 'month', 'day', 'hour')
    }
    facts['tian_he'] = th
    return facts, queries


def ck(name, ok, extra=""):
    print(('PASS' if ok else 'FAIL'), name, extra)
    assert ok, name


# Case 1: 财多身弱 (乙木日主, 戌月土旺, 财多)
pillars1 = {'year':('癸','亥'),'month':('壬','戌'),'day':('乙','未'),'hour':('壬','午')}
facts1, queries1 = build_full(pillars1)
by1 = build_bingyao_layer(facts1, queries1)
print('=== Case 1: 财多身弱 ===')
print('bing_count:', by1['bing_count'])
print('yao_count:', by1['yao_count'])
print('bing_list:', [b['name'] for b in by1['bing_list']])
print('yao_list:', [y['name'] for y in by1['yao_list']])
ck('Case1 病药层state', by1['state'] == 'STRUCTURE_IDENTIFIED')
ck('Case1 有病', by1['bing_count'] >= 1)
ck('Case1 有药', by1['yao_count'] >= 1)
ck('Case1 无越权', '吉凶' not in by1['boundary_note'] or '不判' in by1['boundary_note'])

# Case 2: 杀重身轻 (庚金日主, 午月火旺, 杀重)
pillars2 = {'year':('甲','子'),'month':('丙','寅'),'day':('庚','午'),'hour':('丙','申')}
facts2, queries2 = build_full(pillars2)
by2 = build_bingyao_layer(facts2, queries2)
print('\n=== Case 2: 杀重身轻 ===')
print('bing_count:', by2['bing_count'])
print('yao_count:', by2['yao_count'])
print('bing_list:', [b['name'] for b in by2['bing_list']])
print('yao_list:', [y['name'] for y in by2['yao_list']])
ck('Case2 病药层state', by2['state'] == 'STRUCTURE_IDENTIFIED')

# Case 3: 伤官见官 (甲木日主, 伤官+官杀同时出现)
pillars3 = {'year':('丁','酉'),'month':('戊','申'),'day':('甲','子'),'hour':('辛','未')}
facts3, queries3 = build_full(pillars3)
by3 = build_bingyao_layer(facts3, queries3)
print('\n=== Case 3: 伤官见官 ===')
print('bing_count:', by3['bing_count'])
print('bing_list:', [b['name'] for b in by3['bing_list']])
ck('Case3 病药层state', by3['state'] == 'STRUCTURE_IDENTIFIED')

# Case 4: 枭神夺食 (丙火日主, 偏印+食神同时出现)
pillars4 = {'year':('甲','子'),'month':('壬','寅'),'day':('丙','午'),'hour':('戊','申')}
facts4, queries4 = build_full(pillars4)
by4 = build_bingyao_layer(facts4, queries4)
print('\n=== Case 4: 枭神夺食 ===')
print('bing_count:', by4['bing_count'])
print('bing_list:', [b['name'] for b in by4['bing_list']])
ck('Case4 病药层state', by4['state'] == 'STRUCTURE_IDENTIFIED')

print('\n病药子层 Golden: ALL PASS')
