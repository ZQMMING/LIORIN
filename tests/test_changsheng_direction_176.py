# -*- coding: utf-8 -*-
"""PATCH-176 changsheng_direction golden (SFTK-010-004)"""
import sys; sys.path.insert(0,'.')
from engines.common.l0_fact_builder import build

fails=0
def ck(n,g,e):
    global fails; ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 构造: 日干dg, 地支z(放到日支位), 其余干支随意
def cd_of(dg,z):
    f=build({'year':['甲','子'],'month':['丙','寅'],'day':[dg,z],'hour':['戊','辰']})
    return f['changsheng_direction'].get('day',{}).get('direction')

# 阳生=TRUE_LIFE
ck("甲生亥=TRUE_LIFE", cd_of('甲','亥'), 'TRUE_LIFE')
ck("丙生寅=TRUE_LIFE", cd_of('丙','寅'), 'TRUE_LIFE')
ck("戊生寅=TRUE_LIFE", cd_of('戊','寅'), 'TRUE_LIFE')
ck("庚生巳=TRUE_LIFE", cd_of('庚','巳'), 'TRUE_LIFE')
ck("壬生申=TRUE_LIFE", cd_of('壬','申'), 'TRUE_LIFE')
# 阴生=WEAK
ck("乙生午=WEAK", cd_of('乙','午'), 'WEAK')
ck("丁生酉=WEAK", cd_of('丁','酉'), 'WEAK')
ck("己生酉=WEAK", cd_of('己','酉'), 'WEAK')
ck("辛生子=WEAK", cd_of('辛','子'), 'WEAK')
ck("癸生卯=WEAK", cd_of('癸','卯'), 'WEAK')
# 阴死=LIFE
ck("乙死亥=LIFE", cd_of('乙','亥'), 'LIFE')
ck("丁死寅=LIFE", cd_of('丁','寅'), 'LIFE')
ck("己死寅=LIFE", cd_of('己','寅'), 'LIFE')
ck("辛死巳=LIFE", cd_of('辛','巳'), 'LIFE')
ck("癸死申=LIFE", cd_of('癸','申'), 'LIFE')
# 阳死=TRUE_DEATH
ck("甲死午=TRUE_DEATH", cd_of('甲','午'), 'TRUE_DEATH')
ck("丙死子=TRUE_DEATH", cd_of('丙','子'), 'TRUE_DEATH')
ck("戊死子=TRUE_DEATH", cd_of('戊','子'), 'TRUE_DEATH')
ck("庚死子=TRUE_DEATH", cd_of('庚','子'), 'TRUE_DEATH')
ck("壬死卯=TRUE_DEATH", cd_of('壬','卯'), 'TRUE_DEATH')
# 阴阳同宫自洽: 同一支亥, 对甲=TRUE_LIFE, 对乙=LIFE
ck("亥对甲=TRUE_LIFE", cd_of('甲','亥'), 'TRUE_LIFE')
ck("亥对乙=LIFE", cd_of('乙','亥'), 'LIFE')
ck("午对甲=TRUE_DEATH", cd_of('甲','午'), 'TRUE_DEATH')
ck("午对乙=WEAK", cd_of('乙','午'), 'WEAK')
# 反例: 其余八运无标签
ck("甲临子(沐浴)无标签", cd_of('甲','子'), None)
# note锁旺衰
f=build({'year':['甲','子'],'month':['丙','寅'],'day':['甲','亥'],'hour':['戊','辰']})
ck("note含长生不等于旺", '长生不等于旺' in f['changsheng_direction_note'], True)
ck("note含不进160", '不进160' in f['changsheng_direction_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
