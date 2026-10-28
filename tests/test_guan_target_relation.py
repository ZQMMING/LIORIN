# -*- coding: utf-8 -*-
"""PATCH-155 官星受冲/被合: 关系必须作用到官星本身"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.condition_router import route_condition

# 丁日: 官=水(壬癸). 年丁+月壬 => 丁壬合, 壬=丁官 => 官星被合
he = build({'year':['丁','子'],'month':['壬','寅'],'day':['丁','卯'],'hour':['己','巳']})
# 丁日官支亥(藏壬), 时支巳冲亥 => 官星受冲
chong = build({'year':['甲','子'],'month':['壬','亥'],'day':['丁','卯'],'hour':['己','巳']})
# 有合但合的不是官: 丙辛合但辛非丁官
plain = build({'year':['丙','子'],'month':['辛','寅'],'day':['丁','卯'],'hour':['己','巳']})
cases = [
    ('官星被合(丁壬合壬=官)', route_condition('官星被合', he)['status'], 'SATISFIED'),
    ('有合但非官被合', route_condition('官星被合', plain)['status'], 'UNSATISFIED'),
    ('官星受冲(巳冲亥官支)', route_condition('官星受冲', chong)['status'], 'SATISFIED'),
    ('有六冲但非官支', route_condition('官星受冲', plain)['status'], 'UNSATISFIED'),
]
fails=0
for n,g,e in cases:
    ok=g==e; fails+=(not ok)
    print(f"{'PASS' if ok else 'FAIL'} {n}: {g} (期望{e})")
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
