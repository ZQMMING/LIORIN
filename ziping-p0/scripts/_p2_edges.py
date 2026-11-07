
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import _pillars
from engines.common.l0_fact_builder import build as _l0
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.ge_jie_layer import build_ge_cheng, apply_he_po_ge, normalize_ti_wx
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.bing_debate import resolve_primary_bing
from engines.common.yongyao_resolve import resolve_yongyao
SH={"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE={"木":"土","火":"金","土":"水","金":"木","水":"火"}
for cid,bz in [("DT-0009","丙子己亥乙丑壬午"),("DT-0010","甲寅壬申癸巳癸亥")]:
    p=_pillars(bz); f=_l0(p); f["pillars"]=p
    f["wuxing_power"]=build_wuxing_power(p,f); th=build_tian_he(p,f); f["tian_he"]=th
    build_ge_cheng(f); apply_he_po_ge(f); normalize_ti_wx(f)
    bl=build_bingyao_layer(f,[]).get("bing_list") or []
    db=resolve_primary_bing(f,bl); yy=resolve_yongyao(f,db,{})
    print("="*86); print("★%s %s  日主=%s"%(cid,bz,f.get("daymaster_element") or f.get("dm_wx")))
    print("  bing_list: %s"%[(b.get("bing_id"),b.get("name")) for b in bl])
    print("  primary_bing=%r"%yy.get("primary_bing"))
    print("  --- all_edges 逐条(核 kind 与五行关系) ---")
    for e in yy.get("all_edges") or []:
        m=e.get("wuxing"); k=e.get("kind"); fn=e.get("function"); bl_=e.get("blocked")
        print("    kind=%-3s 药=%s function=%-10s blocked=%r"%(k,m,fn,bl_))
        if k=="制":
            print("        KE_BACK[病]? 病五行须为",{v:m for v,v in KE.items()}.get(m), " 引擎给的病五行:", (yy.get("primary_bing") or {}).get("wuxing"))
    print("  medicine_blocked=%r"%(yy.get("medicine_blocked"),))
    print("  primary_medicine=%r"%json.dumps(yy.get("primary_medicine"),ensure_ascii=False,default=str)[:200])
