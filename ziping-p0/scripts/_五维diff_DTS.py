#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DTS 逐盘五维 diff 清单生成器 (走 tools/gate.py 唯一入口)

对 DTS 有断语案例逐盘 paipan, 摊开五维引擎实际值:
  slice  : 命中切片ID (ge_cheng.ge_evidence.zhun/zhu/pang + bing_list.slice_id)
  boolean: 切片条件三态 MATCHED/NOT_MATCHED/ABSTAIN + 破格命中
  stage  : 程级A′ routes/winner_shen/winner_basis
  enum   : ge 格名 + strength_verdict.value + root_weight_class
  topology: yuan_liu/fang_ju/tong_guan/guan_topo
并核底层六块(L0/L1/L2/L3/L4/拓扑)全展开。
产出 _DTS23_五维diff_v1.json。
"""
import sys, os, io, json
ROOT = r'D:\shuntian-ziping-p0'
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from p0_v2.bazi_gate import paipan, load_cases
from tools.gate import check_single_instance

OK, _ = check_single_instance()
print('check_single_instance:', OK)

j75 = json.load(open(os.path.join(ROOT, 'p0_v2', 'case_audit', '_75盘_完整断语.json'), encoding='utf-8-sig'))
v2 = json.load(open(os.path.join(ROOT, 'p0_v2', 'case_audit', '_DTS23_校验器v2.json'), encoding='utf-8-sig'))
vmap = {v['cid']: v for v in v2}
dts = [c for c in j75 if c['book'] == 'DTS']

def five_dim(r):
    gc = r.get('ge_cheng') or {}
    ev = gc.get('ge_evidence') or {}
    # 切片维: 证据链(准神主条 + 旁参辅证) + bing_list slice_id
    slices = {
        'zhun': ev.get('zhun', []),
        'zhu': ev.get('zhu', []),
        'pang': ev.get('pang', []),
        'mapped': ev.get('mapped', False),
        'rule_text': str(ev.get('rule_text', ''))[:40],
        'bing_refs': [b.get('slice_id') for b in (r.get('bing_list') or []) if b.get('slice_id')],
    }
    # 布尔维
    booleans = []
    for b in (r.get('bing_list') or []):
        sc = b.get('slice_condition') or {}
        booleans.append({'bing': b.get('bing_id'), 'wx': b.get('bing_wx'),
                         'sev': b.get('severity'), 'state': sc.get('state', ''),
                         'slice': sc.get('slice_id') or b.get('slice_id')})
    po_hits = [h.get('hit_type') for h in (gc.get('po_ge_hits') or [])]
    # 枚举维
    sv = ((r.get('l3_contract') or {}).get('strength_verdict') or {})
    enums = {'ge': gc.get('ge'), 'strength': sv.get('value'),
             'root_class': [v.get('class') for v in (r.get('root_weight_class') or {}).values()],
             'xi_wx': gc.get('xi_wx'), 'cheng_bai': gc.get('cheng_bai')}
    # 程级维
    ysd = r.get('yongshen_decision') or {}
    stage = {'routes': [x.get('route') for x in (ysd.get('routes') or [])],
             'winner': ysd.get('winner_shen'), 'basis': str(ysd.get('winner_basis', ''))[:40]}
    # 拓扑维
    topo = r.get('topology') or {}
    topology = {'yuan_liu': (topo.get('yuan_liu') or {}).get('yuan_wx'),
                'fang_ju': (topo.get('fang_ju') or {}).get('variant'),
                'tong_guan': len((topo.get('tong_guan') or {}).get('rules') or []),
                'guan_topo': (topo.get('guan_topo') or {})}
    return {'slices': slices, 'booleans': booleans, 'po_ge': po_hits,
            'enums': enums, 'stage': stage, 'topology': topology}

out_cases = []
for c in dts:
    cid = c['case_id']
    r = paipan(c['bazi'])
    fd = five_dim(r)
    out_cases.append({'cid': cid, 'bazi': c['bazi'],
                      'ans': (vmap.get(cid) or {}).get('g', {}).get('wx') or None,
                      'verdict': (vmap.get(cid) or {}).get('v', ''),
                      **fd})

out = {'book': 'DTS', 'entry': 'tools/gate.py',
       'note': "切片维读 ge_cheng.ge_evidence (准神DTS主条+旁参PZZQ辅证, 2026-10-17 新增证据链)",
       'cases': out_cases,
       'stat': {'n': len(out_cases),
                 'with_answer': sum(1 for e in out_cases if e['ans']),
                 'with_evidence': sum(1 for e in out_cases if e['slices']['mapped']),
                 'with_bing_refs': sum(1 for e in out_cases if e['slices']['bing_refs']),
                 'verdict_dist': {k: sum(1 for e in out_cases if e['verdict'] == k)
                                  for k in sorted(set(e['verdict'] for e in out_cases))}}}
dst = os.path.join(ROOT, 'p0_v2', 'case_audit', '_DTS23_五维diff_v1.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已落:', dst)
print(out['stat'])
for c in out_cases:
    if c['ans']:
        print(c['cid'], 'ans=', c['ans'], '| 准=', c['slices']['zhun'], '| 旁=', c['slices']['pang'],
              '| winner=', c['stage']['winner'], '| ge=', c['enums']['ge'])
