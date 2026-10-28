# -*- coding: utf-8 -*-
"""PATCH-183 day_year_same / yun_year_same golden (纯结构, 不判吉凶)"""
import sys; sys.path.insert(0, '.')
from engines.common.relation_178 import yun_natal_relations

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

# 日柱 = 甲子
pillars = {'year': ['丙', '寅'], 'month': ['戊', '戌'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}

# G1 流年==日柱 -> day_year_same
r1 = yun_natal_relations({'year': ['甲', '子'], 'decade': ['壬', '申']}, pillars)
ck("G1 流年甲子==日柱甲子 -> day_year_same",
   any(x['relation'] == 'day_year_same' and x['semantic'] == '日年相并' for x in r1), True)

# G2 流年==大运 -> yun_year_same
r2 = yun_natal_relations({'year': ['壬', '申'], 'decade': ['壬', '申']}, pillars)
ck("G2 流年壬申==大运壬申 -> yun_year_same",
   any(x['relation'] == 'yun_year_same' and x['semantic'] == '岁运并临' for x in r2), True)

# G3 流年!=日柱 -> 无 day_year_same
r3 = yun_natal_relations({'year': ['乙', '丑'], 'decade': ['壬', '申']}, pillars)
ck("G3 流年乙丑!=日柱甲子 -> 无day_year_same",
   not any(x['relation'] == 'day_year_same' for x in r3), True)

# G4 流年!=大运 -> 无 yun_year_same
ck("G4 流年乙丑!=大运壬申 -> 无yun_year_same",
   not any(x['relation'] == 'yun_year_same' for x in r3), True)

# G5 两者同时相等 -> 两个独立relation同时存在
r5 = yun_natal_relations({'year': ['甲', '子'], 'decade': ['甲', '子']}, pillars)
rel5 = [x['relation'] for x in r5]
ck("G5 同时相等 -> day_year_same与yun_year_same独立并存",
   rel5.count('day_year_same') == 1 and rel5.count('yun_year_same') == 1, True)

# 锁死: 不产生伏吟/返吟/pressure_on_day/吉凶
ck("锁死 无伏吟/返吟/pressure_on_day",
   not any(x['relation'] in ('伏吟', '返吟', 'pressure_on_day') for x in r1 + r2 + r3 + r5), True)
ck("锁死 无吉凶字段(relation/semantic层)",
   not any(('吉' in str(x.get('relation','')) or '凶' in str(x.get('relation',''))
            or '吉' in str(x.get('semantic','')) or '凶' in str(x.get('semantic','')))
           for x in r1 + r2 + r3 + r5), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
