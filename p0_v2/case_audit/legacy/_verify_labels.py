# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
import json, os
from collections import Counter

OUT = r"D:\shuntian-ziping-p0\p0_v2\case_audit"
books = ["DTS","PZZQ","QTBJ","YHZP","SFTK","SMTH"]

print("书名 | good | bad | mixed | neutral | 合计")
tot = Counter()
for b in books:
    f = os.path.join(OUT, b + "_clean.jsonl")
    recs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    labels = Counter(r.get("label","MISSING") for r in recs)
    # check all have label
    missing = sum(1 for r in recs if "label" not in r)
    print(b, "|", labels.get("good",0), "|", labels.get("bad",0), "|",
          labels.get("mixed",0), "|", labels.get("neutral",0), "|", len(recs),
          "| missing_label=" + str(missing))
    for k in ["good","bad","mixed","neutral"]:
        tot[k] += labels.get(k,0)
print("合计 |", tot["good"], "|", tot["bad"], "|", tot["mixed"], "|", tot["neutral"], "|",
      sum(tot.values()))

# Write label_distribution.md
md = "# 六本案例库 label 分布\n\n"
md += "| 书名 | good | bad | mixed | neutral | 合计 |\n"
md += "|---|---|---|---|---|---|\n"
gt = Counter()
for b in books:
    f = os.path.join(OUT, b + "_clean.jsonl")
    recs = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    labels = Counter(r.get("label","") for r in recs)
    md += f"| {b} | {labels.get('good',0)} | {labels.get('bad',0)} | {labels.get('mixed',0)} | {labels.get('neutral',0)} | {len(recs)} |\n"
    for k in ["good","bad","mixed","neutral"]:
        gt[k] += labels.get(k,0)
md += f"| **合计** | **{gt['good']}** | **{gt['bad']}** | **{gt['mixed']}** | **{gt['neutral']}** | **{sum(gt.values())}** |\n"
md += "\n## 四类定义\n"
md += "- **good**：原断明确富贵/科甲/仕路显赫/长寿/富（无重大凶断）\n"
md += "- **bad**：原断明确凶死/贫夭/残疾/刑克/破家\n"
md += "- **mixed**：贵但短寿/先凶后吉/吉凶并存\n"
md += "- **neutral**：原断中性/无明确吉凶结局\n"
md += "\n## 标注方法\n歧义案例（贵词+凶词同现）逐条读 raw 全文精判命主实际结局；拿不准的归 neutral。\n"

with open(os.path.join(OUT, "label_distribution.md"), "w", encoding="utf-8") as f:
    f.write(md)
print("\nlabel_distribution.md written")
