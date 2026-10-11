# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json,collections,os
OUTDIR=r"D:\shuntian-ziping-p0\p0_v2\case_audit"
rows=[json.loads(l) for l in open(os.path.join(OUTDIR,"QTBJ_clean.jsonl"),encoding="utf-8") if l.strip()]
# re-load full to get pollution list
print("clean written rows:",len(rows))
pol=collections.Counter()
for r in rows:
    for p in r.get("pollution",[]): pol[p]+=1
print("pollution dist:",dict(pol))
vd=collections.Counter(r["verdict"] for r in rows)
print("verdict:",dict(vd))
# doubt list for report
doubts=[(r["case_id"],r["bazi"],r["pass_reason"]) for r in rows if r["verdict"]=="doubt"]
print("doubts:",len(doubts))
