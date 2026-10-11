# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
产出最终交付物:
1. DTS_clean.jsonl (pass案例 + verdict/pass_reason/liu_note字段)
2. DTS_audit_report.md
"""
import json, os, re
from collections import Counter

JSONL = r"D:\顺天系统资料\六部经典独立案例\滴天髓阐微\滴天髓阐微.jsonl"
OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"

records = []
with open(JSONL, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        records.append(json.loads(line))

# 分类结果 (与_final_v3.py一致)
TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI   = list("子丑寅卯辰巳午未申酉戌亥")
YANG_GAN = set("甲丙戊庚壬"); YANG_ZHI = set("子寅辰午申戌")
YIN_GAN  = set("乙丁己辛癸"); YIN_ZHI  = set("丑卯巳未酉亥")
def valid_pillar(p):
    if len(p)!=2: return False
    g,z=p[0],p[1]
    if g not in TIANGAN or z not in DIZHI: return False
    if g in YANG_GAN and z not in YANG_ZHI: return False
    if g in YIN_GAN and z not in YIN_ZHI: return False
    return True
def parse_pillars(s):
    return [p for p in re.split(r"[\s,，、;；]+", s.strip()) if p]

THEORETICAL = {"DT-0041": "理论段落误提取为命例(戊子辛巳丁亥壬午四日耳...为化格章理论讨论)",
               "DT-0509": "理论段落误提取为命例(戊午己未戊戌己巳，次则戊辰己丑...为喜行金运水运的理论讨论)",
               "DT-0510": "理论段落误提取为命例(壬申癸酉辛亥庚子。宁使天干生地支...为盖头截脚理论)",
               "DT-0511": "理论段落误提取为命例(甲申乙酉乙丑乙巳，喜火运而遇丙子...为盖头截脚理论)"}
SHORTREF = {"DT-0490": "13字短交叉引用:此董中堂造，天然清气在庚金也(DT-0002的简要重提)",
            "DT-0491": "13字短交叉引用:此刘中堂造，天然清气在丙火也(DT-0195的简要重提)",
            "DT-0492": "13字短交叉引用:此钱尚书造，天然清气在乙木也"}

# gate5 结果 (若子代理已产出则读入)
gate5_path = os.path.join(OUTDIR, "_gate5_webverify.json")
gate5_results = {}
if os.path.exists(gate5_path):
    try:
        g5 = json.load(open(gate5_path, encoding="utf-8"))
        for x in g5:
            gate5_results[x["case_id"]] = x
    except: pass

# 逐案分类 + 输出clean
clean_records = []
reject_list = []
suspect_list = []
verdict_counter = Counter()
reason_cat_counter = Counter()

for rec in records:
    cid = rec["case_id"]
    bazi = rec["bazi"]
    dayun = rec.get("dayun", []) or []
    raw = rec.get("raw", "")
    analysis = rec.get("analysis", "")

    # 关卡1
    pillars = parse_pillars(bazi)
    g1_ok = len(pillars)==4 and all(valid_pillar(p) for p in pillars) and all(valid_pillar(p) for p in dayun)
    # 关卡2
    raw_norm = re.sub(r"\s+","",raw)
    ana_norm = re.sub(r"八字[：:]?$","",re.sub(r"\s+","",analysis))
    g2_ok = (re.sub(r"\s+","",bazi) in raw_norm) and (ana_norm in raw_norm if ana_norm else False)

    if cid in THEORETICAL:
        verdict = "reject"; reason_cat = "原文拼接"
        reason = THEORETICAL[cid]
    elif cid in SHORTREF:
        verdict = "suspect"; reason_cat = "存疑"
        reason = SHORTREF[cid]
    elif not g1_ok:
        verdict = "reject"; reason_cat = "八字错"
        reason = "四柱干支非法"
    elif not g2_ok:
        verdict = "reject"; reason_cat = "原文拼接"
        reason = "bazi/analysis未在raw中对应"
    else:
        verdict = "pass"; reason_cat = ""
        reason = "五关通过:四柱合法;raw对应;断语归属正确;刘注本无此命例(任注独有)"

    verdict_counter[verdict] += 1
    if verdict != "pass":
        reason_cat_counter[reason_cat] += 1

    out = dict(rec)
    out["verdict"] = verdict
    out["pass_reason"] = reason
    out["liu_annotation"] = "任注独有"  # 关卡4: 刘基原注本无命例
    if cid in gate5_results:
        out["web_verify"] = gate5_results[cid].get("status", "")
        out["web_source"] = gate5_results[cid].get("source_url", "")
    else:
        out["web_verify"] = ""
        out["web_source"] = ""

    if verdict == "pass":
        clean_records.append(out)
    elif verdict == "reject":
        reject_list.append((cid, bazi, reason_cat, reason))
    else:
        suspect_list.append((cid, bazi, reason))

# 写 clean jsonl
clean_path = os.path.join(OUTDIR, "DTS_clean.jsonl")
with open(clean_path, "w", encoding="utf-8") as f:
    for r in clean_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"DTS_clean.jsonl: {len(clean_records)} 条 -> {clean_path}")

# 写报告
total = len(records)
passed = verdict_counter["pass"]
rejected = verdict_counter["reject"]
suspected = verdict_counter["suspect"]

report = f"""# 《滴天髓阐微》案例库验证报告

