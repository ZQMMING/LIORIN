
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
r=paipan("丙子己亥乙丑壬午")
yy=r["yongyao"]
print("yongyao 顶层键:",sorted(yy.keys()))
print("  primary=%r ji_shen=%r"%(yy.get("primary"),yy.get("ji_shen")))
print("  all_edges=%d 条: %s"%(len(yy.get("all_edges") or []),
    [(e.get("kind"),e.get("wuxing"),e.get("accepted")) for e in (yy.get("all_edges") or [])]))
print("  auxiliary=%d 条: %s"%(len(yy.get("auxiliary_medicine") or []),
    [(e.get("kind"),e.get("wuxing")) for e in (yy.get("auxiliary_medicine") or [])]))
print("  blocked=%r evidence_refs=%r"%(yy.get("medicine_blocked"),yy.get("evidence_refs")))
bl=r["bing_list"]
print("bing_list[0] 键:",sorted(bl[0].keys()))
print("  severity=%r domain=%r slice=%r src=%r"%(bl[0].get("severity"),bl[0].get("bing_domain"),bl[0].get("slice_id"),bl[0].get("severity_source")))
