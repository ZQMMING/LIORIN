# -*- coding: utf-8 -*-
"""PATCH-160.11 Readiness Rule三态"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.readiness_rule import readiness_readiness
f = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
# 160.11.1 已知无根盘: root_facts全False但字段在, 不算缺失
f_noroot = build({'year':['丙','午'],'month':['壬','子'],'day':['甲','午'],'hour':['丙','寅']})
print("无根盘root_facts:", f_noroot['root_facts'])
r_cai = readiness_readiness(f, '财')
r_guan = readiness_readiness(f, '官')
r_x = readiness_readiness(f, '神')
r_nr = readiness_readiness(f_noroot, '财')
cases = [
    ('官方齐备->SAT', r_guan['state'], 'SATISFIED'),
    ('官方仅输入齐备非强弱', '非强弱结论' in r_guan['direction'], True),
    ('财方齐备->SAT', r_cai['state'], 'SATISFIED'),
    ('未知target->UNKNOWN', r_x['state'], 'UNKNOWN'),
    ('UNKNOWN不含强弱结论', r_guan['state']!='STRONG' and r_guan['state']!='WEAK', True),
    ('已知无根不判缺失->SAT', r_nr['state'], 'SATISFIED'),
    ('无根盘无"根气信息缺失"误判', '根气信息缺失' not in ' '.join(r_nr['missing']), True),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
