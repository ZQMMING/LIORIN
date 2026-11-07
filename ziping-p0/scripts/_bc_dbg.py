
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
for cid,bz in [("DT-0002","庚申庚辰戊辰戊午"),("DT-0003","辛酉辛丑己酉丙寅"),("DT-0004","壬辰壬寅甲寅庚午")]:
    r=paipan(bz); rf=r.get("raw_facts") or {}
    cf=rf.get("combination_facts") or {}
    wm=r.get("wangshuai_matrix") or {}
    print("="*84); print("★%s %s  四支=%s"%(cid,bz,[bz[1],bz[3],bz[5],bz[7]]))
    print("  liuchong=%s"%json.dumps(cf.get("liuchong"),ensure_ascii=False))
    print("  branch_chong=%s"%json.dumps(wm.get("branch_chong"),ensure_ascii=False))
