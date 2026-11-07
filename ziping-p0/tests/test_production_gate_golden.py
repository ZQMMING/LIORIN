# -*- coding: utf-8 -*-
"""Production Entry Gate Golden GP-001~010."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.production_entry import production_entry, FrozenCanonicalBaziChart

PILLARS = {'year': ['甲', '辰'], 'month': ['戊', '子'], 'day': ['戊', '辰'], 'hour': ['甲', '寅']}

def ck(name, ok, extra=""):
    print(('PASS' if ok else 'FAIL'), name, extra)
    assert ok, name

# GP-001 valid FrozenCanonical -> PASS
r = production_entry(FrozenCanonicalBaziChart(pillars=PILLARS))
ck('GP-001 valid canonical -> gate_passed', r['gate_passed'] is True and r['engine_result'] is not None)

# GP-002 ordinary pillars dict -> REJECT
r2 = production_entry(PILLARS)
ck('GP-002 普通dict -> REJECT', r2['gate_passed'] is False and r2['engine_result'] is None)

# GP-003 BaziChart(模拟) -> REJECT
class FakeBaziChart:
    def __init__(self, p): self.pillars = p
r3 = production_entry(FakeBaziChart(PILLARS))
ck('GP-003 BaziChart对象 -> REJECT', r3['gate_passed'] is False and r3['engine_result'] is None)

# GP-004 BirthInput(模拟) -> REJECT
class BirthInput:
    def __init__(self, p): self.pillars = p
r4 = production_entry(BirthInput(PILLARS))
ck('GP-004 BirthInput -> REJECT', r4['gate_passed'] is False)

# GP-005 malformed canonical -> REJECT
bad = FrozenCanonicalBaziChart(pillars={'year': ['甲', '辰'], 'month': ['戊']})
r5 = production_entry(bad)
ck('GP-005 malformed -> REJECT', r5['gate_passed'] is False)

# GP-006 missing frozen/canonical identity -> REJECT
import dataclasses
r6 = production_entry(FrozenCanonicalBaziChart(pillars=PILLARS, canonical=False, frozen=True))
ck('GP-006 缺身份标记 -> REJECT', r6['gate_passed'] is False)

# GP-007 Gate failure -> no Rule/Judgment execution (engine_result 必须为 None)
ck('GP-007 gate失败不执行主链', r2['engine_result'] is None and r3['engine_result'] is None)

# GP-008 valid canonical -> EngineResult (facts 存在)
ck('GP-008 EngineResult含facts', 'root_facts' in r['engine_result'] or 'combination_facts' in r['engine_result'])

# GP-009 EngineResult remains fail-closed (无 Judgment 越权字段)
# 注: WEAK 在此为 changsheng_direction 已有授权标签(176), 非身强弱 Judgment
import json
s = json.dumps(r['engine_result'], ensure_ascii=False)
ck('GP-009 result无越权', 'STRONG' not in s and '用神' not in s)
ck('GP-009b 无吉/凶Judgment value', '吉凶判断' not in s and '大凶' not in s)

# GP-010 no STRONG/用神 Judgment (gate 层也不产; WEAK=changsheng标签豁免)
# 注: boundary_note说明"不判用神"含用神字样属正常; l1_result里的query名称(YONGSHEN-*)只是结构查询ID
er_s = json.dumps(r['engine_result'], ensure_ascii=False)
ck('GP-010 engine_result无越权', r['gate_passed'] is True and '用神' not in er_s and 'STRONG' not in er_s)
ck('GP-010b L1 Query存在且无越权输出', 'l1_result' in r and r['l1_result']['query_summary']['total'] == 40 and r['l1_result']['query_summary']['unknown'] == 0)

print('\nProduction Entry Gate Golden GP-001~010: ALL PASS')
