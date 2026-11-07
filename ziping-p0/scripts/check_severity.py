# -*- coding: utf-8 -*-
"""severity 序数分布核 —— 六本 1412 条病机"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import _pillars
from engines.common.l0_fact_builder import build as _l0
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.ge_jie_layer import build_ge_cheng, apply_he_po_ge, normalize_ti_wx
from engines.common.bingyao_layer import build_bingyao_layer

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
sev = collections.Counter()
src = collections.Counter()
byid = collections.defaultdict(collections.Counter)
crash = 0
n = 0
for bk in BOOKS:
    fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip():
            continue
        d = json.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        try:
            p = _pillars(bz); f = _l0(p); f["pillars"] = p
            f["wuxing_power"] = build_wuxing_power(p, f)
            f["tian_he"] = build_tian_he(p, f)
            build_ge_cheng(f); apply_he_po_ge(f); normalize_ti_wx(f)
            bl = build_bingyao_layer(f, []).get("bing_list") or []
        except Exception:
            crash += 1
            continue
        n += 1
        for b in bl:
            sev[b.get("severity")] += 1
            src[str(b.get("severity_source", "")).split("-")[0]] += 1
            byid[b["bing_id"]][b.get("severity")] += 1

print("=" * 76)
print("severity 序数分布   盘 %d   崩溃 %d   病机 %d" % (n, crash, sum(sev.values())))
print("=" * 76)
print("  0(无病) %4d" % sev[0])
for k in (1, 2, 3, 4):
    print("  %d%8d  %5.1f%%" % (k, sev[k], sev[k] / max(1, sum(sev.values())) * 100))
print("\n  来源类型: %s" % ", ".join("%s=%d" % (k, v) for k, v in src.most_common()))
print("\n  逐病 severity:")
for bid in sorted(byid):
    c = byid[bid]
    print("    %-22s %s  (n=%d)" % (bid, " ".join("%d:%d" % (k, c[k]) for k in (1, 2, 3, 4) if c[k]), sum(c.values())))