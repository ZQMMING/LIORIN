
import sys,os,json,traceback
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import _pillars, paipan
from engines.common.l0_fact_builder import build as _l0
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.ge_jie_layer import build_ge_cheng, apply_he_po_ge, normalize_ti_wx
from engines.common.bingyao_layer import build_bingyao_layer
fp=r"D:/shuntian-ziping-p0/p0_v2/case_audit/DTS_clean.jsonl"
c=0
for line in open(fp,encoding="utf-8-sig"):
    if not line.strip(): continue
    d=json.loads(line); bz=(d.get("bazi") or "").replace(" ","")
    if len(bz)!=8: continue
    try:
        p=_pillars(bz); f=_l0(p); f["pillars"]=p
        f["wuxing_power"]=build_wuxing_power(p,f)
        f["tian_he"]=build_tian_he(p,f)
        build_ge_cheng(f); apply_he_po_ge(f); normalize_ti_wx(f)
        build_bingyao_layer(f,[]).get("bing_list") or []
    except Exception as e:
        c+=1
        if c<=2:
            print("★崩溃 %s %s"%(d["case_id"],bz))
            traceback.print_exc(limit=6)
    if c>=2: break
print("共遇到崩溃 %d"%c)
