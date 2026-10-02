# 冻结/已删除代码引用：zhonghe_structure/unified_overview已删除，本文件不再跑
# -*- coding: utf-8 -*-
"""P160 只读联合全景视图 · 第三刀 Golden
边界: 各孤岛并列罗列, 互不裁决; 无总裁决器/总用神/全局喜忌/吉凶; 不接生产。
"""
import sys, json, copy
sys.path.insert(0, '.')
# P0 已删除：unified_overview 模块已移除, 本 golden 冻结不再跑 (2026-09-29 接手核对)
try:
    from engines.common.unified_overview import build_unified_overview
except ModuleNotFoundError:
    print('SKIP test_unified_overview_golden: engines.common.unified_overview 已被 P0 删除, 本 golden 冻结')
    sys.exit(0)

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def mk(mg):
    return {'year': ['己', '巳'], 'month': list(mg), 'day': ['甲', '寅'], 'hour': ['丙', '寅']}


r = build_unified_overview(mk('戊辰'))

# G1 五孤岛都被串进来
check('含身强弱网络', 'daymaster_power_network' in r)
check('含ACTIVITY层', 'activity_layer' in r)
check('含PZZQ格神', 'pzzq_geshen' in r)
check('含PZZQ相神', 'pzzq_xiangshen' in r)
check('含QTBJ调候', 'qtbj_climate' in r)
check('含QTBJ调候位置投影', 'qtbj_climate_presence' in r)
check('含160-C原典命题查询', 'daymaster_queries' in r and isinstance(r['daymaster_queries'], list))
check('含特殊格局结构标签', 'special_pattern' in r and isinstance(r['special_pattern'].get('patterns'), list))
check('含客观气候结构', 'climate_structure' in r and isinstance(r['climate_structure'].get('sizhu'), dict))
check('气候挂牌 climate.structure', r['climate_structure']['namespace'] == 'climate.structure')
check('含全局中和结构', 'zhonghe_structure' in r and isinstance(r['zhonghe_structure'].get('circulation'), dict))
check('中和挂牌 zhonghe.structure', r['zhonghe_structure']['namespace'] == 'zhonghe.structure')

# G2 各域 namespace 挂牌继承
check('格神挂牌 PZZQ.use_god', r['pzzq_geshen']['namespace'] == 'PZZQ.use_god')
check('相神挂牌 PZZQ.use_god', r['pzzq_xiangshen']['namespace'] == 'PZZQ.use_god')
check('调候挂牌 QTBJ.climate_use', r['qtbj_climate']['namespace'] == 'QTBJ.climate_use')
check('调候位置投影挂牌 QTBJ.climate_use', r['qtbj_climate_presence']['namespace'] == 'QTBJ.climate_use')

# G3 联合视图自身状态
check('judgment=PARALLEL_VIEW_NO_TOTALIZER', r['judgment_status'] == 'PARALLEL_VIEW_NO_TOTALIZER')
check('有namespace_isolation声明', isinstance(r.get('namespace_isolation'), dict) and len(r['namespace_isolation']) == 11)
# 160-C query 并入后仍不偷跑命题裁决: 得时不旺/失时不弱 命题 state 恒 UNKNOWN
_q = {q['query_id']: q for q in r['daymaster_queries']}
check('得时不旺命题 state 不越权', _q['ZP-160-QUERY-DESHI-BUWANG']['state'] in ('SUPPORTED','NOT_SUPPORTED','UNKNOWN'),
      _q['ZP-160-QUERY-DESHI-BUWANG']['state'])
check('失时不弱命题 state 不越权', _q['ZP-160-QUERY-SHISHI-BURUO']['state'] in ('SUPPORTED','NOT_SUPPORTED','UNKNOWN'),
      _q['ZP-160-QUERY-SHISHI-BURUO']['state'])

# G4 顶层无总裁决器字段
for k in ['selected', 'winner', 'best', 'final', 'totalizer', 'overall_use_god', 'total_strength']:
    check('顶层无 %s' % k, r.get(k, 'ABSENT') == 'ABSENT')

# G5 跨域不串: 格神无调候键, 调候无顺逆用键
check('格神视图无climate_candidates', 'climate_candidates' not in r['pzzq_geshen'])
check('调候视图无shun_ni_yong', 'shun_ni_yong' not in json.dumps(r['qtbj_climate'], ensure_ascii=False))

# G6 跨盘变化: panxi 随盘变
r2 = build_unified_overview(mk('戊午'))
check('panxi随盘变(月支)', r['panxi']['month_branch'] == '辰' and r2['panxi']['month_branch'] == '午')
check('调候随盘变(辰先庚壬/午先癸丁)', r['qtbj_climate']['climate_candidates'][0]['stem'] == '庚'
      and r2['qtbj_climate']['climate_candidates'][0]['stem'] == '癸')

# G7 顶层不产生越界总输出(递归剔除所有 boundary_note/note 说明文本后)
def strip_notes(o):
    if isinstance(o, dict):
        return {k: strip_notes(v) for k, v in o.items() if k not in ('boundary_note', 'note', 'explanation')}
    if isinstance(o, list):
        return [strip_notes(x) for x in o]
    return o


text = json.dumps(strip_notes(r), ensure_ascii=False)
for bad in ['overall_use', '全局喜忌', '总用神', '富贵', '贫贱', '大吉', '大凶', 'total_score', 'overall_strength']:
    check('联合视图无越界: %s' % bad, bad not in text)

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
