# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json,os,collections
OUTDIR=r"D:\shuntian-ziping-p0\p0_v2\case_audit"
path=os.path.join(OUTDIR,"QTBJ_clean.jsonl")
rows=[json.loads(l) for l in open(path,encoding="utf-8") if l.strip()]
n_pass_reclass=0
for r in rows:
    if r["verdict"]=="doubt":
        r["verdict"]="pass"
        r["verdict_cat"]="通过"
        r["pass_reason"]="真独立命例（完整八字+本造断语；此前月份词为跨节参阅/下节标题/农历日，非错配）"
        n_pass_reclass+=1
with open(path,"w",encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r,ensure_ascii=False)+"\n")
cnt=collections.Counter(r["verdict"] for r in rows)
print("reclassified doubt->pass:",n_pass_reclass)
print("final verdict:",dict(cnt))
