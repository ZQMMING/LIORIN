
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import _pillars, paipan
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
for cid,bz in [("DT-0014","戊辰壬戌辛未己丑"),("DT-0029","甲申甲戌甲寅甲戌"),("DT-0009","丙子己亥乙丑壬午")]:
    p=_pillars(bz); f=l0build(p)
    wp=build_wuxing_power(p,f)
    wpd=wp.get("wuxing_power",wp)
    print("="*86); print("★%s %s  日主=%s"%(cid,bz,f.get("day_stem")))
    print("  wuxing_power 顶层键:",sorted(wp.keys()))
    print("  每五行:")
    for wx in ("木","火","土","金","水"):
        d=wpd.get(wx) or {}
        print("    %s: %s"%(wx,json.dumps(d,ensure_ascii=False,default=str)[:170]))
