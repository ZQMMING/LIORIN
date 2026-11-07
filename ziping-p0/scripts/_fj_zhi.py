
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
LIUHE={frozenset(x) for x in [("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")]}
CHONG={frozenset(x) for x in [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]}
SANHE={frozenset(x) for x in [("申","子","辰"),("亥","卯","未"),("寅","午","戌"),("巳","酉","丑")]}
BW={"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
SH={"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE={"木":"土","火":"金","土":"水","金":"木","水":"火"}
def j(x): return ",".join(x) if x else "-"
for cid,bz,tgtw in [("DT-0365","己巳戊辰辛酉己亥","木"),("PZ-0194","己巳癸酉癸未庚申","火")]:
    r=paipan(bz); rf=r.get("raw_facts") or {}
    cf=rf.get("combination_facts") or {}
    zs=[bz[1],bz[3],bz[5],bz[7]]
    print("="*94)
    print(f"* {cid} {bz}   财五行={tgtw}")
    print(f"  四支(年月日时): {zs}")
    print(f"  liuhe={json.dumps(cf.get('liuhe'),ensure_ascii=False)} | liuchong={json.dumps(cf.get('liuchong'),ensure_ascii=False)} | sanhe={json.dumps(cf.get('sanhe'),ensure_ascii=False)}")
    print(f"  banhe={json.dumps(cf.get('banhe'),ensure_ascii=False)} | liuhai={json.dumps(cf.get('liuhai'),ensure_ascii=False)} | liupo={json.dumps(cf.get('liupo'),ensure_ascii=False)}")
    for i,z in enumerate(zs):
        pos="年月日时"[i]
        he=sorted(o for o in zs if o!=z and frozenset((z,o)) in LIUHE)
        ch=sorted(o for o in zs if o!=z and frozenset((z,o)) in CHONG)
        san=sorted(o for o in zs if o!=z and frozenset((z,o)) in SANHE)
        by=sorted(o for o in zs if o!=z and SH[BW[o]]==BW[z])
        to=sorted(o for o in zs if o!=z and SH[BW[z]]==BW[o])
        kb=sorted(o for o in zs if o!=z and KE[BW[o]]==BW[z])
        mark="*财根" if BW[z]==tgtw else "      "
        print(f"  {mark} {pos} {z}({BW[z]}) 六合={j(he):4s} 六冲={j(ch):4s} 三合={j(san):4s} | 生我={j(by):4s} 我生={j(to):4s} 克我={j(kb):4s}")
