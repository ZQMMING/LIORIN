# -*- coding: utf-8 -*-
"""PATCH-146 blocked/supported bundle + required×blocked合成"""
import sys
sys.path.insert(0, '.')
from engines.common.condition_bundle import aggregate_required, aggregate_blocked, synthesize

def req(*s): return [{'condition': f'c{i}', 'status': v} for i, v in enumerate(s)]
def blk(*s): return [{'condition': f'b{i}', 'status': v} for i, v in enumerate(s)]

cases = [
    ('blocked全UNSAT->CLEAR', aggregate_blocked(blk('UNSATISFIED','UNSATISFIED'))['bundle_status'], 'CLEAR'),
    ('blocked有SAT->BLOCKED', aggregate_blocked(blk('UNSATISFIED','SATISFIED'))['bundle_status'], 'BLOCKED'),
    ('blocked有UNK->BLOCK_UNKNOWN', aggregate_blocked(blk('UNSATISFIED','UNKNOWN'))['bundle_status'], 'BLOCK_UNKNOWN'),
    ('blocked空->BLOCK_UNKNOWN', aggregate_blocked(blk())['bundle_status'], 'BLOCK_UNKNOWN'),
]
# 合成: req SAT + blk CLEAR -> SUPPORTED
syn = synthesize(aggregate_required(req('SATISFIED','SATISFIED')),
                 aggregate_blocked(blk('UNSATISFIED')), [])
cases.append(('合成SUPPORTED', syn['candidate_direction'], 'SUPPORTED'))
syn2 = synthesize(aggregate_required(req('UNSATISFIED','SATISFIED')),
                  aggregate_blocked(blk('UNSATISFIED')), [])
cases.append(('合成NOT_SUPPORTED', syn2['candidate_direction'], 'NOT_SUPPORTED'))
syn3 = synthesize(aggregate_required(req('SATISFIED','UNKNOWN')),
                  aggregate_blocked(blk('UNSATISFIED')), [])
cases.append(('合成PENDING', syn3['candidate_direction'], 'PENDING'))

fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
