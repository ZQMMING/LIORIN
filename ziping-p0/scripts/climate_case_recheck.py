import sys,json,glob,re,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
from cheng_bai import compute_cheng_bai
src=open("scripts/climate_bing_check.py",encoding="utf-8-sig").read()
ns={};exec(src.split("seen=set()")[0],ns);T=ns["T"]
def rclass(out,gan):
    stems=[out["pillars"][p][0] for p in ["year","month","day","hour"]]
    hidden=out["l0_chart"]["hidden_stems"]
    ben=[hidden[p]["main"] for p in ["year","month","day","hour"]]
    def strong(t):return any(s==t for s in [stems[0],stems[1],stems[3]]) or any(b==t for b in ben)
    main,aux=T[gan][out["pillars"]["month"][1]]
    if strong(main):return 0
    if any(strong(a) for a in aux):return 1
    return 2
# 收紧 ground truth
PERMIT=re.compile(r"(无癸亦可|无癸不碍|无癸?[亦]?可)")
GT_YA=re.compile(r"(无丙|乏癸|无癸|不见壬|无壬|少丙|无火暖|无水润|寒木无向阳|无向阳|孤阳|独阳不长)")
GT_YP=re.compile(r"(寒木向阳|得丙暖|丙透暖|丙癸两透|癸透润|壬透济|得丙|得癸|向阳|丙火?[暖照]|水火既济)")
GT_HAN=re.compile(r"(金寒水冷|金水寒凝|寒.*无火|冻.*无暖|寒凝)")
GT_ZAO=re.compile(r"(火炎土燥|土焦|火炎|燥烈无水|过燥)")
seen=set();rows=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen or d.get("label") not in ("good","bad"):continue
        seen.add(cid)
        try:out=paipan(d["bazi"])
        except:continue
        gan=out["pillars"]["day"][0]
        cb=compute_cheng_bai(out.get("raw_facts",{}).get("ge_cheng"))
        if cb=="SPECIAL_PASS":continue
        rc=rclass(out,gan)
        txt=((d.get("raw") or "")+" "+(d.get("analysis") or ""))
        rows.append((cid,d["label"],rc,txt))
print("非从专label盘",len(rows)," 引擎r2(main缺)输出:",sum(1 for x in rows if x[2]==2))
# ground truth 事件(排除变格许可)
ya=[];yp=[];han=[];zao=[]
for cid,lab,rc,txt in rows:
    if GT_YA.search(txt) and not PERMIT.search(txt):ya.append((cid,lab,rc))
    if GT_YP.search(txt):yp.append((cid,lab,rc))
    if GT_HAN.search(txt):han.append((cid,lab,rc))
    if GT_ZAO.search(txt):zao.append((cid,lab,rc))
def rep(name,g,goodr):
    hit=sum(1 for x in g if x[2]==goodr);n=len(g)
    print("%s n=%d 引擎符合=%d 命中率(recall)=%.1f%% 漏=%d"%(name,n,hit,100*hit/n if n else 0,n-hit))
    return g
rep("GT 调候缺",ya,2)
rep("GT 调候在局",yp,0)
rep("GT 寒成病",han,2)
rep("GT 燥成病",zao,2)
# 漏判清单(GT缺但引擎非r2)
miss=[x for x in ya if x[2]!=2]
print("\n未覆盖(断语称缺引擎未判) %d:"%len(miss))
for x in miss:print(" ",x[0],x[1],"r%d"%x[2])
conf=[x for x in yp if x[2]!=0]
print("反向冲突(断语称在局引擎判缺) %d:"%len(conf))
for x in conf[:20]:print(" ",x[0],x[1],"r%d"%x[2])
