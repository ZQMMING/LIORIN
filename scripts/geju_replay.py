# -*- coding: utf-8 -*-
"""格局/结构病域断语事件回放 v2（不碰label）。
断语病种 -> 期望格 -> 该格引擎 po_ge_hits 命中 -> per病种 precision/recall
语境桶(断语病种但盘格不匹配)不计漏; 引擎维度缺单独记。
"""
import sys,json,glob,re,collections
sys.path.insert(0,"p0_v2");sys.path.insert(0,"engines/common");sys.path.insert(0,"engines")
from bazi_gate import paipan

DISEASES=[
 # name, 断语pattern, 期望格集, 引擎命中判据(domain,detail子串)
 ("GE_GUAN_BEI_SHANG",re.compile(r"(伤官见官|官星被伤|官被伤|破官|伤其官|官.*逢伤|透官.*伤)"),
  lambda ge: ge=="正官格", lambda h: h["domain"]=="GEJU" and "伤官" in h["hit_detail"]),
 ("GE_YONG_BEI_HE",re.compile(r"(合去|逢合|被合|合住|羁绊|合而不化|官星不清|被合去)"),
  lambda ge: ge=="正官格", None),  # 引擎无合维度
 ("GE_YONG_WU_ZHUO",re.compile(r"(孤官无辅|孤官|无着|用神无着|无辅|气势不流通)"),
  lambda ge: ge=="正官格", None),  # 缺失型模板不对应孤官
 ("GE_CONG_PO",re.compile(r"(假从|破从|从而不纯|从.*比劫|从.*争财)"),
  lambda ge: "从格" in ge, None),  # 从格无po_ge模板(po_n=0)
 ("JG_CAI_PO_YIN",re.compile(r"(财破印|印逢财坏|财坏印|财伤印|印被财伤|佩印.*逢财|印.*遇财)"),
  lambda ge: "印格" in ge, lambda h: h["domain"]=="JIEGOU" and ("正财" in h["hit_detail"] or "偏财" in h["hit_detail"])),
 ("JG_CAI_DANG_SHA",re.compile(r"(财党煞|财滋煞|财生煞|财来党煞|透财而逢煞|财.*煞)"),
  lambda ge: ge=="财格", lambda h: h["domain"]=="JIEGOU" and "七杀" in h["hit_detail"]),
 ("JG_YIN_DUO_SHI",re.compile(r"(枭夺食|枭神夺食|偏印夺食|印夺食|食被印夺)"),
  lambda ge: "食神格" in ge, lambda h: "偏印" in h["hit_detail"]),
]
seen=set();tot=0
stat=collections.defaultdict(lambda:{"decl":0,"in_ge":0,"hit":0,"miss":0,"ctx":0,"nodim":0})
eng_total=collections.Counter()
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for line in open(f,encoding="utf-8"):
        d=json.loads(line);cid=d["case_id"]
        if cid in seen:continue
        seen.add(cid);tot+=1
        try:out=paipan(d["bazi"])
        except:continue
        gc=(out.get("raw_facts") or {}).get("ge_cheng") or {}
        ge=gc.get("ge") or "";hits=gc.get("po_ge_hits") or []
        txt=(d.get("raw") or "")+" "+(d.get("analysis") or "")
        for nm,pat,ge_ok,hit_ok in DISEASES:
            if not pat.search(txt):continue
            s=stat[nm];s["decl"]+=1
            if not ge_ok(ge):
                s["ctx"]+=1;continue  # 语境桶(泛论/他造/格识别差异)
            s["in_ge"]+=1
            if hit_ok is None:
                s["nodim"]+=1;continue  # 引擎维度缺
            m=any(hit_ok(h) for h in hits)
            if m:s["hit"]+=1
            else:s["miss"]+=1
print("全案例盘(去重) n=%d"%tot)
print("\n=== 7病种 断语事件 recall（按格对齐，不碰label）===")
print("%-18s %5s %5s %5s %5s %5s"%("病种","decl","格匹配","命中","漏","语境桶"))
for nm,pat,ge_ok,hit_ok in DISEASES:
    s=stat[nm]
    rec=100*s["hit"]/s["in_ge"] if s["in_ge"] else 0
    print("%-18s %5d %5d %5d %5d %5d  recall(格内)=%.1f%%"%(
        nm,s["decl"],s["in_ge"],s["hit"],s["miss"],s["ctx"],rec))
# 格内汇总
agg_in=sum(s["in_ge"] for s in stat.values());agg_hit=sum(s["hit"] for s in stat.values())
agg_miss=sum(s["miss"] for s in stat.values());agg_nodim=sum(s["nodim"] for s in stat.values())
print("\n格内合计: 匹配%d 命中%d 漏%d 维度缺%d -> recall=%.1f%%"%(agg_in,agg_hit,agg_miss,agg_nodim,100*agg_hit/agg_in if agg_in else 0))
