
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
GW={"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
SH={"木":"火","火":"土","土":"金","金":"水","水":"木"}
SB={"木":"水","火":"木","土":"火","金":"土","水":"金"}
KB={"木":"金","火":"水","土":"木","金":"火","水":"土"}
KE={"木":"土","土":"水","水":"火","火":"金","金":"木"}
def rows(r,wx):
    wp=(r.get("raw_facts") or {}).get("wuxing_power",{}).get("wuxing_power",{}) or {}
    return wp.get(wx) or {}
for cid,bz in [("DT-0368","甲申丙子乙酉丙戌"),("PZ-0179","丙寅戊戌辛酉戊子"),
               ("DT-0365","己巳戊辰辛酉己亥"),("PZ-0194","己巳癸酉癸未庚申")]:
    r=paipan(bz); w=GW[bz[4]]
    yin=SB[w]; zi=SH[w]; chen=KB[w]; cai=KE[w]
    print("="*94)
    print("★%s %s 日主=%s(%s) 月令=%s"%(cid,bz,bz[4],w,(r.get("raw_facts") or {}).get("month_element")))
    for nm,wx in (("我",w),("印",yin),("食伤",zi),("官杀",chen),("财",cai)):
        d=rows(r,wx)
        m=sum(int(d.get(k,0) or 0) for k in ("ben_n","zhong_n","yu_n","stem_n"))
        print("  %-4s(%s) ling=%-3s ben=%-2s zhong=%-2s yu=%-2s stem=%-2s mass=%-2d rd=%s"%(
            nm,wx,d.get("ling_state"),d.get("ben_n"),d.get("zhong_n"),d.get("yu_n"),d.get("stem_n"),m,
            json.dumps(d.get("root_detail"),ensure_ascii=False)))
    fj=(r.get("l3_contract") or {}).get("fan_ju") or {}
    print("  引擎=%s"%fj.get("types"))
    print("  flag=%s"%json.dumps(fj.get("flag_map"),ensure_ascii=False))
