# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json,re,collections
MAIN=r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴.jsonl"
BARE=r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴_bare.jsonl"
def load(p):
    o=[]
    for line in open(p,encoding="utf-8"):
        line=line.strip()
        if line:o.append(json.loads(line))
    return o
rows=load(MAIN)+load(BARE)
def parse_bazi(b): return [x for x in re.split(r"[\s,，、]+",(b or "").strip()) if x]
NAME2BR={"正月":"寅","二月":"卯","三月":"辰","四月":"巳","五月":"午","六月":"未","七月":"申","八月":"酉","九月":"戌","十月":"亥","十一月":"子","十二月":"丑"}

# strip lunar dates: <month>...日  e.g. 正月三十日 / 十一月廿八日
lunar_re=re.compile(r"(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)[初一二三四五六七八九十廿十百0-9]{1,4}日")
# cut appended general theory
cut_re=re.compile(r"(总论|总之|用法之别|看法，分为三节|附于)")

def case_specific(ana):
    t=ana
    # cut at first general-theory marker
    m=cut_re.search(t)
    if m: t=t[:m.start()]
    # remove lunar dates
    t=lunar_re.sub("",t)
    return t

res=[]
for r in rows:
    bazi=r["bazi"]; p=parse_bazi(bazi)
    if len(p)!=4: continue
    bbr=p[1][-1]
    cs=case_specific(r["analysis"])
    # explicit solar-month mentions in case-specific text
    mentioned={br for nm,br in NAME2BR.items() if nm in cs}
    # strong season words
    strong={"仲春":"卯","仲夏":"午","仲秋":"酉","仲冬":"子"}
    bad=[]
    for nm,br in NAME2BR.items():
        if nm in cs and br!=bbr:
            bad.append(f"月份{nm}({br})")
    for wk,br in strong.items():
        if wk in cs and br!=bbr:
            bad.append(f"{wk}={br}")
    if bad:
        res.append((r["case_id"],bazi,f"bazi月={bbr}",bad,cs[:80].replace("\n"," ")))

print("REFINED month conflicts:",len(res))
for x in res: print("  ",x)
