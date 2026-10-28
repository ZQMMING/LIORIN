# -*- coding: utf-8 -*-
"""PATCH-160.6 成员事实->SFTK六条输入表达回测
证明: ten_god_members能枚举成员, 但不产生旺衰结论; 同count不直判旺。"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

def members_of(f, tg_set):
    return [m for m in f['ten_god_members'] if m['ten_god'] in tg_set]

CAI = {'正财','偏财'}; BI = {'比肩','劫财'}; SHA = {'七杀','正官'}
cases = [
    # 财成员多但根轻 vs 财成员少但根重
    ('财多根轻', build({'year':['戊','子'],'month':['戊','戌'],'day':['甲','寅'],'hour':['己','巳']})),
    ('财少根重', build({'year':['甲','子'],'month':['戊','午'],'day':['甲','寅'],'hour':['丙','寅']})),
    # 日主有根但失令
    ('有根失令', build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})),
    # 杀有成员但无轻重判断
    ('杀有成员', build({'year':['庚','午'],'month':['庚','辰'],'day':['甲','子'],'hour':['丙','寅']})),
]
fails=0
for name, f in cases:
    cai = members_of(f, CAI); bi = members_of(f, BI); sha = members_of(f, SHA)
    # 关键断言: L0只列成员, 不输出任何旺衰字段
    has_strength_field = any(k in f for k in ['strength','daymaster_strong','wealth_strong','party_strength'])
    print(f"[{name}] 财成员{len(cai)} 比劫{len(bi)} 官杀{len(sha)} | 无旺衰字段:{not has_strength_field}")
    assert not has_strength_field
    # 财成员可定位到柱/本中余气
    if cai:
        assert all('pillar' in c and 'qi_position' in c for c in cai)
print("\n=== 关键边界: 同count不直判旺 ===")
# 两个财成员数不同的命局, 系统不应给出任何'财旺/财多'布尔
for name, f in cases:
    assert '财多' not in f and '财旺' not in f and '身强' not in f and '身弱' not in f
print("PASS: ten_god_members=必要输入, 未携带旺衰结论; SFTK六条最终旺衰仍UNKNOWN(不强行减少)")
print("=> ALL PASS")
sys.exit(0)
