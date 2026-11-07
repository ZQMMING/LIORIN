import sys,json,glob,re,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
from cheng_bai import compute_cheng_bai
src=open("scripts/climate_bing_check.py",encoding="utf-8-sig").read()
ns={};exec(src.split("seen=set()")[0],ns);T=ns["T"]
WINTER={"亥","子","丑"}
def rclass(out,gan):
    stems=[out["pillars"][p][0] for p in ["year","month","day","hour"]]
    hidden=out["l0_chart"]["hidden_stems"];ben=[hidden[p]["main"] for p in ["year","month","day","hour"]]
    strong=lambda t:any(s==t for s in [stems[0],stems[1],stems[3]]) or any(b==t for b in ben)
    main,aux=T[gan][out["pillars"]["month"][1]]
    return 0 if strong(main) else (1 if any(strong(a) for a in aux) else 2)
DARK=re.compile(r"(缺[丙丁甲]|无[丙丁甲壬癸]|不见[丙丁甲]|乏[丙丁癸]|欠[丙丁]|不可无[丙丁甲]|非[丙丁甲]不[暖济]|无火|无阳)")
HOT=re.compile(r"(得[丙丁甲]|丙[暖照]|丁[暖照]|[丙丁甲][透出]|见[丙丁甲]|有[丙丁甲]|火[暖照]|得暖|向阳)")
seen=set();winter=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen or d.get("label")!="bad":continue
        seen.add(cid)
        try:out=paipan(d["bazi"])
        except:continue
        gan=out["pillars"]["day"][0];yue=out["pillars"]["month"][1]
        if yue not in WINTER:continue
        if compute_cheng_bai(out.get("raw_facts",{}).get("ge_cheng"))=="SPECIAL_PASS":continue
        rc=rclass(out,gan);txt=((d.get("raw") or "")+" "+(d.get("analysis") or ""))
        winter.append((cid,gan,yue,rc,T[gan][yue],txt))
print("冬月bad非从专盘 n=%d"%len(winter))
# 每格统计 + r1 断语是否支持"缺main凶"
bycell=collections.defaultdict(list)
for r in winter:bycell[(r[1],r[2])].append(r)
for cell in sorted(bycell,key=lambda c:(c[1],c[0])):
    rows=bycell[cell];rcs=collections.Counter(r[3] for r in rows)
    gan,yue=cell;main,aux=T[gan][yue]
    print("%s%s main=%s aux=%s | r0=%d r1=%d r2=%d"%(gan,yue,main,aux,rcs[0],rcs[1],rcs[2]))
# r1 盘(冬月main缺aux在)逐一dump断语看是否"缺main凶"
r1=[r for r in winter if r[3]==1]
print("\n冬月r1盘(main缺aux在) n=%d 逐盘断语:"%len(r1))
for cid,gan,yue,rc,cell,txt in r1:
    m=DARK.search(txt) or HOT.search(txt)
    frag="…%s…"%txt[max(0,(m.start()-18) if m else 0):(m.end()+18) if m else 40].replace("\n","") if m else txt[:40]
    print("%s %s%s | %s"%(cid,gan,yue,frag))
