# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, collections

CANON = r"D:\shuntian\data\classics\canonical\QTBJ_穷通宝鉴.txt"
JSONL = r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴.jsonl"

with open(CANON, encoding="utf-8") as f:
    canon = f.read().split("\n")   # canon[i] line i+1

MONTH2BR = {"正月":"寅","二月":"卯","三月":"辰","四月":"巳","五月":"午","六月":"未",
            "七月":"申","八月":"酉","九月":"戌","十月":"亥","十一月":"子","十二月":"丑"}
STEMS = "甲乙丙丁戊己庚辛壬癸"
hdr_re = re.compile(r"^(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)([" + STEMS + r"])")

# section boundaries (line_no, month_branch, day_stem)
sections=[]
for idx,line in enumerate(canon,1):
    m=hdr_re.match(line.strip())
    if m:
        sections.append((idx, MONTH2BR[m.group(1)], m.group(2)))

def section_at(lineno):
    best=None
    for s in sections:
        if s[0]<=lineno: best=s
        else: break
    return best

# normalize: strip whitespace + separator punct for matching
SEPS = " \t　、。，,；;：:（）()\n\r"
def norm(s):
    return "".join(ch for ch in s if ch not in SEPS)

# per-line normalized canonical
norm_lines=[norm(l) for l in canon]

rows=[]
with open(JSONL, encoding="utf-8") as f:
    for line in f:
        line=line.strip()
        if line: rows.append(json.loads(line))

def parse_bazi(b):
    return [p for p in re.split(r"[\s,，、]+", b.strip()) if p]

YANG_STEM=set("甲丙戊庚壬"); YIN_STEM=set("乙丁己辛癸")
YANG_BR=set("子寅辰午申戌"); YIN_BR=set("丑卯巳未酉亥")
def parity_ok(p):
    s,b=p[0],p[1]
    return (s in YANG_STEM and b in YANG_BR) or (s in YIN_STEM and b in YIN_BR)

# locate bazi in canonical
def locate(norm_bazi):
    hits=[]
    for i,nl in enumerate(norm_lines,1):
        if norm_bazi and norm_bazi in nl:
            hits.append(i)
    return hits

month_mis=[]; stem_mis=[]; not_found=[]; results=[]
for r in rows:
    bid=r["case_id"]; p=parse_bazi(r["bazi"])
    flags=[]
    # G1
    if len(p)!=4:
        flags.append(("八字错",f"四柱数{len(p)}"))
    else:
        for pil in p:
            if len(pil)!=2 or not parity_ok(pil):
                flags.append(("八字错",f"干支不合{pil}"))
    # locate
    nb=norm(r["bazi"])
    hits=locate(nb)
    sec=None
    if not hits:
        not_found.append((bid,r["bazi"]))
        flags.append(("其他","canonical未定位到bazi"))
    else:
        sec=section_at(hits[0])
        if len(p)==4:
            bbr=p[1][-1]; bstem=p[3][0]
            sbr,ssem=sec[1],sec[2]
            if bbr!=sbr:
                month_mis.append((bid,r["bazi"],f"bazi月支{bbr}",f"章节{sbr}",f"canon行{hits[0]}"))
                flags.append(("月份错配",f"{bbr}vs{sbr}@行{hits[0]}"))
            if bstem!=ssem:
                stem_mis.append((bid,r["bazi"],f"日干{bstem}",f"章节日干{ssem}",f"canon行{hits[0]}"))
                flags.append(("断语串位",f"日干{bstem}vs{ssem}@行{hits[0]}"))
    results.append((bid,r["bazi"],hits[0] if hits else None,flags))

print("TOTAL:",len(rows))
print("NOT FOUND in canonical:",len(not_found))
for x in not_found[:20]: print("   ",x)
print("\nMONTH MISMATCH:",len(month_mis))
for x in month_mis: print("   ",x)
print("\nDAY-STEM MISMATCH:",len(stem_mis))
for x in stem_mis: print("   ",x)

# how many fully clean so far
clean=[r for r in results if not r[3]]
print("\nNO FLAGS (G1+G3):",len(clean))
