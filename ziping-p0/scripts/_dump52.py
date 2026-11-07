import sys,json,glob,re
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan
DISEASES=[
 ("GE_GUAN_BEI_SHANG",re.compile(r"(伤官见官|官星被伤|官被伤|破官|伤其官|官.*逢伤|透官.*伤)"),
  lambda ge: ge=="正官格", lambda h: h["domain"]=="GEJU" and "伤官" in h["hit_detail"]),
 ("JG_CAI_PO_YIN",re.compile(r"(财破印|印逢财坏|财坏印|财伤印|印被财伤|佩印.*逢财|印.*遇财)"),
  lambda ge: "印格" in ge, lambda h: h["domain"]=="JIEGOU" and ("正财" in h["hit_detail"] or "偏财" in h["hit_detail"])),
 ("JG_CAI_DANG_SHA",re.compile(r"(财党煞|财滋煞|财生煞|财来党煞|透财而逢煞|财.*煞)"),
  lambda ge: ge=="财格", lambda h: h["domain"]=="JIEGOU" and "七杀" in h["hit_detail"]),
 ("JG_YIN_DUO_SHI",re.compile(r"(枭夺食|枭神夺食|偏印夺食|印夺食|食被印夺)"),
  lambda ge: "食神格" in ge, lambda h: "偏印" in h["hit_detail"]),
]
seen=set();out=[]
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen:continue
        seen.add(cid)
        try:o=paipan(d["bazi"])
        except:continue
        gc=(o.get("raw_facts") or {}).get("ge_cheng") or {}
        ge=gc.get("ge") or "";hits=gc.get("po_ge_hits") or []
        txt=(d.get("raw") or "")+" "+(d.get("analysis") or "")
        for nm,pat,ge_ok,hit_ok in DISEASES:
            m=pat.search(txt)
            if not m or not ge_ok(ge):continue
            hit=any(hit_ok(h) for h in hits)
            frag=txt[max(0,m.start()-16):m.end()+16].replace("\n","")
            out.append((cid,nm,ge,"HIT" if hit else "MISS",frag,"|".join(h["hit_detail"] for h in hits) or "-"))
for x in out:print("%s | %s | %s | %s | hits=[%s] | %s"%(x[0],x[1],x[2],x[3],x[5],x[4]))
print("TOTAL",len(out))
