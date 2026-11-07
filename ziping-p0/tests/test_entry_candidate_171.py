# -*- coding: utf-8 -*-
"""PATCH-171 Entry->Candidate Contract golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.entry_candidate_contract import build_candidates
def types_of(mm, zz, day='乙'):
    f = build({'year':['甲','子'],'month':[mm,zz],'day':[day,'卯'],'hour':['丁','亥']})
    return [x['entry_type'] for x in build_candidates(f)['candidates']]

fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
# 乙日: 财=戊己,官=庚辛,印=壬癸,食=丁,杀=辛,伤=丙
ck("财月->财格", '财格' in types_of('戊','戌'), True)
ck("官月->官格", '官格' in types_of('庚','申'), True)
ck("印月->印格", '印格' in types_of('壬','子'), True)
ck("食月->食神格", '食神格' in types_of('丁','午'), True)
ck("杀月->七煞格", '七煞格' in types_of('辛','酉'), True)
ck("伤月->伤官格", '伤官格' in types_of('丙','巳'), True)
ck("比月->建禄", '建禄' in types_of('乙','卯'), True)
ck("劫月->月劫", '月劫' in types_of('甲','寅'), True)
# 阳刃: 甲日卯月
fr = build({'year':['甲','子'],'month':['甲','卯'],'day':['甲','寅'],'hour':['丁','亥']})
ck("阳刃->阳刃格", '阳刃格' in [x['entry_type'] for x in build_candidates(fr)['candidates']], True)
ck("state=CANDIDATE", build_candidates(fr)['candidates'][0]['state'], 'CANDIDATE')
ck("premise=可查询非已成立", '非已成立' in build_candidates(fr)['candidates'][0]['premise_refs'][0], True)
ck("禁成列表含格成", '格成' in build_candidates(fr)['boundary']['forbidden_outputs'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
