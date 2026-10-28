# -*- coding: utf-8 -*-
"""PATCH-166 配合Relation前提 golden: 仅同现前提, 非配合成立"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
# 乙日: 食神=丁, 财=戊己, 官=庚辛金, 印=壬癸水, 杀=辛(七杀)
# 丁火食神+戊土正财 -> 食神生财前提
f = build({'year':['戊','子'],'month':['戊','戌'],'day':['乙','卯'],'hour':['丁','亥']})
h = f['hezuo_relation_premise']
print("食神生财:", h['食神生财'], "食神制杀:", h['食神制杀'])
fails=0
def ck(n,g,e):
    global fails
    ok=g==e; fails+=(not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
ck("食神+财同现->生财前提", h['食神生财'], True)
ck("食神+杀同现->制杀前提", h['食神制杀'], True)
# 反向: f1有财(戊)+七杀(辛)但无正官(庚) -> 财生官必须False
ck("财+杀≠财生官", h['财生官'], False)
# 干净印比盘: 无食无财无官杀
f2 = build({'year':['癸','亥'],'month':['壬','子'],'day':['乙','卯'],'hour':['壬','亥']})
h2 = f2['hezuo_relation_premise']
ck("纯印比盘->生财前提False", h2['食神生财'], False)
ck("纯印比盘->制杀前提False", h2['食神制杀'], False)
ck("不判成格", '格成' not in f and 'success' not in f, True)
ck("有note说明", '非配合成立' in h['_note'], True)
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
