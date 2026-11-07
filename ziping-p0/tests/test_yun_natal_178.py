# -*- coding: utf-8 -*-
"""PATCH-178 运x命局结构关系 golden"""
import sys; sys.path.insert(0,'.')
from engines.common.relation_178 import yun_natal_relations

fails=0
def ck(n,g,e):
    global fails; ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

pillars={'year':['甲','子'],'month':['丙','申'],'day':['乙','亥'],'hour':['戊','辰']}
# 大运己巳
rels=yun_natal_relations({'decade':['己','巳']},pillars)
types=[(r['relation'],r.get('natal_pillar'),r.get('he') or r.get('branches')) for r in rels]
ck("运干己+年干甲=甲己合", ('天干五合','year','甲己合') in types, True)
ck("运支巳+月支申=巳申六合", ('地支六合','month',['巳','申']) in types, True)
ck("运支巳+日支亥=巳亥六冲(带position)", ('地支六冲','day',['巳','亥']) in types, True)
# 三合: 运申 + 命局子辰 -> 申子辰水局
p2={'year':['甲','子'],'month':['丙','寅'],'day':['乙','卯'],'hour':['戊','辰']}
r2=yun_natal_relations({'decade':['庚','申']},p2)
san=[x for x in r2 if x['relation']=='三合']
ck("运申+子辰=申子辰水局", len(san)==1 and san[0]['group']=='申子辰水局', True)
ck("三合note非成格", '非成格' in san[0]['note'], True)
# 透清: 运干透命局藏干. 丁透自亥(亥藏壬甲?无丁). 用运干甲透自寅(寅藏甲丙戊)
p3={'year':['甲','子'],'month':['丙','寅'],'day':['乙','亥'],'hour':['戊','辰']}
r3=yun_natal_relations({'decade':['甲','申']},p3)
tou=[x for x in r3 if x['relation']=='透清']
ck("运干甲透寅藏干=透清", any(x['branch']=='寅' for x in tou), True)
ck("透清note非用神成立", all('非用神成立' in x['note'] for x in tou), True)
# 空运不报错
ck("空运=空列表", yun_natal_relations({},pillars), [])
# 边界: 无喜忌吉凶字段
ck("结果无喜忌字段", not any('喜' in str(r) or '忌' in str(r) or '吉' in str(r) or '凶' in str(r) for r in rels), True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
