# 盘级中间量 dump: L3 ling_state / L4 cheng_bai+po_ge+jiu_ying+special / P1 bing_list+yongyao / 验收判定
import sys,glob,json
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
from cheng_bai import compute_cheng_bai

out={}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in out:continue
        if not (d.get("label") or ""):continue
        o=paipan(d["bazi"])
        rf=o.get("raw_facts") or {}
        gc=rf.get("ge_cheng") or {}
        wp=rf.get("wuxing_power") or {}
        ling=tuple((k,(v.get("ling_state") if isinstance(v,dict) else ""))
                   for k,v in (wp.get("wuxing_power") or {}).items())
        cb=compute_cheng_bai(gc)
        po=gc.get("po_ge")
        ji=rf.get("jiu_ying") or {}
        sp=rf.get("special") or {}
        bl=o.get("bing_list") or []
        ya=o.get("yongyao") or {}
        out[cid]={"bazi":d["bazi"],"label":d.get("label"),
                  "ling":ling,"cheng_bai":cb,
                  "po_ge":json.dumps(po,sort_keys=True,ensure_ascii=False),
                  "jiu_ying":ji.get("triggered"),
                  "special":json.dumps({k:sp.get(k) for k in ["cong_state","zhuanwang_state","hua_qi","judgment_status"]},sort_keys=True,ensure_ascii=False),
                  "bing_list":json.dumps(bl,sort_keys=True,ensure_ascii=False),
                  "yao_primary":ya.get("primary")}
import sys as _s
json.dump(out,open(_s.argv[1],"w",encoding="utf-8"),ensure_ascii=False)
print("盘数",len(out))
