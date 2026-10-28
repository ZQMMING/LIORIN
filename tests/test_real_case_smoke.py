# -*- coding: utf-8 -*-
"""真实命例 smoke: 111 个竞赛命例全跑通 160-C 整条链, 不崩/不越权.
只压工程稳定性, 不判吉凶."""
import sys, json, collections
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_power_queries import run_queries

P2S = {'JIA':'甲','YI':'乙','BING':'丙','DING':'丁','WU':'戊','JI':'己','GENG':'庚','XIN':'辛','REN':'壬','GUI':'癸'}
P2B = {'ZI':'子','CHOU':'丑','YIN':'寅','MAO':'卯','CHEN':'辰','SI':'巳','WU':'午','WEI':'未','SHEN':'申','YOU':'酉','XU':'戌','HAI':'亥'}
CASES = r'D:\顺天系统资料\shuntian\cases\global_mingli.json'

def _run(c):
    ch = c['chart']
    p = {k: [P2S[ch['four_stems'][i]], P2B[ch['four_branches'][i]]] for i, k in enumerate(('year','month','day','hour'))}
    f = build(p); pa = build_power_structure(p)
    hst = {p[k][1]: f['hidden_stems'][k] for k in ('year','month','day','hour')}
    rc = build_root_classes(p, hst); tc = build_tou_cang(f); wx = build_wang_xiang(f, f['day_stem'])
    rr = build_root_relations(rc, f['combination_facts']); ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(p, f); th = build_tian_he(p, f)
    net = build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th)
    return run_queries(net)

def test_111_real_cases_smoke():
    d = json.load(open(CASES, encoding='utf-8'))
    cases = [c for grp in d for c in grp['cases'] if c.get('chart')]
    assert len(cases) >= 100, f'案例数 {len(cases)} 不足'
    errors = []
    forbidden = ('STRONG', 'WEAK', '身强', '身弱', 'score', 'weight', 'threshold')
    for c in cases:
        try:
            for q in _run(c):
                blob = (q['name'] or '') + (q['boundary_note'] or '')
                for bad in forbidden:
                    assert bad not in blob, f'越界词 {bad}: {q["query_id"]}'
                assert q['state'] in ('SUPPORTED','NOT_SUPPORTED','UNKNOWN')
        except Exception as e:
            errors.append((c.get('case_no'), repr(e)[:100]))
    assert not errors, f'{len(errors)} 个案例崩溃: {errors[:5]}'

if __name__ == '__main__':
    test_111_real_cases_smoke()
    print('SMOKE PASS')
