# -*- coding: utf-8 -*-
"""PATCH-4d/4e 被拦盘 断语反查(不碰 label): 抽 12 盘核"断语是否支持拦因"。
读 case_audit 原文, 标 支持/不支持/无关(取用章语)。"""
import json, glob, collections

cases = {}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f, encoding="utf-8"):
        d = json.loads(l)
        cases[d["case_id"]] = d

NEW = json.load(open("scripts/_sp_audit_new.json", encoding="utf-8"))
ban = [(cid, [p[1] for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG-BAN"])
       for cid, d in NEW.items() if any(p[0] == "ZP-SPECIAL-CONG-BAN" for p in d.get("pats", []))]
print("被拦总盘 %d" % len(ban))

# 反查对象: 各类拦因各抽若干
by_reason = collections.defaultdict(list)
for cid, reasons in ban:
    for r in reasons:
        by_reason[r].append(cid)

for reason, ids in sorted(by_reason.items()):
    print("\n=== %s (%d 盘) ===" % (reason, len(ids)))
    for cid in ids[:4]:
        d = cases.get(cid, {})
        raw = (d.get("raw") or d.get("analysis") or "")[:120].replace("\n", " ")
        print("  %s: %s" % (cid, raw))
