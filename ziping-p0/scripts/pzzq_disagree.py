# -*- coding: utf-8 -*-
"""PZZQ good/bad 分歧拆解: 象限 + 按格局/主病分布, 导出分歧明细."""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
CA = os.path.join(ROOT, "p0_v2", "case_audit")
from p0_v2.bazi_gate import paipan

rows = [json.loads(l) for l in open(os.path.join(CA, "PZZQ_clean.jsonl"), encoding="utf-8-sig") if l.strip()]
quad = collections.Counter()
disagree = []
for c in rows:
    lab = c.get("label")
    if lab not in ("good", "bad"):
        continue
    bazi = (c.get("bazi") or "").replace(" ", "")
    r = paipan(bazi)
    bl = r.get("bing_list") or []
    ev = "bad" if bl else "good"
    gc = r.get("ge_cheng") or {}
    ge = gc.get("ge") or "无格"
    primary = None
    if bl:
        primary = bl[0].get("bing_id")
    quad[(lab, ev)] += 1
    if lab != ev:
        disagree.append({"case_id": c.get("case_id"), "bazi": bazi,
                         "label": lab, "eng": ev, "ge": ge,
                         "primary": primary,
                         "n_bing": len(bl)})

gg = quad[("good", "good")]; gb = quad[("good", "bad")]
bg = quad[("bad", "good")]; bb = quad[("bad", "bad")]
tot = gg+gb+bg+bb
print("PZZQ good/bad total=%d agree=%d rate=%.1f%%" % (tot, gg+bb, (gg+bb)/tot*100))
print("象限 good+无病=%d good+有病=%d bad+无病=%d bad+有病=%d" % (gg, gb, bg, bb))

print("\n--- good+有病(误报) 按格局 ---")
g1 = collections.Counter(d["ge"] for d in disagree if d["label"] == "good")
for k, v in g1.most_common():
    print("  %-16s %d" % (k, v))
print("\n--- good+有病 按主病 ---")
g2 = collections.Counter(d["primary"] for d in disagree if d["label"] == "good")
for k, v in g2.most_common(12):
    print("  %-20s %d" % (k, v))

print("\n--- bad+无病(漏判) 按格局 ---")
b1 = collections.Counter(d["ge"] for d in disagree if d["label"] == "bad")
for k, v in b1.most_common():
    print("  %-16s %d" % (k, v))

json.dump(disagree, open(os.path.join(ROOT, "scripts", "pzzq_disagree.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n分歧明细 -> scripts/pzzq_disagree.json 共%d条" % len(disagree))
