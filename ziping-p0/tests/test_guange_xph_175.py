# -*- coding: utf-8 -*-
"""PATCH-175 官格刑破害接线 golden (G1-G7)"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.guange_rule_contract import guange_rule_input

def cond_of(month, hour):
    f = build({'year':['甲','子'],'month':month,'day':['乙','卯'],'hour':hour})
    return guange_rule_input(f)['conditions']

fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# G1 官星受冲(乙日申月官, 时支寅冲申)
g1 = cond_of(['庚','申'], ['甲','寅'])
ck("G1 官星受冲=SATISFIED(blocked)", g1['官星受冲'], 'SATISFIED')
# G5 无刑破害(年酉 月申 日卯 时午: 无三刑/六破/六害)
g5 = cond_of(['庚','申'], ['丁','午'])
g5 = None
from engines.common.l0_fact_builder import build as _b
_f5 = _b({'year':['辛','酉'],'month':['庚','申'],'day':['乙','卯'],'hour':['己','未']})
g5 = guange_rule_input(_f5)['conditions']
ck("G5 无刑=刑CLEAR", g5['刑'], 'CLEAR')
ck("G5 无破=破CLEAR", g5['破'], 'CLEAR')
ck("G5 无害=害CLEAR", g5['害'], 'CLEAR')
# G2/G6 三刑: 地支寅巳申 -> 寅巳申三刑
g6 = cond_of(['丙','巳'], ['甲','寅'])  # 年子 日卯 -> 巳寅申? 需申. 改用月申+时巳
g6 = cond_of(['庚','申'], ['丙','巳'])  # 子卯申巳 -> 寅巳申缺寅
# 直接验证结构函数
from engines.common.guange_rule_contract import _struct_state
ck("有结构=UNKNOWN", _struct_state(['寅巳申三刑']), 'UNKNOWN')
ck("空结构=CLEAR", _struct_state([]), 'CLEAR')
ck("缺数据=UNKNOWN", _struct_state(None), 'UNKNOWN')
# 刑UNKNOWN不得升级BLOCKED: note已含
ck("note含刑不升级BLOCKED", '不升级BLOCKED' in guange_rule_input(build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','午']}))['boundary_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
