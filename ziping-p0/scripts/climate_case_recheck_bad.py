import sys,json,glob,re
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
from cheng_bai import compute_cheng_bai
src=open("scripts/climate_bing_check.py",encoding="utf-8-sig").read()
ns={};exec(src.split("seen=set()")[0],ns);T=ns["T"]
def rclass(out,gan):
    stems=[out["pillars"][p][0] for p in ["year","month","day","hour"]]
    hidden=out["l0_chart"]["hidden_stems"];ben=[hidden[p]["main"] for p in ["year","month","day","hour"]]
    strong=lambda t:any(s==t for s in [stems[0],stems[1],stems[3]]) or any(b==t for b in ben)
    main,aux=T[gan][out["pillars"]["month"][1]]
    return 0 if strong(main) else (1 if any(strong(a) for a in aux) else 2)
PERMIT=re.compile(r"(无癸亦可|无癸不碍|无癸?[亦]?可)")
GT_YA=re.compile(r"(无丙|乏癸|无癸|不见壬|无壬|少丙|无火暖|无水润|无向阳|孤阳|独阳不长)")
GT_YP=re.compile(r"(寒木向阳|得丙暖|丙癸两透|得丙|得癸|向阳|丙火?[暖照]|既济)")
seen=set();bad=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen or d.get("label")!="bad":continue
        seen.add(cid)
        try:out=paipan(d["bazi"])
        except:continue
        gan=out["pillars"]["day"][0]
        if compute_cheng_bai(out.get("raw_facts",{}).get("ge_cheng"))=="SPECIAL_PASS":continue
        rc=rclass(out,gan);txt=((d.get("raw") or "")+" "+(d.get("analysis") or ""))
        bad.append((cid,rc,txt))
ya=[x for x in bad if GT_YA.search(x[2]) and not PERMIT.search(x[2])]
yp=[x for x in bad if GT_YP.search(x[2])]
print("bad非从专盘",len(bad))
print("GT缺 n=%d r2命中=%d recall=%.1f%%"%(len(ya),sum(1 for x in ya if x[1]==2),100*sum(1 for x in ya if x[1]==2)/len(ya)))
print("GT在局 n=%d r0命中=%d recall=%.1f%%"%(len(yp),sum(1 for x in yp if x[1]==0),100*sum(1 for x in yp if x[1]==0)/len(yp)))
for cid,rc,txt in ya:
    if rc!=2:
        m=GT_YA.search(txt);print("【%s r%d】%s"%(cid,rc,txt[max(0,m.start()-22):m.end()+22].replace(chr(10),"")))
