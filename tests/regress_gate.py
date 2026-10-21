# -*- coding: utf-8 -*-
"""常设回归闸门(入库): 100盘基线 + 全量 2106 语义分布 + 大运分布.
用法: python tests/regress_gate.py
"""
import sys, os, json, glob, collections, io
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_p0 = os.path.join(ROOT, "p0_v2")
if _p0 in sys.path:
    sys.path.remove(_p0)
from p0_v2.bazi_gate import paipan

CA = os.path.join(ROOT, "p0_v2", "case_audit")
base = json.load(open(os.path.join(CA, "_100盘_base_regen2.json"), encoding="utf-8"))
ge_diff = xi_diff = winner_diff = 0
chg = []
for c in base["cases"]:
    r = paipan(c["bazi"])
    gc = r.get("ge_cheng") or {}
    ysd = r.get("yongshen_decision") or {}
    if gc.get("ge") != c.get("ge"):
        ge_diff += 1
        chg.append((c["bazi"], c.get("ge"), gc.get("ge")))
    if (gc.get("xi_wx") or []) != (c.get("xi_wx") or []):
        xi_diff += 1
    if ysd.get("winner_shen") != c.get("winner_shen"):
        winner_diff += 1

BOOKS = ["DTS_clean.jsonl", "PZZQ_clean.jsonl", "QTBJ_clean.jsonl",
         "SFTK_clean.jsonl", "SMTH_clean.jsonl", "YHZP_clean.jsonl"]
bing = collections.Counter(); pri = collections.Counter(); ge = collections.Counter()
shape = collections.Counter()
for fn in BOOKS:
    hits = glob.glob(os.path.join(ROOT, "p0_v2", "**", fn), recursive=True)
    if not hits:
        continue
    with open(hits[0], encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            bz = (obj.get("bazi") or "").strip()
            if not bz or len(bz.split()) != 4:
                continue
            try:
                r = paipan(bz)
            except Exception:
                continue
            for b in (r.get("bing_list") or []):
                bing[b.get("bing_id")] += 1
            pri[(r.get("yongyao") or {}).get("primary") or "None"] += 1
            g = (r.get("ge_cheng") or {})
            ge[g.get("ge") or "None"] += 1
            shape["%s/%s" % (g.get("shape_base"), g.get("shape"))] += 1

DAYUN = ['甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未']
lv = collections.Counter()
for c in base["cases"]:
    r = paipan(c["bazi"], dayun_list=DAYUN)
    for st in ((r.get("suiyun") or {}).get("dayun_steps") or []):
        lv[(st.get("verdict") or {}).get("shorthand")] += 1

OUT = os.path.join(ROOT, "p0_v2", "output", "REGRESSION_LATEST.txt")
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("回归闸门报告\n")
    f.write("100pan: ge_diff=%d xi_diff=%d winner_diff=%d (expect 0/0/0)\n" % (ge_diff, xi_diff, winner_diff))
    for b, o, n in chg:
        f.write("  ge变更: %s | %s -> %s\n" % (b, o, n))
    f.write("病机: %s\n" % dict(bing.most_common()))
    f.write("primary: %s\n" % dict(pri.most_common()))
    f.write("格局: %s\n" % dict(ge.most_common(12)))
    f.write("形态: %s\n" % dict(shape.most_common(16)))
    f.write("大运吉凶: %s\n" % dict(lv.most_common()))
print("100pan: ge_diff=%d xi_diff=%d winner_diff=%d (expect 0/0/0)" % (ge_diff, xi_diff, winner_diff))
print("病机:", dict(bing.most_common()))
print("报告:", OUT)
sys.exit(0 if (ge_diff, xi_diff, winner_diff) == (0, 0, 0) else 1)
