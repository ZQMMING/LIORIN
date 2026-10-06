"""病识别整层审计: label bad 盘 × identify_bing原始触发(未过滤未消) × 最终bing。"""
import json,sys,collections
sys.path.insert(0,"scripts"); sys.path.insert(0,"p0_v2")
sys.path.insert(0,"engines/common")
from bazi_gate import paipan
from bingyao_layer import identify_bing

cat = collections.Counter()
miss = []        # raw空 -> 识别漏
killed = []      # raw有但最终空 -> 被消/豁免
for book in ["DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP"]:
    for l in open("p0_v2/case_audit/%s_clean.jsonl"%book,encoding="utf-8-sig"):
        c=json.loads(l)
        if c.get("label")!="bad": continue
        try: r=paipan(c["bazi"])
        except Exception: continue
        f=r.get("raw_facts") or {}
        raw=identify_bing(f, r.get("power_queries") or [])
        final=r.get("bing_list") or []
        if not raw:
            cat["识别漏(raw空)"]+=1; miss.append(c)
        elif not final:
            cat["触发后被消/豁免"]+=1; killed.append((c,raw))
        else:
            cat["已识别(最终有病)"]+=1
print("bad盘分类:",dict(cat))
print("\n=== 识别漏(raw空) 抽样 ===")
for c in miss[:15]:
    print(c["case_id"],c["bazi"],"|",(c.get("raw") or "")[:70])
