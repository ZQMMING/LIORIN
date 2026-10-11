# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
最终分类 v3: 修正dayun空字段问题
- dayun字段为空但analysis首行有干支串(大运行) -> PASS (字段未抽取, 但案例本身正确)
- 理论段落误提取 -> REJECT
- 13字短交叉引用 -> SUSPECT
"""
import json, re, os
from collections import Counter

JSONL = r"D:\顺天系统资料\六部经典独立案例\滴天髓阐微\滴天髓阐微.jsonl"
OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI   = list("子丑寅卯辰巳午未申酉戌亥")
YANG_GAN = set("甲丙戊庚壬"); YANG_ZHI = set("子寅辰午申戌")
YIN_GAN  = set("乙丁己辛癸"); YIN_ZHI  = set("丑卯巳未酉亥")

def valid_pillar(p):
    if len(p) != 2: return False
    g, z = p[0], p[1]
    if g not in TIANGAN or z not in DIZHI: return False
    if g in YANG_GAN and z not in YANG_ZHI: return False
    if g in YIN_GAN and z not in YIN_ZHI: return False
    return True

def parse_pillars(s):
    return [p for p in re.split(r"[\s,，、;；]+", s.strip()) if p]

records = []
with open(JSONL, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        records.append(json.loads(line))

THEORETICAL_NONCASES = {"DT-0041", "DT-0509", "DT-0510", "DT-0511"}
SHORT_REFS = {"DT-0490", "DT-0491", "DT-0492"}

# 有名命例: 真正的人/职位名 (排除动作描述)
TITLE_RE = re.compile(
    r"([\u4e00-\u9fa5]{1,3}"
    r"(?:中堂|尚书|侍郎|中丞|太史|相公|观察|太守|刺史|方伯|都转|运使|京兆|"
    r"进士|孝廉|茂才|举人|秀才|明经|"
    r"公子|王孙|夫人|孺人))造?"
)
EXCLUDE = {"仕至","仕至观","仕至侍","仕至尚","擢观","仁至观","仁至方","仁至尚","仁至侍",
           "至观","至侍","至尚","至刑","虽位","运仕","堂而","署出","卯仕","此造","此命",
           "皆中","己丑中","红绫易","易公","出为观","而升观","丑中进"}

results = []
named_for_gate5 = []
dayun_field_empty_count = 0

for rec in records:
    cid = rec["case_id"]
    bazi = rec["bazi"]
    dayun = rec.get("dayun", []) or []
    raw = rec.get("raw", "")
    analysis = rec.get("analysis", "")
    reasons = []
    notes = []

    # 关卡1
    pillars = parse_pillars(bazi)
    g1_ok = True
    if len(pillars) != 4:
        g1_ok = False; reasons.append(f"八字柱数={len(pillars)}")
    else:
        for p in pillars:
            if not valid_pillar(p):
                g1_ok = False; reasons.append(f"干支非法:{p}")
    for p in dayun:
        if not valid_pillar(p):
            g1_ok = False; reasons.append(f"大运非法:{p}")

    # 关卡2
    raw_norm = re.sub(r"\s+", "", raw)
    ana_norm = re.sub(r"八字[：:]?$", "", re.sub(r"\s+", "", analysis))
    g2_ok = (re.sub(r"\s+","",bazi) in raw_norm) and (ana_norm in raw_norm if ana_norm else False)
    if not g2_ok:
        reasons.append("bazi/analysis未在raw中对应")

    # dayun 字段空但 analysis 首行有干支串
    if len(dayun) == 0:
        first_line = analysis.split("\n")[0] if "\n" in analysis else analysis[:60]
        parts = parse_pillars(first_line)
        if len(parts) >= 6 and all(valid_pillar(p) for p in parts):
            notes.append("dayun字段为空,但analysis首行含大运行(字段抽取遗漏,案例本身正确)")
            dayun_field_empty_count += 1

    # 判定
    if cid in THEORETICAL_NONCASES:
        verdict = "reject"; reason_cat = "原文拼接"
        reasons.append("理论段落误提取为命例")
    elif cid in SHORT_REFS:
        verdict = "suspect"; reason_cat = "存疑"
        reasons.append("13字短交叉引用(非完整命例)")
    elif not g1_ok:
        verdict = "reject"; reason_cat = "八字错"
    elif not g2_ok:
        verdict = "reject"; reason_cat = "原文拼接"
    else:
        verdict = "pass"; reason_cat = ""

    # 关卡5有名命例
    named_label = None
    for m in TITLE_RE.finditer(analysis):
        label = m.group(0)
        if label in EXCLUDE or len(label) < 3: continue
        named_label = label
        break

    entry = {
        "case_id": cid, "line_no": rec.get("line_no"),
        "bazi": bazi, "dayun": dayun,
        "verdict": verdict, "reason_cat": reason_cat,
        "reasons": reasons, "notes": notes,
        "named_as": named_label,
        "analysis_head": analysis[:250].replace("\n", " "),
    }
    results.append(entry)
    if named_label and verdict == "pass":
        named_for_gate5.append({
            "case_id": cid, "bazi": bazi,
            "named_as": named_label,
            "analysis_head": analysis[:400].replace("\n", " "),
        })

vc = Counter(r["verdict"] for r in results)
print("=== 最终判定 ===")
for k,v in vc.items(): print(f"  {k}: {v}")
print(f"\ndayun字段空但analysis有大运行: {dayun_field_empty_count} 条")
print(f"\n=== 关卡5候选(有名有姓, 仅pass): {len(named_for_gate5)} 条 ===")
nc = Counter(x["named_as"] for x in named_for_gate5)
for name, cnt in nc.most_common(50):
    print(f"  {name}: {cnt}")

# 保存供子代理使用
named_json = os.path.join(OUTDIR, "_named_cases_gate5.json")
with open(named_json, "w", encoding="utf-8") as f:
    json.dump(named_for_gate5, f, ensure_ascii=False, indent=2)
print(f"\n有名命例已存: {named_json}")

# 保存最终分类
with open(os.path.join(OUTDIR, "_final_results_v3.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(results), "verdict": dict(vc), "results": results}, f, ensure_ascii=False, indent=2)

print("\n=== REJECT/SUSPECT ===")
for r in results:
    if r["verdict"] != "pass":
        print(f"  [{r['verdict'].upper()}] {r['case_id']} {r['bazi']} | {'; '.join(r['reasons'])}")
