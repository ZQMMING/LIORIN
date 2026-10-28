# -*- coding: utf-8 -*-
# 冻结/已删除代码引用：zhonghe_structure/unified_overview已删除，本文件不再跑
"""古命例端到端验收 · 原典命例结构自洽性核对
来源: YHZP-082-001《論七殺》A级原文三命例.
边界: 引擎不输出身强/身弱裁决(Resolver NOT_AUTHORIZED);
本验收只核对"引擎读出的多维结构"是否与原典文字描述的结构自洽, 不要求引擎判身强弱.
"""
import sys, json
sys.path.insert(0, '.')
# P0 已删除：unified_overview/zhonghe_structure 模块已移除, 本 golden 冻结不再跑 (2026-09-29 接手核对)
try:
    from engines.common.unified_overview import build_unified_overview
except ModuleNotFoundError:
    print('SKIP test_ancient_case_golden: engines.common.unified_overview 已被 P0 删除, 本 golden 冻结')
    sys.exit(0)

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def dim(p):
    r = build_unified_overview(p)
    return r['daymaster_power_network']['dimensions'], {q['query_id']: q for q in r['daymaster_queries']}


# 例2: 甲午 丙寅 庚子 丙子 — 原典: 身弱, 月令丙寅七杀, 火克金, 金死子, 身弱杀旺无制
d, q = dim({'year': ['甲', '午'], 'month': ['丙', '寅'], 'day': ['庚', '子'], 'hour': ['丙', '子']})
check('例2 失令(庚生寅月)', d['SEASONAL']['state'] == 'OUT_OF_SEASON', d['SEASONAL']['state'])
check('例2 无根', d['ROOT']['has_root'] is False and d['ROOT']['root_weight_class'] == 'NONE',
      d['ROOT']['root_weight_class'])
check('例2 官杀成党(丙双透+寅午火根)',
      d['CONTROL']['GUANSHA']['stem_present'] and d['CONTROL']['GUANSHA']['root_present'])
check('例2 无根不能任财官', q['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'NOT_SUPPORTED',
      q['ZP-160-QUERY-REN-CAIGUAN']['state'])
check('例2 不谬报"失时不弱"', q['ZP-160-QUERY-SHISHI-BURUO']['match_type'] == 'NO_MATCH',
      q['ZP-160-QUERY-SHISHI-BURUO']['match_type'])

# 例1: 辛丑 乙未 乙卯 丙子 — 原典: 身旺生于六月, 贵而有权
d1, q1 = dim({'year': ['辛', '丑'], 'month': ['乙', '未'], 'day': ['乙', '卯'], 'hour': ['丙', '子']})
check('例1 有根', d1['ROOT']['has_root'] is True)
check('例1 根为重根(卯禄)', d1['ROOT']['root_weight_class'] == 'HEAVY', d1['ROOT']['root_weight_class'])
check('例1 比劫成党(乙透+卯根)',
      d1['SUPPORT']['BIJIE']['stem_present'] and d1['SUPPORT']['BIJIE']['root_present'])
check('例1 有根能任财官', q1['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'SUPPORTED',
      q1['ZP-160-QUERY-REN-CAIGUAN']['state'])

# 例3: 丁巳 戊申 壬子 戊申 — 原典: 身旺, 丁壬合戊癸合, 贵
d3, q3 = dim({'year': ['丁', '巳'], 'month': ['戊', '申'], 'day': ['壬', '子'], 'hour': ['戊', '申']})
check('例3 月令印生(金生水 SUPPORTS)', d3['SEASONAL']['state'] == 'SUPPORTS', d3['SEASONAL']['state'])
check('例3 有根', d3['ROOT']['has_root'] is True)
check('例3 有根能任财官', q3['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'SUPPORTED',
      q3['ZP-160-QUERY-REN-CAIGUAN']['state'])

# 越界防护: 三例引擎都不输出身强/身弱裁决
for tag, qq in [('例2', q), ('例1', q1), ('例3', q3)]:
    for _qid, qqq in qq.items():
        check('%s 命题不裁决(无STRONG/WEAK)' % tag,
              qqq['state'] not in ('STRONG', 'WEAK'))

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
