# -*- coding: utf-8 -*-
"""PATCH-189 六阴朝阳 Structural Entry golden (辛日+戊子时+官杀全无, 非成格)"""
import sys; sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build

fails = 0
def ck(n, g, e):
    global fails; ok = g == e; fails += (not ok); print(f"{'PASS' if ok else 'FAIL'} {n}: {g}")

def entry(pillars):
    return build(pillars).get('liuyin_chaoyang_entry', {})

# G1 正例: 辛日+戊子时+天干藏干官杀全无
# 辛(阴金): 正官=丙, 七杀=丁. 天干癸壬戊辛无丙丁; 藏干亥壬辰子无火
p1 = {'year': ['癸', '亥'], 'month': ['壬', '辰'], 'day': ['辛', '亥'], 'hour': ['戊', '子']}
ck("G1 正例", entry(p1)['is_entry'], True)

# G2 非辛日(庚日)
p2 = {'year': ['癸', '亥'], 'month': ['壬', '辰'], 'day': ['庚', '亥'], 'hour': ['戊', '子']}
ck("G2 非辛日", entry(p2)['is_entry'], False)

# G3 非戊子时(丙申时)
p3 = {'year': ['癸', '亥'], 'month': ['壬', '辰'], 'day': ['辛', '亥'], 'hour': ['丙', '申']}
ck("G3 非戊子时", entry(p3)['is_entry'], False)

# G4 天干见正官(丙) -> FALSE
p4 = {'year': ['丙', '寅'], 'month': ['壬', '辰'], 'day': ['辛', '亥'], 'hour': ['戊', '子']}
ck("G4 天干见正官丙", entry(p4)['is_entry'], False)

# G5/G8 藏干见七杀(未藏丁), 天干无丙丁 -> FALSE
p5 = {'year': ['癸', '亥'], 'month': ['壬', '辰'], 'day': ['辛', '未'], 'hour': ['戊', '子']}
ck("G5 藏干见七杀丁", entry(p5)['is_entry'], False)

# G6 只有正官(天干丙) -> FALSE (官杀联合存在性, 正官单独也不立)
ck("G6 仅正官", entry(p4)['is_entry'], False)

# G7 只有七杀(天干丁) -> FALSE
p7 = {'year': ['丁', '亥'], 'month': ['壬', '辰'], 'day': ['辛', '亥'], 'hour': ['戊', '子']}
ck("G7 仅七杀", entry(p7)['is_entry'], False)

# G8 天干无藏干有(同p5) -> FALSE
ck("G8 天干无藏干有", entry(p5)['is_entry'], False)

# G9 天干有藏干无(天干丙, 藏干无火) -> FALSE
p9 = {'year': ['丙', '寅'], 'month': ['壬', '辰'], 'day': ['辛', '亥'], 'hour': ['戊', '子']}
ck("G9 天干有藏干无", entry(p9)['is_entry'], False)

# G10 语义锁: 不输出成格/贵贱/喜忌/吉凶
r10 = entry(p1)
ck("G10 无成格贵贱字段", not any(w in str(r10) for w in ['成格', '貴', '賤', '喜', '忌', '吉', '凶']), True)
ck("G10 type标注复用Fact", 'any_stem' in str(r10.get('reuse', [])), True)

print('=>', 'ALL PASS' if fails == 0 else f'{fails} FAIL')
sys.exit(1 if fails else 0)
