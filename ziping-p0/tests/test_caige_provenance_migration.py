# -*- coding: utf-8 -*-
"""财格 Provenance 迁移样板验收 (4项)。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.common import caige_rule_contract as c
from tests.validate_provenance_contract import EXISTING_EVIDENCE_IDS

def build():
    pillars = {'year': ['甲', '辰'], 'month': ['戊', '子'], 'day': ['戊', '辰'], 'hour': ['甲', '寅']}
    return c.caige_rule_input(pillars)

def ck(name, ok):
    print(('PASS' if ok else 'FAIL'), name)
    assert ok, name

r = build()

# 1. condition_id 唯一
p = r['condition_provenance']
ids = [v['condition_id'] for v in p.values()]
ck('G1 condition_id唯一', len(ids) == len(set(ids)) == 4)

# 2. evidence_refs 全部存在
all_refs_ok = all(
    ref in EXISTING_EVIDENCE_IDS
    for v in p.values() for ref in v['evidence_refs']
)
ck('G2 evidence_refs全部存在', all_refs_ok)

# 3. 旧 Rule 输出逐项等价（三态值仍是原字符串）
cond = r['conditions']
ck('G3a 财有根三态仍在', cond['财有根'] in ('SATISFIED', 'UNSATISFIED', 'UNKNOWN'))
ck('G3b 财透三态仍在', cond['财透'] in ('SATISFIED', 'UNSATISFIED', 'UNKNOWN'))
ck('G3c 财太露仍UNKNOWN', cond['财太露'] == 'UNKNOWN')
ck('G3d 财逢七杀伤力态仍在', cond['财逢七杀'] in ('SATISFIED', 'UNSATISFIED', 'UNKNOWN'))

# 4. provenance regression: 财太露不挂证据变SAT, 财逢七杀不升required
ck('G4a 财太露authorization=unknown_pending', p['财太露']['authorization'] == 'unknown_pending')
ck('G4b 财逢七杀authorization=blocked', p['财逢七杀']['authorization'] == 'blocked')
ck('G4c state仍CANDIDATE', r['state'] == 'CANDIDATE')
ck('G4d rule_id=ZP-RULE-CAI', r['rule_id'] == 'ZP-RULE-CAI')

print('财格迁移验收: ALL PASS')
