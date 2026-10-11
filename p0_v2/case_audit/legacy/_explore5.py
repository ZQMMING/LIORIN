# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, collections

MAIN = r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴.jsonl"
BARE = r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴_bare.jsonl"

def load(p):
    out=[]
    with open(p,encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: out.append(json.loads(line))
    return out

rows = load(MAIN) + load(BARE)
print("TOTAL (main+bare):", len(rows))

def parse_bazi(b):
    return [p for p in re.split(r"[\s,，、]+", (b or "").strip()) if p]

YANG_STEM=set("甲丙戊庚壬"); YIN_STEM=set("乙丁己辛癸")
YANG_BR=set("子寅辰午申戌"); YIN_BR=set("丑卯巳未酉亥")
def parity_ok(p):
    if len(p)!=2: return False
    s,b=p[0],p[1]
    return (s in YANG_STEM and b in YANG_BR) or (s in YIN_STEM and b in YIN_BR)

# month branch <-> month name
BR2NAME={"寅":"正月","卯":"二月","辰":"三月","巳":"四月","午":"五月","未":"六月",
         "申":"七月","酉":"八月","戌":"九月","亥":"十月","子":"十一月","丑":"十二月"}
NAME2BR={"正月":"寅","二月":"卯","三月":"辰","四月":"巳","五月":"午","六月":"未",
         "七月":"申","八月":"酉","九月":"戌","十月":"亥","十一月":"子","十二月":"丑"}

# season words
SEASON={
 "春":set("寅卯辰"),"三春":set("寅卯辰"),"初春":set("寅卯辰"),"仲春":set("卯"),"春":set("寅卯辰"),
 "夏":set("巳午未"),"三夏":set("巳午未"),"初夏":set("巳午未"),"仲夏":set("午"),"夏月":set("巳午未"),"夏":set("巳午未"),
 "秋":set("申酉戌"),"三秋":set("申酉戌"),"初秋":set("申酉戌"),"仲秋":set("酉"),"秋月":set("申酉戌"),"秋":set("申酉戌"),
 "冬":set("亥子丑"),"三冬":set("亥子丑"),"初冬":set("亥子丑"),"仲冬":set("子"),"冬月":set("亥子丑"),"冬":set("亥子丑"),
}

def norm(s): return re.sub(r"\s+","",s or "")

bazi_not_in_raw=[]; month_conflict=[]; named_bazi_mismatch=[]; empty=[]
g1bad=[]; results=[]

for r in rows:
    bid=r.get("case_id"); bazi=r.get("bazi",""); p=parse_bazi(bazi)
    raw=r.get("raw",""); ana=r.get("analysis","")
    flags=[]
    # G1
    if len(p)!=4:
        g1bad.append((bid,bazi,f"四柱数{len(p)}"))
    else:
        for pil in p:
            if not parity_ok(pil):
                g1bad.append((bid,bazi,f"干支不合{pil}"))
    if len(p)==4:
        bbr=p[1][-1]; bstem=p[3][0]
    else:
        bbr=bstem=None

    # G2: bazi in raw (self-consistency); analysis substring raw
    nr=norm(raw); nb=norm(bazi); na=norm(ana)
    if nb and nb not in nr:
        bazi_not_in_raw.append((bid,bazi)); flags.append(("原文拼接","bazi不在raw中"))
    if na and na not in nr:
        flags.append(("原文拼接","analysis不在raw中"))

    # G3a month keyword conflict
    text = norm(ana) or norm(raw)
    # explicit month name mentions
    mentioned_months=set()
    for nm,br in NAME2BR.items():
        if nm in text:
            mentioned_months.add(br)
    if bbr and mentioned_months:
        if bbr not in mentioned_months:
            # only flag if analysis (not just raw) mentions a DIFFERENT specific month
            an=norm(ana)
            ana_months=set(br for nm,br in NAME2BR.items() if nm in an)
            if ana_months and bbr not in ana_months:
                month_conflict.append((bid,bazi,f"bazi月={bbr}",f"analysis提到={''.join(ana_months)}"))
                flags.append(("月份错配",f"{bbr}vs{ana_months}"))
    # season conflict (only strong: analysis explicitly says 仲春/仲夏/仲秋/仲冬 == single branch)
    strong_season={"仲春":"卯","仲夏":"午","仲秋":"酉","仲冬":"子","初春":"寅","初秋":"申","初冬":"亥","初夏":"巳"}
    for wk,br in strong_season.items():
        if wk in norm(ana) and bbr and bbr!=br:
            month_conflict.append((bid,bazi,f"bazi月={bbr}",f"analysis说{wk}={br}"))
            flags.append(("月份错配",f"analysis={wk}"))

    # G3c: named bazi in analysis like "如庚申一造" / "一命、XXXX" / "此造"
    # pattern: 4 consecutive pillars (8 chars) in analysis
    named=re.findall(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]{4,}", ana)
    # extract any 8-char bazi-like
    cand=re.findall(r"(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}", ana)
    for c in cand:
        # compare to record bazi (normalized)
        if norm(c)!=nb and nb:
            named_bazi_mismatch.append((bid,bazi,f"analysis含:{c}"))
            flags.append(("断语串位",f"analysis含他造{c}"))
            break

    if not ana.strip():
        empty.append((bid,bazi))

    results.append((bid,bazi,flags))

print("\nG1 八字错:",len(g1bad)); [print("  ",x) for x in g1bad[:20]]
print("\nG2 bazi不在raw:",len(bazi_not_in_raw)); [print("  ",x) for x in bazi_not_in_raw[:20]]
print("\nG3a 月份冲突:",len(month_conflict)); [print("  ",x) for x in month_conflict[:40]]
print("\nG3c analysis含他造bazi:",len(named_bazi_mismatch)); [print("  ",x) for x in named_bazi_mismatch[:30]]
print("\n空analysis(裸):",len(empty))
