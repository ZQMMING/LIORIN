# -*- coding: utf-8 -*-
"""by_domain 分布核 —— 六本 2106 盘"""
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
from engines.common.bing_debate import resolve_primary_bing

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
dom_pan = collections.Counter()      # 每域出现在多少盘
dom_primary = collections.Counter()  # 每域拿主病的盘数
dom_bing = collections.Counter()    # 每域病机条目数
ndist = collections.Counter()       # 每盘有几个域
crash = 0
n = 0
noprimary = 0
sample = []
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
            db = resolve_primary_bing(f, bl)
        except Exception:
            crash += 1
            continue
        n += 1
        bd = db.get("by_domain") or {}
        if not bl:
            continue
        if not bd:
            noprimary += 1
        ndist[len(bd)] += 1
        for dom, v in bd.items():
            dom_pan[dom] += 1
            dom_bing[dom] += v["bing_count"]
            if v.get("primary"):
                dom_primary[dom] += 1
        if len(sample) < 4 and len(bd) >= 3:
            sample.append((d["case_id"], bz, {k: [r["bing_id"] for r in v["ranked"]] for k, v in bd.items()},
                           db["primary_bing"]["bing_id"] if db.get("primary_bing") else None))

print("=" * 84)
print("by_domain 分布   盘 %d   崩溃 %d   无 by_domain 的有病盘 %d" % (n, crash, noprimary))
print("=" * 84)
print("  每盘域数分布:")
for k in sorted(ndist):
    print("    %d 个域: %4d 盘" % (k, ndist[k]))
print("\n  按域统计:")
print("    %-16s %8s %10s %8s" % ("域", "出现盘数", "病机条目", "拿主病盘"))
for dom in sorted(dom_bing, key=lambda x: -dom_bing[x]):
    print("    %-16s %8d %10d %8d" % (dom, dom_pan[dom], dom_bing[dom], dom_primary[dom]))
print("\n  多域并存抽样(>=3 域, 规则: 案例表原序前 4):")
for cid, bz, m, gp in sample:
    print("    %-9s %-17s 全局主病=%s" % (cid, bz, gp))
    for k, v in sorted(m.items()):
        print("        %-14s %s" % (k, v))