
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
for cid,bz in [("DT-0363","壬辰壬子甲寅戊辰"),("DT-0365","己巳戊辰辛酉己亥"),("PZ-0184","辛酉丙申壬申辛亥")]:
    r=paipan(bz); f=r.get("raw_facts") or {}
    wp=(f.get("wuxing_power") or {}).get("wuxing_power") or {}
    dm=bz[4]
    GW={"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
    w=GW[dm]
    print("="*88); print("★%s %s 日主=%s(%s)  月令=%s"%(cid,bz,dm,w,f.get("month_element") or (f.get("wuxing_power") or {}).get("month_element")))
    print("  四柱: 年%s 月%s 日%s 时%s"%(bz[0:2],bz[2:4],bz[4:6],bz[6:8]))
    for wx in ("木","火","土","金","水"):
        row=wp.get(wx) or {}
        mass=sum(int(row.get(k,0) or 0) for k in ("ben_n","zhong_n","yu_n","stem_n"))
        print("    %s: ben=%s zhong=%s yu=%s stem=%s ju=%s => mass=%-3d ling=%-3s root_detail=%s"%(
            wx,row.get("ben_n"),row.get("zhong_n"),row.get("yu_n"),row.get("stem_n"),
            row.get("ju_n"),mass,row.get("ling_state"),json.dumps(row.get("root_detail"),ensure_ascii=False)))
