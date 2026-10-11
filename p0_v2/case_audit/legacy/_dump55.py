# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json,os
OUTDIR=r"D:\shuntian-ziping-p0\p0_v2\case_audit"
rows=[json.loads(l) for l in open(os.path.join(OUTDIR,"QTBJ_clean.jsonl"),encoding="utf-8") if l.strip()]
doubts=[r for r in rows if r["verdict"]=="doubt"]
print("DOUBTS:",len(doubts))
for r in doubts:
    print("="*80)
    print(r["case_id"],"|",r["bazi"])
    print("RAW:",r["raw"][:600].replace("\n"," / "))
    print("ANA:",r["analysis"][:300].replace("\n"," / "))
