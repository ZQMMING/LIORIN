
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
for cid,bz in [("DT-0029","甲申甲戌甲寅甲戌"),("DT-0044","壬午己酉甲申甲子"),("DT-0021","戊辰辛酉丙午癸巳")]:
    r=paipan(bz)
    rf=r.get("raw_facts") or {}
    rwc=rf.get("root_weight_class_facts") or {}
    print("="*86); print("★%s %s 日主=%s"%(cid,bz,rf.get("daymaster_element")))
    for k,v in rwc.items():
        print("    %-10s %s"%(k, json.dumps(v,ensure_ascii=False,default=str)[:170]))
