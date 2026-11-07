# -*- coding: utf-8 -*-
"""逐盘验收判定 dump: (case_id,label,verdict,reason)。在对应代码版本目录内运行。"""
import json, sys
from yanshou_layer import verdict, paipan
out = []
for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
    for l in open("p0_v2/case_audit/%s_clean.jsonl" % book, encoding="utf-8-sig"):
        c = json.loads(l)
        lab = c.get("label")
        if lab not in ("good", "bad"):
            continue
        try:
            v, why = verdict(paipan(c["bazi"]))
        except Exception as e:
            v, why = "CRASH", str(e)[:40]
        sp = {}
        try:
            s = (paipan(c["bazi"]) or {}).get("raw_facts", {}).get("special", {}) or {}
            sp = {k: s.get(k) for k in ("cong_type", "cong_state", "zhuanwang", "zhuanwang_state",
                                        "hua_qi", "hua_qi_state", "mu_mie", "mu_mie_state", "liangqi")}
        except Exception:
            sp = {}
        out.append({"id": c["case_id"], "label": lab, "verdict": v, "why": why, "sp": sp})
with open(sys.argv[1], "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("dump", len(out))
