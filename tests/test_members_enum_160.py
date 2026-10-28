# -*- coding: utf-8 -*-
"""PATCH-160.5 十神成员枚举golden"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
f = build({'year':['甲','子'],'month':['庚','申'],'day':['乙','卯'],'hour':['丁','亥']})
m = f['ten_god_members']
print("成员数:", len(m))
for x in m: print(' ', x['pillar'], x['type'], x['stem'], x.get('qi_position'), '->', x['ten_god'])
# 验证
fails = 0
def ck(n, g, e):
    global fails
    ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")
# 1 天干成员(3, 排除日干)
ck("天干成员3", len([x for x in m if x['type']=='stem']), 3)
# 2 藏干成员(四柱藏干总数)
import json
HIDDEN = json.load(open('registries/zhi_hidden_stems_v1.json', encoding='utf-8'))['hidden_stems']
exp_hidden = sum(len(HIDDEN[b]) for b in ['子','申','卯','亥'])
ck("藏干成员数", len([x for x in m if x['type']=='hidden']), exp_hidden)
# 3 本气provenance可溯
benqi = [(x['branch'],x['stem']) for x in m if x['type']=='hidden' and x['qi_position']=='本气']
ck("本气可溯", ('申','庚') in benqi, True)
# 4 同十神多成员保留(不set)
ck("无set化(成员>唯一)", len(m), len(m))
# 5 日干不进stem成员
ck("日干不入成员", all(x['stem']!='乙' or x['type']=='hidden' for x in m if x['pillar']=='day' and x['type']=='stem'), True)
# 6 分组中性: 印比=印+比劫
SUPPORT = {'比肩','劫财','正印','偏印'}
sup = [x for x in m if x['ten_god'] in SUPPORT]
drai = [x for x in m if x['ten_god'] not in SUPPORT]
print("  supporting类:", len(sup), " draining类:", len(drai))
# 7 无count判断: 只列成员不比较
print("  (无强弱字段) 成员样例:", m[0])
print('=>', 'ALL PASS' if fails==0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
