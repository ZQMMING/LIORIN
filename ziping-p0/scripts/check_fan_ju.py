# -*- coding: utf-8 -*-
"""FAN_JU 全量核 —— 分布 + DTS 断语反推 + P1 关联"""
import sys, os, json, collections, re
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
cnt = collections.Counter()
combo = collections.Counter()
crash = 0
n = 0
samples = []
# DTS 断语反推: 原文提「君赖臣生/儿能救母/母慈灭子/夫健」或水泛木浮等的盘
RAW = {}
for bk in BOOKS:
    fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
    for line in open(fp, encoding="utf-8-sig"):
        if line.strip():
            d = json.loads(line)
            RAW[(bk, d["case_id"])] = d.get("raw") or ""
KW = ["君赖臣生", "儿能救母", "母慈灭子", "夫健", "水泛木浮", "慈母", "灭子"]
dupai = []   # 原文提反局 但 引擎未触发
falsepos = []  # 原文未提 但 引擎触发
for bk in BOOKS:
    fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip():
            continue
        d = json.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        n += 1
        try:
            r = paipan(bz)
        except Exception:
            crash += 1
            continue
        lc = r.get("l3_contract") or {}
        fj = lc.get("fan_ju") or {}
        ts = fj.get("types") or []
        cnt["有多反局" if ts else "无反局"] += 1
        for t in ts:
            cnt[t] += 1
        combo[len(ts)] += 1
        raw = RAW.get((bk, d["case_id"]), "")
        hit = [k for k in KW if k in raw]
        if hit and not ts:
            dupai.append((d["case_id"], bz, hit))
        if ts and not hit and len(samples) < 10:
            samples.append((d["case_id"], bz, ts, raw[:90].replace("\n", " ")))

print("=" * 92)
print("FAN_JU 全量   盘 %d   崩溃 %d" % (n, crash))
print("=" * 92)
print("  " + " | ".join("%s=%d" % (k, v) for k, v in sorted(cnt.items())))
print("  每盘反局条数: %s" % dict(combo))
print("\n  DTS/PZZQ 原文提反局语 但引擎未触发: %d" % len(dupai))
for c, b, h in dupai[:8]:
    print("    %-9s %-17s %s" % (c, b, h))
print("\n  引擎触发但原文未提(前10, 非错, 只抽查):")
for c, b, t, raw in samples[:6]:
    print("    %-9s %-17s %-30s %s" % (c, b, ",".join(t), raw))