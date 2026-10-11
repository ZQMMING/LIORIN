# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
最终分类 + 提取关卡5有名命例
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

# 已知理论段落误提取 (人工确认)
THEORETICAL_NONCASES = {"DT-0041", "DT-0509", "DT-0510", "DT-0511"}
# 短交叉引用 (13字, 非完整命例)
SHORT_REFS = {"DT-0490", "DT-0491", "DT-0492"}

# 有名命例提取: 在 analysis 中找 "X中堂/X尚书/X侍郎/X中丞/X相公/X观察/X太守" 等
TITLE_RE = re.compile(
    r"([\u4e00-\u9fa5]{1,2}"
    r"(?:中堂|尚书|侍郎|中丞|太史|相公|观察|太守|刺史|方伯|都转|运使|京兆|"
    r"进士|孝廉|茂才|举人|秀才|明经|"
    r"公子|王孙|夫人|孺人))造?"
)
# 排除纯动作/描述
EXCLUDE = {"仕至","仕至观","仕至侍","仕至尚","擢观","仁至观","仁至方","仁至尚","仁至侍",
           "至观","至侍","至尚","至刑","虽位","运仕","堂而","署出","卯仕","此造","此命",
           "此董","此刘","此钱","此秦","此王","皆中","己丑中","红绫易","易公"}

results = []
named_for_gate5 = []

for rec in records:
    cid = rec["case_id"]
    bazi = rec["bazi"]
    dayun = rec.get("dayun", [])
    raw = rec.get("raw", "")
    analysis = rec.get("analysis", "")
    reasons = []

    # 关卡1: 八字自洽
    pillars = parse_pillars(bazi)
    g1_pass = True
    if len(pillars) != 4:
        g1_pass = False; reasons.append(f"八字柱数={len(pillars)}")
    else:
        for p in pillars:
            if not valid_pillar(p):
                g1_pass = False; reasons.append(f"干支非法:{p}")
    for p in dayun:
        if not valid_pillar(p):
            g1_pass = False; reasons.append(f"大运非法:{p}")

    # 关卡2: raw 包含
    raw_norm = re.sub(r"\s+", "", raw)
    ana_norm = re.sub(r"八字[：:]?$", "", re.sub(r"\s+", "", analysis))
    g2_pass = (re.sub(r"\s+","",bazi) in raw_norm) and (ana_norm in raw_norm if ana_norm else False)
    if not g2_pass:
        reasons.append("bazi/analysis未在raw中对应")

    # 关卡3: 断语归属 — 检查是否真为命例 (有大运行 or 有命例行文)
    lines = raw.split("\n")
    has_dayun_line = ("大运" in lines[0] if False else False)
    # 检查是否有 "X造" 或 "此造" 或 "X日" 等命例行文
    is_real_case = bool(re.search(r"[一二三四五六七八九十][日月时日][干支]|日干|日主|此造|此命|之造|先生|造，|造。|生于", analysis))
    has_dayun = len(dayun) >= 6

    # 判定
    if cid in THEORETICAL_NONCASES:
        verdict = "reject"
        reason_cat = "原文拼接"
        reasons.append("理论段落误提取为命例(无大运行,正文为干支理论讨论)")
    elif cid in SHORT_REFS:
        verdict = "suspect"
        reason_cat = "存疑"
        reasons.append("13字短交叉引用(同名命例的简要提及,非完整命例)")
    elif not g1_pass or not g2_pass:
        verdict = "reject"
        reason_cat = "八字错" if not g1_pass else "原文拼接"
    elif not has_dayun and not is_real_case:
        verdict = "suspect"
        reason_cat = "存疑"
        reasons.append("无大运行且命例行文特征弱")
    else:
        verdict = "pass"
        reason_cat = ""

    # 关卡5: 有名命例
    named_label = None
    for m in TITLE_RE.finditer(analysis):
        label = m.group(0)
        if label in EXCLUDE: continue
        if len(label) < 3: continue
        named_label = label
        break

    entry = {
        "case_id": cid,
        "line_no": rec.get("line_no"),
        "bazi": bazi,
        "dayun": dayun,
        "verdict": verdict,
        "reason_cat": reason_cat,
        "reasons": reasons,
        "named_as": named_label,
        "analysis_head": analysis[:200].replace("\n", " "),
    }
    results.append(entry)
    if named_label and verdict in ("pass", "suspect"):
        named_for_gate5.append({
            "case_id": cid,
            "bazi": bazi,
            "named_as": named_label,
            "analysis_head": analysis[:300].replace("\n", " "),
        })

# 汇总
vc = Counter(r["verdict"] for r in results)
print("=== 最终判定 ===")
for k,v in vc.items(): print(f"  {k}: {v}")
print(f"\n=== 关卡5候选有名命例: {len(named_for_gate5)} 条 ===")
nc = Counter(x["named_as"] for x in named_for_gate5)
for name, cnt in nc.most_common(50):
    print(f"  {name}: {cnt}")

# 保存
out = {
    "total": len(results),
    "verdict": dict(vc),
    "results": results,
    "named_for_gate5": named_for_gate5,
}
with open(os.path.join(OUTDIR, "_final_classification.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("\n=== REJECT/SUSPECT 清单 ===")
for r in results:
    if r["verdict"] != "pass":
        print(f"  [{r['verdict'].upper()}] {r['case_id']} {r['bazi']} | {'; '.join(r['reasons'])}")
