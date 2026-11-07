
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
for cid,bz in [("DT-0009","丙子己亥乙丑壬午"),("DT-0010","甲寅壬申癸巳癸亥")]:
    p=_pillars(bz); f=_l0(p); f["pillars"]=p
    f["wuxing_power"]=build_wuxing_power(p,f); th=build_tian_he(p,f); f["tian_he"]=th
    build_ge_cheng(f); apply_he_po_ge(f); normalize_ti_wx(f)
    bl=build_bingyao_layer(f,[]).get("bing_list") or []
    db=resolve_primary_bing(f,bl); yy=resolve_yongyao(f,db,{})
    print("="*84); print("★%s %s 日主=%s"%(cid,bz,f.get("daymaster_element")))
    print("  bing_list:")
    for b in bl:
        print("    %-20s %-8s -> 病五行? %r"%(b.get("bing_id"),b.get("name"),b.get("bing_wx")))
    print("  primary_bing=%r"%yy.get("primary_bing"))
    print("  --- edges 按 kind ---")
    for e in yy.get("all_edges") or []:
        print("    kind=%-3s 药=%-2s function=%-16s blocked=%r"%(e.get("kind"),e.get("wuxing"),e.get("function"),e.get("blocked")))
    print("  medicine_blocked=%s"%(json.dumps(yy.get("medicine_blocked"),ensure_ascii=False,default=str)[:400]))
