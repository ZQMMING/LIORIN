
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
GW={"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
SH={"木":"火","火":"土","土":"金","金":"水","水":"木"}          # 我生=食伤=儿
SB={"木":"水","火":"木","土":"火","金":"土","水":"金"}          # 生我=印=母
KB={"木":"金","火":"水","土":"木","金":"火","水":"土"}          # 克我=官杀
KE={"木":"土","土":"水","水":"火","火":"金","金":"木"}          # 我克=财=妻
def m(f,wx):
    wp=(f.get("wuxing_power") or {}).get("wuxing_power") or {}
    r=wp.get(wx) or {}
    return (int(r.get("ben_n",0) or 0)+int(r.get("zhong_n",0) or 0)
            +int(r.get("yu_n",0) or 0)+int(r.get("stem_n",0) or 0))
POS={"君赖臣生":["DT-0363","DT-0365","DT-0370","PZ-0146","PZ-0184"],
     "母慈灭子":["DT-0370","DT-0372","PZ-0183"],
     "儿能救母":["DT-0009","DT-0368","DT-0369","PZ-0179"],
     "夫健怕妻":["DT-0375","DT-0376","DT-0377","DT-0378"]}
NEG=["YH-0116","YH-0117","SM-0040","YH-0170"]
import glob
rows={}
for bk in ("DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"):
    for l in open(r"D:/shuntian-ziping-p0/p0_v2/case_audit/%s_clean.jsonl"%bk,encoding="utf-8-sig"):
        if l.strip():
            d=json.loads(l); rows[d["case_id"]]=d
for jl,ids in POS.items():
    print("==",jl)
    print("   %-9s %-4s %-4s %-4s %-4s %-4s"%("case","我","印","食伤","官杀","财"))
    for cid in ids:
        d=rows.get(cid)
        if not d: continue
        bz=(d.get("bazi") or "").replace(" ","")
        r=paipan(bz); f=r.get("raw_facts") or {}
        w=GW[bz[4]]
        print("   %-9s %-4d %-4d %-4d %-4d %-4d"%(cid,m(f,w),m(f,SB[w]),m(f,SH[w]),m(f,KB[w]),m(f,KE[w])))
print("== 污染/否定样本")
print("   %-9s %-4s %-4s %-4s %-4s %-4s"%("case","我","印","食伤","官杀","财"))
for cid in NEG:
    d=rows.get(cid)
    if not d: continue
    bz=(d.get("bazi") or "").replace(" ","")
    r=paipan(bz); f=r.get("raw_facts") or {}
    w=GW[bz[4]]
    print("   %-9s %-4d %-4d %-4d %-4d %-4d"%(cid,m(f,w),m(f,SB[w]),m(f,SH[w]),m(f,KB[w]),m(f,KE[w])))
