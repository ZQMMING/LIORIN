#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""六部经典逐盘五维 diff 清单生成器 (走 tools/gate.py 唯一入口)

对 6 部 (PZZQ/DTS/QTBJ/SFTK/SMTH/YHZP) 全案例逐盘 paipan, 摊开五维引擎实际值:
  slice  : ge_cheng.ge_evidence (准神 DTS 主条 zhun + 旁参 PZZQ 辅证 pang + 刑破害透明 xph)
  boolean: bing_list.slice_condition 三态 + po_ge_hits
  stage  : 程级A′ yongshen_decision routes/winner_shen/winner_basis
  enum   : ge 格名 + strength_verdict + root_weight_class + xi_wx + cheng_bai
  topology: yuan_liu/fang_ju/tong_guan/guan_topo
产出 _六部五维diff_v1.json (逐部 cases)。
"""
import sys, os, io, json
ROOT = r'D:\shuntian-ziping-p0'
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from p0_v2.bazi_gate import paipan, load_cases
from tools.gate import check_single_instance

OK, _ = check_single_instance()
print('check_single_instance:', OK)

BOOKS = ('PZZQ', 'DTS', 'QTBJ', 'SFTK', 'SMTH', 'YHZP')

def five_dim(r):
    gc = r.get('ge_cheng') or {}
    ev = gc.get('ge_evidence') or {}
    slices = {
        'zhun': ev.get('zhun', []),
        'pang': ev.get('pang', []),
        'mapped': ev.get('mapped', False),
        'xph': ev.get('xing_po_hai'),
        'bing_refs': [b.get('slice_id') for b in (r.get('bing_list') or []) if b.get('slice_id')],
    }
    booleans = []
    for b in (r.get('bing_list') or []):
        sc = b.get('slice_condition') or {}
        booleans.append({'bing': b.get('bing_id'), 'wx': b.get('bing_wx'),
                         'sev': b.get('severity'), 'state': sc.get('state', ''),
                         'slice': sc.get('slice_id') or b.get('slice_id')})
    po_hits = [h.get('hit_type') for h in (gc.get('po_ge_hits') or [])]
    sv = ((r.get('l3_contract') or {}).get('strength_verdict') or {})
    enums = {'ge': gc.get('ge'), 'strength': sv.get('value'),
             'root_class': [v.get('class') for v in (r.get('root_weight_class') or {}).values()],
             'xi_wx': gc.get('xi_wx'), 'cheng_bai': gc.get('cheng_bai')}
    ysd = r.get('yongshen_decision') or {}
    stage = {'routes': [x.get('route') for x in (ysd.get('routes') or [])],
             'winner': ysd.get('winner_shen'), 'basis': str(ysd.get('winner_basis', ''))[:40]}
    topo = r.get('topology') or {}
    topology = {'yuan_liu': (topo.get('yuan_liu') or {}).get('yuan_wx'),
                'fang_ju': (topo.get('fang_ju') or {}).get('variant'),
                'tong_guan': len((topo.get('tong_guan') or {}).get('rules') or []),
                'guan_topo': (topo.get('guan_topo') or {}).get('topo_ok')}
    return {'slices': slices, 'booleans': booleans, 'po_ge': po_hits,
            'enums': enums, 'stage': stage, 'topology': topology}

out_books = {}
grand = 0; grand_crash = 0; grand_ge = 0; grand_map = 0; grand_bing = 0
for book in BOOKS:
    cases = load_cases(book)
    rows = []
    n_crash = n_ge = n_map = n_bing = 0
    for c in cases:
        try:
            r = paipan(c['bazi'])
        except Exception:
            n_crash += 1
            continue
        grand_crash += n_crash if False else 0
        fd = five_dim(r)
        rows.append({'cid': c.get('case_id'), 'bazi': c['bazi'], **fd})
        if (r.get('ge_cheng') or {}).get('ge'):
            n_ge += 1
        if fd['slices']['mapped']:
            n_map += 1
        if fd['booleans']:
            n_bing += 1
    out_books[book] = {'n': len(cases), 'crash': n_crash,
                       'ge_nonempty': n_ge, 'mapped': n_map, 'with_bing': n_bing,
                       'cases': rows}
    grand += len(cases)
    print('%s: %d 盘 | ge非空=%d | mapped=%d | bing=%d | crash=%d'
          % (book, len(cases), n_ge, n_map, n_bing, n_crash))

out = {'entry': 'tools/gate.py',
       'note': '六部逐盘五维diff清单 (切片ge_evidence/布尔slice_condition/程级routes/枚举ge+xi/拓扑); 准神主条zhun(DTS)+旁参pang(PZZQ)',
       'books': out_books,
       'grand': {'total': grand, 'crash': sum(b['crash'] for b in out_books.values()),
                 'ge_nonempty': sum(b['ge_nonempty'] for b in out_books.values()),
                 'mapped': sum(b['mapped'] for b in out_books.values()),
                 'with_bing': sum(b['with_bing'] for b in out_books.values())}}
dst = os.path.join(ROOT, 'p0_v2', 'case_audit', '_六部五维diff_v1.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('=== 六部合计 ===', out['grand'])
print('已落:', dst)
