"""核3: 旺衰域病 × 病五行∈ti × 独立de_di × label 全量分布(dry run, 不改判定)"""
import json,sys,collections
sys.path.insert(0,"p0_v2")
from bazi_gate import paipan
WS = {"CAI_DUO_SHEN_RUO","SHA_ZHONG_SHEN_QING","XIE_QI_TAI_ZHONG",
      "YIN_DUO_MAI_ZI","BIJIE_CHENG_DANG"}
# (bing, 病五行∈ti, de_di) -> [盘数, good数]
agg = collections.defaultdict(lambda:[0,0])
for book in ["DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP"]:
    for l in open("p0_v2/case_audit/%s_clean.jsonl"%book,encoding="utf-8-sig"):
        c=json.loads(l); lab=c.get("label")
        if lab not in ("good","bad"): continue
        try: r=paipan(c["bazi"])
        except Exception: continue
        rf=r.get("raw_facts") or {}
        ti=set(((rf.get("ge_cheng") or {}).get("ti_wx") or []))
        bwx_map={'CAI_DUO_SHEN_RUO':(rf.get("wuxing_power") or {}).get('cai',''),
                 'XIE_QI_TAI_ZHONG':'x'}
        ded=(r.get("l3_contract") or {}).get("de_di")
        for b in (r.get("bing_list") or []):
            bid=b.get("bing_id")
            if bid not in WS: continue
            in_ti = b.get("bing_wx","") in ti
            k=(bid, in_ti, ded)
            agg[k][0]+=1
            if lab=="good": agg[k][1]+=1
print("bing | 病wx∈ti | de_di | 盘 | good | good占比")
for k in sorted(agg,key=lambda k:(k[0],k[1],str(k[2]))):
    n,g=agg[k]
    print(" %s | %s | %s | %d | %d | %.0f%%"%(k[0],k[1],k[2],n,g,100*g/max(1,n)))
