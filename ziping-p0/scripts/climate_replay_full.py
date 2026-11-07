import sys,json,glob,re,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
from cheng_bai import compute_cheng_bai
import importlib.util
spec=importlib.util.spec_from_file_location("cbc","scripts/climate_bing_check.py")
# 不执行其main: 手动读T
src=open("scripts/climate_bing_check.py",encoding="utf-8-sig").read()
ns={}; 
head=src.split("seen=set()")[0]
exec(head,ns)
T=ns["T"]
def rclass(out,gan):
    stems=[out["pillars"][p][0] for p in ["year","month","day","hour"]]
    mz=out["pillars"]["month"][1]
    hidden=out["l0_chart"]["hidden_stems"]
    ben=[hidden[p]["main"] for p in ["year","month","day","hour"]]
    def strong(tg):
        if any(s==tg for s in [stems[0],stems[1],stems[3]]):return True
        if any(b==tg for b in ben):return True
        return False
    main,aux=T[gan][mz]
    if strong(main):return 0
    if any(strong(a) for a in aux):return 1
    return 2
# 气候事件正则
RE_HAN=re.compile(r"(寒|冻|凝|冷)")
RE_ZAO=re.compile(r"(火炎|土燥|焦|炎燥|燥烈|过燥|炎上)")
RE_SHI=re.compile(r"(水泛|过湿|湿滞|水潦|泛溢|湿泥)")
RE_YP=re.compile(r"(得[丙癸壬]|[丙癸壬]透|用[丙癸壬]|丙暖|壬济|癸润|逢[丙癸壬])")
RE_YA=re.compile(r"(无[丙癸壬]|乏[丙癸壬]|不见[丙癸壬]|少[丙癸壬]|无火暖|无水润)")
SUIYUN=re.compile(r"(行.运|大运|流年|交.年|岁运|运至|运逢|交运)")
YUANJU=re.compile(r"(格|官|煞|杀|财|印|食|伤|身弱|身旺|根|令|寒|暖|燥|湿)")
seen=set();rows=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen or d.get("label") not in ("good","bad"):continue
        seen.add(cid)
        try:out=paipan(d["bazi"])
        except Exception:rows.append((cid,d["label"],None,-1,"",""));continue
        gan=out["pillars"]["day"][0]
        cb=compute_cheng_bai(out.get("raw_facts",{}).get("ge_cheng"))
        rc=rclass(out,gan) if cb!="SPECIAL_PASS" else -2
        txt=(d.get("raw") or "")+" "+(d.get("analysis") or "")
        rows.append((cid,d["label"],cb,rc,txt,gan))
print("总",len(rows))
# A 六态
cc=collections.Counter(x[2] for x in rows)
print("六态:",dict(cc))
# B 岁运识别(bad, 含岁运词 且 无原局病机关键词)
sui=set()
for cid,lab,cb,rc,txt,gan in rows:
    if lab!="bad":continue
    if SUIYUN.search(txt) and not YUANJU.search(txt):
        sui.add(cid)
print("规则识别纯岁运bad:",len(sui))
# C 气候事件回放(非从专, 非岁运)
ev=collections.Counter()
for cid,lab,cb,rc,txt,gan in rows:
    if rc<0:continue
    han=bool(RE_HAN.search(txt));zao=bool(RE_ZAO.search(txt));shi=bool(RE_SHI.search(txt))
    yp=bool(RE_YP.search(txt));ya=bool(RE_YA.search(txt))
    if han:ev["han"]+=1
    if zao:ev["zao"]+=1
    if shi:ev["shi"]+=1
    # 调候在局/缺 vs 引擎rc
    if yp:
        ev["yp_total"]+=1
        if rc==0:ev["yp_hit"]+=1
        else:ev["yp_miss"]+=1
    if ya:
        ev["ya_total"]+=1
        if rc==2:ev["ya_hit"]+=1
        else:ev["ya_conflict"]+=1
print("气候断语事件: 寒%d 燥%d 湿%d"%(ev["han"],ev["zao"],ev["shi"]))
print("断语称调候在局 n=%d 引擎r0命中=%d 漏=%d (命中率%.1f%%)"%(ev["yp_total"],ev["yp_hit"],ev["yp_miss"],100*ev["yp_hit"]/ev["yp_total"] if ev["yp_total"] else 0))
print("断语称调候缺 n=%d 引擎r2命中=%d 反向冲突=%d (命中率%.1f%%)"%(ev["ya_total"],ev["ya_hit"],ev["ya_conflict"],100*ev["ya_hit"]/ev["ya_total"] if ev["ya_total"] else 0))
# D 口径甲(剔识别岁运)
core=[x for x in rows if x[3]>=0 and x[0] not in sui]
sick=[x for x in core if x[3]==2]
print("口径甲(剔岁运%d) 非从专=%d 气候病=%d (%.1f%%)"%(len(sui),len(core),len(sick),100*len(sick)/len(core)))

