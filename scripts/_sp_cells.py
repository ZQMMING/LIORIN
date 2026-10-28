"""15格逐格对账数据: 每格(cong_type×cong_state)盘数+案例断语 + HUAQI/MUMIE 全盘断语。"""
import json,glob,re
d=json.load(open("scripts/_sp_audit.json",encoding="utf-8"))
raw={}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f,encoding="utf-8"):
        x=json.loads(l); raw[x["case_id"]]=x
def sent(cid,n=1):
    t=(raw.get(cid,{}).get("raw") or "").replace("\n"," ")
    s=[x for x in re.split(r"[。；]",t) if len(x)>8]
    return " | ".join(s[:n])[:90]
# 1. 15格盘数+案例
from collections import Counter
ct=Counter()
for c,v in d.items():
    if v.get("cong_type"): ct[(v["cong_type"],v["cong_state"])]+=1
print("== 15格盘数(主从格) ==")
for k,n in sorted(ct.items(),key=lambda x:-x[1]):
    print("  %s/%s: %d"%(k[0],k[1],n))
print("== 每格案例断语(前2) ==")
seen=Counter()
for c,v in d.items():
    t=v.get("cong_type")
    if not t: continue
    k=(t,v.get("cong_state"))
    if seen[k]<2:
        seen[k]+=1; print("  %s/%s %s: %s"%(t,v.get("cong_state"),c,sent(c,1)))
# 2. HUAQI/MUMIE 全盘断语
print("== HUAQI 盘(30) ==")
for c,v in d.items():
    for i,n,s in v.get("pats",[]):
        if i=="ZP-SPECIAL-HUAQI":
            print("  %s %s: %s"%(c,s,sent(c,2)))
print("== MUMIE 盘(40) ==")
for c,v in d.items():
    for i,n,s in v.get("pats",[]):
        if i=="ZP-SPECIAL-MUMIE":
            print("  %s %s: %s"%(c,s,sent(c,2)))
