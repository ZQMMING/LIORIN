# -*- coding: utf-8 -*-
"""应期复合旺衰 transit_power golden:
G1 空岁运复合七档与主链逐例等价; G2 岁运禄根入复合根; G3 印+禄抬档;
G4 衰神冲旺旺神发/旺者冲衰衰者拔(五行旺衰有序枚举比较); G5 岁运半合归化;
G6 结构-only无喜忌用神吉凶STRONG/WEAK; G7 岁运不改月令日干。"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engines.common.l0_fact_builder import build as l0build, WUXING
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.wuxing_power import build_wuxing_power, build_spectrum_topology
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_power_network import build_power_network
from engines.common.transit_power import build_transit_power, transit_clash_verdicts

fails = []
def check(name, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else ' :: ' + str(extra)))
    if not cond: fails.append(name)

def gp(chart):
    g = list(chart.replace(' ', ''))
    return {pos: [g[i*2], g[i*2+1]] for i, pos in enumerate(('year','month','day','hour'))}

def main_spectrum(chart):
    p = gp(chart); f = l0build(p); th = build_tian_he(p, f); wp = build_wuxing_power(p, f, th)
    ds = p['day'][0]
    pa = build_power_structure(p)
    hst = {p[k][1]: f['hidden_stems'][k] for k in ('year','month','day','hour')}
    rc = build_root_classes(p, hst)
    tc = build_tou_cang(f); wxo = build_wang_xiang(f, ds)
    rr = build_root_relations(rc, f['combination_facts']); ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(p, f)
    net = build_power_network(pa, rc, tc, wxo, rr, ts, branch_tier=bt, tian_he=th, facts=f)
    net.setdefault('facts', {})['daymaster_element'] = WUXING[ds]
    return build_spectrum_topology(net, wp)

# G1 空岁运等价
for c in ['己巳己巳乙酉丙戌','辛亥壬辰丙申己亥','甲辰丁卯甲子戊辰','壬申丙午庚午庚辰','辛卯丁酉庚午丙子']:
    main_spec = main_spectrum(c)['spectrum']
    tp = build_transit_power(gp(c), extra_pillars=[])
    check('G1 空岁运七档等价 '+c, tp['spectrum']['spectrum'] == main_spec,
          (tp['spectrum']['spectrum'], main_spec))

# G2 岁运禄根入复合根(藏干兜底)
p = gp('己巳己巳乙酉丙戌')
tp = build_transit_power(p, extra_pillars=[['己','卯']])
check('G2 岁运卯为乙禄 HEAVY_LU', tp['root_class_detail'].get('卯') == 'HEAVY_LU', tp['root_class_detail'])
check('G2 复合木本气根 ben_n=1', tp['wuxing_power']['wuxing_power']['木']['ben_n'] == 1)

# G3 印+禄抬档(衰极 -> 非衰极)
tp0 = build_transit_power(p, extra_pillars=[])
tp3 = build_transit_power(p, extra_pillars=[['丁','亥'],['己','卯']])
order = ['衰', '平', '旺', '强']
check('G3 原局衰极', tp0['spectrum']['spectrum'] == '衰', tp0['spectrum']['spectrum'])
check('G3 印禄岁运抬档', order.index(tp3['spectrum']['spectrum']) > order.index('衰'), tp3['spectrum']['spectrum'])

# G4 衰神冲旺旺神发: 甲木当令重根, 岁运酉冲卯 -> 木旺金衰, 酉拔卯发
p = gp('甲辰丁卯甲子戊辰')
tp = build_transit_power(p, extra_pillars=[['庚','酉']])
vs = transit_clash_verdicts(tp)
mq = [v['verdict'] for v in vs if set(v['pair']) == {'卯','酉'}]
check('G4 复合七档仍太旺(旺根不被拔)', tp['spectrum']['spectrum'] == '强', tp['spectrum']['spectrum'])
check('G4 卯酉冲 酉衰者拔卯旺神发', any('酉衰者拔' in v and '卯旺神发' in v for v in mq), mq)

# G5 岁运半合归化: 辛卯丁酉庚午丙子 午在, 岁运寅 -> 寅午半合火
p = gp('辛卯丁酉庚午丙子')
ban0 = build_transit_power(p, extra_pillars=[])['wuxing_power']['wuxing_power']['火']['banhe_n']
tp5 = build_transit_power(p, extra_pillars=[['戊','寅']])
ban1 = tp5['wuxing_power']['wuxing_power']['火']['banhe_n']
check('G5 岁运寅午半合火 banhe 增加', ban1 >= ban0 + 1, (ban0, ban1))

# G6 结构-only 无越界词(先递归剔除 boundary_note/note/explanation 否定声明, 与 unified golden 同口径)
import json as _json
def _strip_notes(o):
    if isinstance(o, dict):
        return {k: _strip_notes(v) for k, v in o.items() if k not in ('boundary_note', 'note', 'explanation')}
    if isinstance(o, list):
        return [_strip_notes(v) for v in o]
    return o
blob = _json.dumps(_strip_notes(tp5), ensure_ascii=False)
for bad in ['喜神','忌神','用神','富贵','贫贱','大吉','大凶','STRONG','WEAK','total_score']:
    check('G6 无越界词 '+bad, bad not in blob)
check('G6 judgment_status 结构only', tp5['judgment_status'] == 'TRANSIT_POWER_PURE_RULE')

# G7 岁运不改月令日干(该造月支酉=金令)
check('G7 月令仍原局(酉月金)', tp5['wuxing_power']['month_element'] == '金', tp5['wuxing_power']['month_element'])
check('G7 日干仍庚', tp5['daymaster'] == '庚')

print('\nTOTAL FAILS', len(fails))
sys.exit(1 if fails else 0)
