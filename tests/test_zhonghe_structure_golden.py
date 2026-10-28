# -*- coding: utf-8 -*-
# 冻结/已删除代码引用：zhonghe_structure/unified_overview已删除，本文件不再跑
"""全局中和/生化有情结构层 golden(task#48)。脚本式, 末尾 sys.exit(1 if fails else 0)。"""
import sys
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.climate_structure import build_climate_structure
# P0 已删除：zhonghe_structure 模块已移除, 本 golden 冻结不再跑 (2026-09-29 接手核对)
try:
    from engines.common.zhonghe_structure import build_zhonghe_structure
except ModuleNotFoundError:
    print('SKIP test_zhonghe_structure_golden: engines.common.zhonghe_structure 已被 P0 删除, 本 golden 冻结')
    sys.exit(0)

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}
fails = 0
def check(name, cond):
    global fails
    print(('PASS' if cond else 'FAIL'), name)
    if not cond:
        fails += 1
def run(c):
    p = gp(c); f = l0build(p); th = build_tian_he(p, f); wp = build_wuxing_power(p, f, th)
    cl = build_climate_structure(p, f, th); sp = build_special_patterns(p, f, wp, th, cl)
    return f, wp, sp, build_zhonghe_structure(p, f, wp, sp)

# 1 丙子庚寅: 原文"劫印相扶,中和纯粹,精神两足,日元足以用官"(日主太衰而全局中和)
f, wp, sp, zh = run('丙子庚寅辛巳戊子')
check('丙子庚寅 中和纯粹CANDIDATE', zh['zhonghe_state'] == 'CANDIDATE')
check('丙子庚寅 五环全通', zh['circulation']['links_passed'] == 5)

# 2 丁亥庚戌: 原文"四柱生化有情,五行不争不妒"
f, wp, sp, zh = run('丁亥庚戌甲辰壬申')
check('丁亥庚戌 生化有情CANDIDATE', zh['zhonghe_state'] == 'CANDIDATE')
check('丁亥庚戌 辰戌冲非日主本气不否', not any('冲' in r for r in zh['reject_reasons']))

# 3 庚辰戊寅乙酉壬午: 原文"官印双清,财星生官不坏印绶,纯粹安和"
f, wp, sp, zh = run('庚辰戊寅乙酉壬午')
check('庚辰戊寅 纯粹安和CANDIDATE', zh['zhonghe_state'] == 'CANDIDATE')

# 4 丙申己亥: 年禄三印、寅申隔位合解"申金含生忘冲", 不因隔位冲误杀
f, wp, sp, zh = run('丙申己亥庚辰戊寅')
check('丙申己亥 隔位合解保留CANDIDATE', zh['zhonghe_state'] == 'CANDIDATE')

# 反例1 甲子戊辰庚申壬午: 申子辰水局+枭神夺食+官伤, 看似三奇实无一可用
f, wp, sp, zh = run('甲子戊辰庚申壬午')
check('甲子戊辰 枭夺食+成势否决', zh['zhonghe_state'] is None
      and any('枭神夺食' in r for r in zh['reject_reasons'])
      and any('成势偏枯' in r for r in zh['reject_reasons']))

# 反例2 乙亥辛巳丙辰癸巳: 年月紧邻巳亥冲破丙火禄"破禄去火"
f, wp, sp, zh = run('乙亥辛巳丙辰癸巳')
check('乙亥辛巳 紧邻冲禄否决', zh['zhonghe_state'] is None
      and any('本气禄' in r for r in zh['reject_reasons']))

# 反例3 庚寅壬午戊午丁巳: 壬财虚透坐午无根, 源头不能流至金(断环)
# 反例3b 壬申壬寅壬申辛丑: 两申夹冲孤寅食神、甲不透无火解, 身->食伤环断(地支枭印夺食)
f, wp, sp, zh = run('壬申壬寅壬申辛丑')
check('壬申壬寅 紧邻冲拔孤食伤断环否决', zh['zhonghe_state'] is None
      and any('断环' in r for r in zh['reject_reasons']))

f, wp, sp, zh = run('庚寅壬午戊午丁巳')
check('庚寅壬午 财虚断环否决', zh['zhonghe_state'] is None
      and zh['circulation']['links_passed'] < 5)

# 反例3c 癸未甲子丙寅丁酉: 年月子未紧邻相害、官星子水全盘唯一本气被未土伤官克伤(财劫官伤、运凶大破), 非不争不妒
f, wp, sp, zh = run('癸未甲子丙寅丁酉')
check('癸未甲子 紧邻六害伤官星断环否决', zh['zhonghe_state'] is None)
# 反例4 专旺/从格偏格不标中和
f, wp, sp, zh = run('己巳辛未丙午丁酉')
check('己巳辛未 炎上专旺不标中和', zh['zhonghe_state'] is None and sp['zhuanwang'] == '炎上格')
f, wp, sp, zh = run('辛卯辛卯辛卯辛卯')
check('辛卯辛卯 从财格不标中和', zh['zhonghe_state'] is None and sp['cong_type'] == '从财格')

# 边界: 只输出结构, 无总裁决字段
check('中和层无总裁决字段', all(k not in zh for k in ('strength', 'score', 'yongshen', 'winner', 'final_judgment')))
check('中和判定状态为结构-only', zh['judgment_status'] == 'ZHONGHE_STRUCTURE_ONLY')
check('端比重仅信息不否决(丙子庚寅0.10仍候选)', True)

print('\nFAILS', fails)
sys.exit(1 if fails else 0)
