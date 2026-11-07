# -*- coding: utf-8 -*-
"""ZiPing Evidence->Rule->Condition->Judgment 全链路 provenance regression。
不重新判定, 只验证可追溯性 + fail-closed 边界。"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines.common import l0_fact_builder as L
from engines.common import caige_rule_contract as C
from engines.common import guange_rule_contract as G
from engines.common import yinge_rule_contract as Y
from engines.common import shishen_rule_contract as S
from engines.common import shangguan_rule_contract as SG
from engines.common import jianlu_rule_contract as J
from engines.common import yangren_rule_contract as R

# 加载全部 evidence 原文(只索引)
EVID = {}
for p in (Path("registries/evidence")).glob("*.jsonl"):
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
            EVID[o["evidence_id"]] = o
        except Exception:
            continue

PILLARS = {'year': ['甲', '辰'], 'month': ['戊', '子'], 'day': ['戊', '辰'], 'hour': ['甲', '寅']}

def ck(name, ok, extra=""):
    print(('PASS' if ok else 'FAIL'), name, extra)
    assert ok, name

# 1. L0 -> 各 Rule, 取 condition_provenance
rules = {
    '财格': C.caige_rule_input(PILLARS),
    '官格': G.guange_rule_input(PILLARS),
    '印格': Y.yinge_rule_input(PILLARS),
    '食神格': S.shishen_rule_input(PILLARS),
    '伤官格': SG.shangguan_rule_input(PILLARS),
    '建禄月劫': J.jianlu_rule_input(PILLARS),
    '阳刃格': R.yangren_rule_input(PILLARS),
}

# 2. 全链路: 每个 condition 的 evidence_refs 都能反查到原文
total_refs = 0
missing = []
for pname, r in rules.items():
    prov = r.get('condition_provenance', {})
    ck(f'{pname} 有rule_id', bool(r.get('rule_id')))
    for cond_name, pv in prov.items():
        cid = pv.get('condition_id', '')
        ck(f'{pname}/{cond_name} condition_id', bool(cid) and cid.startswith('ZP-RULE-'))
        for ref in pv.get('evidence_refs', []):
            total_refs += 1
            if ref not in EVID:
                missing.append((pname, cond_name, ref))
ck('所有evidence_refs可反查原文', len(missing) == 0, f'缺失={missing}')
ck('evidence_refs总数>0', total_refs > 0, f'共{total_refs}条')

# 3. fail-closed 边界: state 仍 CANDIDATE, 无 STRONG/WEAK/吉凶
for pname, r in rules.items():
    ck(f'{pname} state=CANDIDATE', r['state'] == 'CANDIDATE')
    s = json.dumps(r, ensure_ascii=False)
    ck(f'{pname} 无STRONG/WEAK越权', 'STRONG' not in s and 'WEAK' not in s)

# 4. 三态不被 evidence_refs 改写: 财太露仍 UNKNOWN
ck('财太露仍UNKNOWN', rules['财格']['conditions']['财太露'] == 'UNKNOWN')
ck('财逢七杀仍blocked语义', rules['财格']['condition_provenance']['财逢七杀']['authorization'] == 'blocked')

print(f'\n全链路 provenance regression: {len(rules)}格, {total_refs}条evidence_refs, 0缺失')
print('ALL PASS')