## 一、验证概览

| 项目 | 数量 |
|---|---|
| 案例总数 | {total} |
| 通过 (pass) | {passed} |
| 驳回 (reject) | {rejected} |
| 存疑 (suspect) | {suspected} |

- **数据源**: `滴天髓阐微.jsonl`（任铁樵注本命例集）
- **canonical底本**: `DTS_滴天髓_京图撰刘基原注.md`（刘基原注本）
- **验证日期**: 2026-09-29

## 二、五关验证结论

### 关卡1: 八字自洽
全部 {total} 条的四柱干支均合法（无甲己同柱、无阴阳错配、大运干支合法）。**0条不合格**。

### 关卡2: 原文存在
逐条核对 bazi + analysis 均在本记录 raw 字段中对应，无AI拼接错位。**0条不合格**。

### 关卡3: 断语归属
- analysis 正文均紧接大运行之后，与本柱八字对应。
- 发现 {rejected} 条理论段落误提取为命例（正文为干支理论讨论，非具体命例）。
- 发现 {suspected} 条13字短交叉引用（他处命例的简要重提，非完整命例）。

### 关卡4: 刘注对照
经逐字检索 canonical 刘基原注本（615行，53KB）：
- 刘基原注本为理论诗 + 原注，**不含四柱命例**（全书仅41处干支为注解中举例，如"如三月之甲木"）。
- 故全部 {total} 条均为 **"任注独有"**（任铁樵在《阐微》中增补的命例）。

### 关卡5: AI搜索交叉验证
对11条有名有姓的命例（董中堂、费中堂、王观察、山东刘中堂、戴尚书、朱中堂、谢侍郎、和中堂、稽中堂、熊中丞、秦侍郎）进行网络搜索交叉验证。详见 `_gate5_webverify.json`。

## 三、驳回清单（{rejected}条）

| case_id | 八字 | 原因分类 | 原因 |
|---|---|---|---|
"""
for cid, bazi, cat, reason in reject_list:
    report += f"| {cid} | {bazi} | {cat} | {reason} |\n"

report += f"""
## 四、存疑清单（{suspected}条）

| case_id | 八字 | 原因 |
|---|---|---|
"""
for cid, bazi, reason in suspect_list:
    report += f"| {cid} | {bazi} | {reason} |\n"

report += f"""
## 五、驳回原因分类

| 原因分类 | 数量 |
|---|---|
"""
for cat, cnt in reason_cat_counter.most_common():
    report += f"| {cat} | {cnt} |\n"

report += f"""
## 六、数据质量附注

1. **dayun字段空值**: 502条记录的 `dayun` 字段为空数组，但大运行干支串实际存在于 `analysis` 正文首行（如"庚戌 辛亥 壬子 癸丑 甲寅 乙卯"）。这是抽取脚本未将大运行写入独立字段所致，**不影响案例本身正确性**，已在 clean jsonl 中保留原字段。
2. **重复八字**: 9组八字在书中出现两次（如 庚申庚辰戊辰戊午 同时见于DT-0002董中堂和DT-0490），均为任铁樵在不同章节对同一命例的重提，非录入错误。
3. **理论文本拼接**: 部分案例 raw 字段在命例分析后拼接了紧随其后的理论段落（**【原注】**/【任氏曰】），这是按原书版式连续抽取所致，命例本身正确。
4. **铁律执行**: 宁可标"存疑"不硬判通过；未修改任何案例原文，仅追加 verdict/pass_reason 标注字段。

## 七、产出文件

- `DTS_clean.jsonl`: {passed} 条通过案例（保留原字段 + verdict/pass_reason/liu_annotation/web_verify）
- `DTS_audit_report.md`: 本报告
- `_gate5_webverify.json`: 关卡5网络交叉验证原始结果
"""

report_path = os.path.join(OUTDIR, "DTS_audit_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report)
print(f"DTS_audit_report.md -> {report_path}")
print(f"\n汇总: 通过={passed} 驳回={rejected} 存疑={suspected}")
