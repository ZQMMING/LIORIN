
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
p=_pillars("丙子己亥乙丑壬午"); f=_l0(p); f["pillars"]=p
f["wuxing_power"]=build_wuxing_power(p,f); f["tian_he"]=build_tian_he(p,f)
build_ge_cheng(f); apply_he_po_ge(f); normalize_ti_wx(f)
bl=build_bingyao_layer(f,[]).get("bing_list") or []
print("bing_list 键:")
for b in bl: print("  ",b.get("bing_id"),"domain=",repr(b.get("bing_domain")),"slice=",b.get("slice_id"))
db=resolve_primary_bing(f,bl)
print("ranked[0] domain=",repr(db["ranked"][0].get("bing_domain")))
print("by_domain keys=",list((db.get("by_domain") or {}).keys()))
