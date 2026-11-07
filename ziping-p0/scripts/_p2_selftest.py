
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
# 规则筛: 病最多的盘 + 有 edges 的盘 + 用神非空的盘
best=None; withedge=None
n=0
for bk in ("DTS","PZZQ"):
    fp=r"D:/shuntian-ziping-p0/p0_v2/case_audit/%s_clean.jsonl"%bk
    for line in open(fp,encoding="utf-8-sig"):
        if not line.strip(): continue
        d=json.loads(line); bz=(d.get("bazi") or "").replace(" ","")
        if len(bz)!=8: continue
        n+=1
        if n>200: break
        try: r=paipan(bz)
        except Exception: continue
        bl=r.get("bing_list") or []
        if len(bl)>=2 and best is None: best=(d["case_id"],bz,bl,r.get("bing_debate"),r.get("yongyao"))
        yy=r.get("yongyao") or {}
        if bl and yy.get("all_edges") and withedge is None:
            withedge=(d["case_id"],bz,bl,r.get("bing_debate"),yy)
        if best and withedge: break
for tag,x in (("多病",best),("有edges",withedge)):
    if not x: print("%s 未取到"%tag); continue
    cid,bz,bl,db,yy=x
    print("="*88); print("★自证[%s] %s %s"%(tag,cid,bz))
    print("  bing_list:")
    for b in bl:
        print("    %-22s %-10s domain=%s slice=%s classic=%r"%(
            b.get("bing_id"),b.get("name"),b.get("bing_domain"),b.get("slice_id"),str(b.get("classic"))[:40]))
    print("  bing_debate:"); print("   ",json.dumps(db,ensure_ascii=False,default=str)[:520])
    print("  yongyao:");     print("   ",json.dumps(yy,ensure_ascii=False,default=str)[:760])
