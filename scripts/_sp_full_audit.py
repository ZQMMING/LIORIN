"""special_pattern 全格对账: 全量2106盘 dump patterns 产出 + 四支三合组合。
输出: scripts/_sp_audit.json {case_id: {patterns:[(id,name,state)], cong_type, cong_state, zw, liangqi, hua, branches}}"""
import json,sys,glob,re,collections
sys.path.insert(0,"p0_v2")
from bazi_gate import paipan
out={}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f,encoding="utf-8"):
        d=json.loads(l)
        bz=d.get("bazi") or ""
        if not bz: continue
        try:
            r=paipan(bz)
        except Exception as e:
            out[d["case_id"]]={"err":str(e)[:80]};continue
        sp=r.get("special") or {}
        pats=[(p.get("pattern_id"),p.get("name"),p.get("state")) for p in sp.get("patterns",[])]
        bz4=re.findall(r"[子丑寅卯辰巳午未申酉戌亥]",bz)
        out[d["case_id"]]={"pats":pats,"cong_type":sp.get("cong_type"),
            "cong_state":sp.get("cong_state"),"zw":sp.get("zhuanwang_state"),
            "lq":(sp.get("liangqi") or {}).get("name"),"hq":sp.get("hua_qi"),
            "br":bz4,"label":d.get("label")}
json.dump(out,open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False)
print("dump",len(out))
