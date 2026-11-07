# -*- coding: utf-8 -*-
"""PATCH-141H-C golden: bundle三态聚合"""
import sys
sys.path.insert(0, '.')
from engines.common.condition_bundle import aggregate_required

cases = [
    ([{'condition':'a','status':'SATISFIED'},{'condition':'b','status':'SATISFIED'}], 'SATISFIED'),
    ([{'condition':'a','status':'SATISFIED'},{'condition':'b','status':'UNSATISFIED'}], 'UNSATISFIED'),
    ([{'condition':'a','status':'SATISFIED'},{'condition':'b','status':'UNKNOWN'}], 'UNKNOWN'),
    ([{'condition':'a','status':'UNKNOWN'}], 'UNKNOWN'),
    ([], 'UNKNOWN'),
]
fails=0
for items,e in cases:
    g=aggregate_required(items)['bundle_status']; ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {[x['status'] for x in items]} -> {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
