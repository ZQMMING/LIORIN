"""三合 4×N 矩阵: 4组 × 8判据 逐格盘数 + 三支齐案例断语。"""
import json,glob,re,sys
GAN_WX={"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
JU={"申子辰":"水","亥卯未":"木","寅午戌":"火","巳酉丑":"金"}
CHONG={"子":"午","午":"子","卯":"酉","酉":"卯","寅":"申","申":"寅","巳":"亥","亥":"巳","辰":"戌","戌":"辰","丑":"未","未":"丑"}
LIUHE=[set("子丑"),set("寅亥"),set("卯戌"),set("辰酉"),set("巳申"),set("午未")]
rows=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f,encoding="utf-8"):
        d=json.loads(l);bz=d.get("bazi") or ""
        g=re.findall(r"[甲乙丙丁戊己庚辛壬癸]",bz); z=re.findall(r"[子丑寅卯辰巳午未申酉戌亥]",bz)
        if len(g)==4 and len(z)==4: rows.append((d["case_id"],g,z,d.get("label")))
raw={}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f,encoding="utf-8"):
        d=json.loads(l);raw[d["case_id"]]=d

def cell(jstr,hua):
    js=set(jstr)
    full=[r for r in rows if js.issubset(set(r[2]))]
    pairs=[set(jstr[i:j]) for i,j in [(0,1),(1,2),(0,2)]]
    half=[r for r in rows if not js.issubset(set(r[2])) and any(p.issubset(set(r[2])) for p in pairs)]
    tou=[r for r in full if any(GAN_WX[x]==hua for x in r[1])]
    ling=[r for r in full if r[2][1] in js]
    yuchong=[r for r in full if any(CHONG.get(b) in set(r[2]) for b in js)]
    yuliuhe=[]
    for r in full:
        zs=set(r[2])
        if any({b,o} in LIUHE for b in js for o in zs): yuliuhe.append(r)
    return full,half,tou,ling,yuchong,yuliuhe

print("%-8s %6s %6s %6s %6s %6s %8s  化神"%("组","三支齐","半合","透化神","月令","遇冲","遇六合"))
allex={}
for j,h in JU.items():
    full,half,tou,ling,yc,yl=cell(j,h); allex[j]=full
    print("%-8s %6d %6d %6d %6d %6d %8d   %s"%(j,len(full),len(half),len(tou),len(ling),len(yc),len(yl),h))
for j in JU:
    print("== %s 三支齐案例(前6) =="%j)
    for cid,g,z,lb in allex[j][:6]:
        t=(raw[cid].get("raw") or "").replace("\n"," ")
        sents=[s for s in re.split(r"[。；]",t) if len(s)>10]
        print("  %s label=%s | %s"%(cid,lb,(sents[0][:64] if sents else "")))
