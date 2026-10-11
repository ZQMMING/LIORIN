# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""QTBJ 五关验证 - 终版"""
import json, re, collections, os

MAIN = r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴.jsonl"
BARE = r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴_bare.jsonl"
OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"

def load(p):
    o=[]
    with open(p,encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: o.append(json.loads(line))
    return o

rows = load(MAIN) + load(BARE)

def parse_bazi(b):
    return [x for x in re.split(r"[\s,，、]+",(b or "").strip()) if x]

YANG_STEM=set("甲丙戊庚壬"); YIN_STEM=set("乙丁己辛癸")
YANG_BR=set("子寅辰午申戌"); YIN_BR=set("丑卯巳未酉亥")
def parity_ok(p):
    if len(p)!=2: return False
    s,b=p[0],p[1]
    return (s in YANG_STEM and b in YANG_BR) or (s in YIN_STEM and b in YIN_BR)

# ordered longest-first to avoid 十二月->二月 substring bug
MONTHS=[("十二月","丑"),("十一月","子"),("十月","亥"),("九月","戌"),("八月","酉"),
        ("七月","申"),("六月","未"),("五月","午"),("四月","巳"),("三月","辰"),
        ("二月","卯"),("正月","寅")]

def norm(s): return re.sub(r"\s+","",s or "")

# pollution markers
POLLUTION_PATTERNS = {
    "徐乐吾评注": r"徐乐吾曰",
    "坊本抄本异文": r"坊本|抄本",
    "OCR/传抄讹字": r"廿力|拾月|木喜南而软弱|断凿|楝梁|墓春",
}

# cross-ref / non-birth-month contexts to EXCLUDE when judging month conflict
def strip_nonbirth(t):
    # lunar dates: <month><date chars>日
    t = re.sub(r"(十二月|十一月|十月|正月|二月|三月|四月|五月|六月|七月|八月|九月)[初一二三四五六七八九十廿百0-9]{1,4}日","",t)
    # cross references to other sections
    t = re.sub(r"[参阅参观][^，。；]{0,8}节","",t)
    t = re.sub(r"见上[^，。；]{0,8}节","",t)
    t = re.sub(r"见首节|见首[^，。；]{0,6}节","",t)
    t = re.sub(r"与[正二三四五六七八九十冬腊]{1,4}[月同论同看]?","",t)
    t = re.sub(r"[正二三四五六七八九十冬腊]月[甲乙丙丁戊己庚辛壬癸]节命例","",t)  # next-section header
    t = re.sub(r"[正二三四五六七八九十]月[甲乙丙丁戊己庚辛壬癸]?节[^，。]{0,10}","",t)
    # luck pillars / death dates / taiyuan
    t = re.sub(r"[寅卯辰巳午未申酉戌亥子丑]运","",t)
    t = re.sub(r"胎元","",t)
    return t

res=[]
for r in rows:
    bid=r["case_id"]; bazi=r["bazi"]; p=parse_bazi(bazi)
    raw=r.get("raw",""); ana=r.get("analysis","")
    reasons=[]; pollution=[]; doubt=[]

    # G1
    if len(p)!=4:
        reasons.append("八字错:四柱数=%d"%len(p))
    else:
        for pil in p:
            if not parity_ok(pil):
                reasons.append("八字错:干支不合%s"%pil)

    nb=norm(bazi); nr=norm(raw); na=norm(ana)
    # G2
    if nb and nb not in nr: reasons.append("原文拼接:bazi不在raw")
    if na and na not in nr: reasons.append("原文拼接:analysis不在raw")

    # G3 month
    if len(p)==4:
        bbr=p[1][-1]
        cs=strip_nonbirth(ana) or strip_nonbirth(raw)
        # find first (longest-first) month mention that differs
        mentioned=set()
        for nm,br in MONTHS:
            if nm in cs: mentioned.add(br)
        mentioned.discard(bbr)
        # strong single-season words
        for wk,br in [("仲春","卯"),("仲夏","午"),("仲秋","酉"),("仲冬","子")]:
            if wk in cs: mentioned.discard(br)
        if mentioned:
            doubt.append("月份存疑:analysis提及%s但bazi月支=%s"%("".join(sorted(mentioned)),bbr))

    # G3c: analysis contains another full bazi
    if re.search(r"(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}", ana) and nb not in norm(ana):
        # allow if it's '一命、XXXX' referring to THIS chart
        others=[c for c in re.findall(r"(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}",ana) if norm(c)!=nb]
        if others:
            reasons.append("断语串位:analysis含他造bazi%s"%others[0])

    # G4 pollution
    for tag,pat in POLLUTION_PATTERNS.items():
        if re.search(pat, raw+ana): pollution.append(tag)

    # verdict
    if reasons:
        verdict="reject"; cat=reasons[0].split(":")[0]
    elif doubt:
        verdict="doubt"; cat="存疑"
    else:
        verdict="pass"; cat="通过"

    res.append({**r, "verdict":verdict, "verdict_cat":cat,
                "pass_reason":"; ".join(reasons+doubt),
                "pollution":pollution})

# summary
cnt=collections.Counter(x["verdict"] for x in res)
catcnt=collections.Counter(x["verdict_cat"] for x in res)
print("VERDICT:",dict(cnt))
print("CATS:",dict(catcnt))

print("\n--- REJECTS ---")
for x in res:
    if x["verdict"]=="reject":
        print("  ",x["case_id"],x["bazi"],"|",x["pass_reason"])
print("\n--- DOUBTS ---")
for x in res:
    if x["verdict"]=="doubt":
        print("  ",x["case_id"],x["bazi"],"|",x["pass_reason"])

# named people extraction (G5 sample)
names=re.findall(r"[\u4e00-\u9fa5]{2,6}(?=命[，,])", "".join(r["analysis"] for r in rows))
names2=re.findall(r"曰[:：]?([一-龥]{2,8}?)命", "".join(r["analysis"] for r in rows))
print("\nNamed people hits sample:", list(set(names+names2))[:40])

# write clean.jsonl (pass+doubt)
os.makedirs(OUTDIR,exist_ok=True)
with open(os.path.join(OUTDIR,"QTBJ_clean.jsonl"),"w",encoding="utf-8") as f:
    for x in res:
        f2={k:v for k,v in x.items() if k in ("line_no","bazi","dayun","raw","analysis","case_id","book","verdict","pass_reason","pollution")}
        f.write(json.dumps(f2,ensure_ascii=False)+"\n")
print("\nwrote QTBJ_clean.jsonl")
