
import sys,os,json
sys.path.insert(0,r"D:/shuntian-ziping-p0")
_P0=os.path.join(r"D:/shuntian-ziping-p0","p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
import collections
st=collections.Counter(); ex=[]
for bk in ["DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"]:
    for l in open(r"D:/shuntian-ziping-p0/p0_v2/case_audit/%s_clean.jsonl"%bk,encoding="utf-8-sig"):
        if not l.strip(): continue
        d=json.loads(l); bz=(d.get("bazi") or "").replace(" ","")
        if len(bz)!=8: continue
        zlis=[bz[1],bz[3],bz[5],bz[7]]
        dup=[z for z,c in collections.Counter(zlis).items() if c>=2]
        if not dup:
            st["无重复支"]+=1; continue
        r=paipan(bz); lc=(r.get("raw_facts") or {}).get("combination_facts",{}).get("liuchong") or []
        # 该重复支在 liuchong 里出现了几次
        n_rep=sum(1 for pr in lc if dup[0] in pr)
        if n_rep>=2:
            st["★重复支在liuchong出现>=2次(L0全报)"]+=1
            if len(ex)<5: ex.append((d["case_id"],bz,zlis,lc))
        elif n_rep==1:
            st["重复支在liuchong只出现1次(L0去重)"]+=1
        else:
            st["重复支不在liuchong"]+=1
print("="*84)
print("N_dup 真实口径 —— L0 liuchong 是否全报重复支")
print("="*84)
for k in sorted(st): print("  %-42s %5d"%(k,st[k]))
print()
for e in ex: print("  ",e)
