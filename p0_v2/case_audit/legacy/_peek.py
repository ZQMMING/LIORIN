# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json,re
MAIN=r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴.jsonl"
BARE=r"D:\顺天系统资料\六部经典独立案例\穷通宝鉴\穷通宝鉴_bare.jsonl"
def load(p):
    o=[]
    for line in open(p,encoding="utf-8"):
        line=line.strip()
        if line:o.append(json.loads(line))
    return o
rows={r["case_id"]:r for r in load(MAIN)+load(BARE)}
for cid in ["QT-0003","QT-0008","QT-0019","QT-0099","QT-0155","QT-0284","QT-0305"]:
    r=rows[cid]
    print("="*70)
    print(cid, r["bazi"])
    print("ANALYSIS:", r["analysis"][:400].replace("\n"," / "))
