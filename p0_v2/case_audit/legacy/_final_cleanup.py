# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""物理清理：每个clean.jsonl只保留verdict=pass，删除reject，加verified_at/verdict_reason"""
import json, os, datetime

OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"
TODAY = "2026-09-29"

books = ["DTS", "PZZQ", "QTBJ", "YHZP", "SFTK", "SMTH"]
summary = []

for book in books:
    path = os.path.join(OUTDIR, f"{book}_clean.jsonl")
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        continue
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    total_orig = len(recs)

    passed = []
    deleted = []
    for r in recs:
        v = r.get("verdict", "pass").lower()
        if v in ("pass", "approved", "ok", ""):
            # 补充字段
            r["verified_at"] = TODAY
            if "verdict_reason" not in r:
                r["verdict_reason"] = r.get("pass_reason", "五关通过")
            passed.append(r)
        else:
            deleted.append(r)

    # 重写clean.jsonl（只保留pass）
    with open(path, "w", encoding="utf-8") as f:
        for r in passed:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 写删除清单
    del_path = os.path.join(OUTDIR, f"_{book}_deleted.jsonl")
    with open(del_path, "w", encoding="utf-8") as f:
        for r in deleted:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    deleted_count = len(deleted)
    kept = len(passed)
    accuracy = kept / total_orig * 100 if total_orig else 0
    summary.append((book, total_orig, deleted_count, kept, accuracy))
    print(f"{book}: orig={total_orig} deleted={deleted_count} kept={kept} accuracy={accuracy:.1f}%")

print("\n=== 汇总 ===")
print(f"{'书名':<8} {'原总数':>6} {'删除数':>6} {'最终保留':>8} {'准确率':>8}")
tot_o = tot_d = tot_k = 0
for book, o, d, k, a in summary:
    print(f"{book:<8} {o:>6} {d:>6} {k:>8} {a:>7.1f}%")
    tot_o += o; tot_d += d; tot_k += k
print(f"{'合计':<8} {tot_o:>6} {tot_d:>6} {tot_k:>8} {tot_k/tot_o*100:>7.1f}%")
