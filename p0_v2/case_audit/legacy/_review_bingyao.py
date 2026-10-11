# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""深度抽查: 病药逻辑 + 诗诀散文一致性"""
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
STEM2EL = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
BR_HIDDEN = {
 "子":[("癸",1.0)],"丑":[("己",1.0),("癸",0.5),("辛",0.3)],
 "寅":[("甲",1.0),("丙",0.5),("戊",0.3)],"卯":[("乙",1.0)],
 "辰":[("戊",1.0),("乙",0.5),("癸",0.3)],"巳":[("丙",1.0),("戊",0.5),("庚",0.3)],
 "午":[("丁",1.0),("己",0.5)],"未":[("己",1.0),("丁",0.5),("乙",0.3)],
 "申":[("庚",1.0),("壬",0.5),("戊",0.3)],"酉":[("辛",1.0)],
 "戌":[("戊",1.0),("辛",0.5),("丁",0.3)],"亥":[("壬",1.0),("甲",0.5)],
}
def pillars(b): return [p for p in re.split(r'\s+', (b or '').strip()) if p]
def strength(bs):
    sc=collections.Counter()
    for p in bs:
        sc[STEM2EL[p[0]]]+=1.0
        for h,w in BR_HIDDEN[p[1]]: sc[STEM2EL[h]]+=w
    return sc

# 1. 所有含"病"或"药"的命例
print('########## 含病/药的命例 ##########')
for c in cases:
    a = c.get('analysis','')
    if '病' in a or '药' in a:
        bs = pillars(c['bazi'])
        sc = strength(bs)
        top = sorted(sc.items(), key=lambda x:-x[1])
        print('='*60)
        print(c['case_id'], c['bazi'], '| 日干', bs[2][0], '| 五行力:', {k:round(v,1) for k,v in top})
        print(a)
