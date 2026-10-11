# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
滴天髓阐微 案例库验证 v2
关卡1: 八字自洽
关卡2: 原文存在
关卡3: 断语归属 (精化: 日主五行/四柱引用一致性/截断检测)
关卡5候选: 提取有名有姓命例
"""
import json, re, os
from collections import Counter

JSONL = r"D:\顺天系统资料\六部经典独立案例\滴天髓阐微\滴天髓阐微.jsonl"
OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI   = list("子丑寅卯辰巳午未申酉戌亥")
YANG_GAN = set("甲丙戊庚壬"); YANG_ZHI = set("子寅辰午申戌")
YIN_GAN  = set("乙丁己辛癸"); YIN_ZHI  = set("丑卯巳未酉亥")
WUXING_GAN = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
WUXING_ZHI = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

def valid_pillar(p):
    if len(p) != 2: return False, f"柱长异常:{p}"
    g, z = p[0], p[1]
    if g not in TIANGAN: return False, f"天干非法:{g}"
    if z not in DIZHI: return False, f"地支非法:{z}"
    if g in YANG_GAN and z not in YANG_ZHI: return False, f"阳干配阴支:{p}"
    if g in YIN_GAN and z not in YIN_ZHI: return False, f"阴干配阳支:{p}"
    return True, ""

def parse_pillars(s):
    return [p for p in re.split(r"[\s,，、;；]+", s.strip()) if p]

def normalize(s):
    return re.sub(r"\s+", "", s)

# 有名有姓/有身份模式 (关卡5候选)
TITLE_PAT = re.compile(
    r"([\u4e00-\u9fa5]{1,3}"  # 姓氏/名字前缀
    r"(?:中堂|尚书|相公|中丞|太史|侍郎|观察|太守|刺史|方伯|观察使|都转|运使|太守|京兆|太守|"
    r"进士|孝廉|茂才|举人|秀才|明经|"
    r"公子|王孙|太史|孝廉|"
    r"夫人|小姐|命妇|儒人|孺人))"
)
# 排除泛称
GENERIC = {"此造","此命","此君","此人","其造","前造","上造","下造","今造","一生","凡造"}

records = []
with open(JSONL, "r", encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line: continue
        rec = json.loads(line)
        rec["_lineno"] = ln
        records.append(rec)

results = []
bazi_counter = Counter()
named_cases = []
all_suspects_detail = []

for rec in records:
    cid = rec.get("case_id", "?")
    bazi_str = rec.get("bazi", "") or ""
    dayun = rec.get("dayun", []) or []
    raw = rec.get("raw", "") or ""
    analysis = rec.get("analysis", "") or ""
    reasons = []
    gates = {}

    pillars = parse_pillars(bazi_str)
    bazi_counter[bazi_str] += 1

    # ===== 关卡1 =====
    if len(pillars) != 4:
        reasons.append(f"八字柱数异常({len(pillars)})")
        gates["g1_count"] = "fail"
    else:
        gates["g1_count"] = "ok"
        bad = []
        for p in pillars:
            ok, why = valid_pillar(p)
            if not ok: bad.append(why)
        if bad:
            reasons.append("干支非法:" + ";".join(bad))
            gates["g1_pillars"] = "fail"
        else:
            gates["g1_pillars"] = "ok"

    bad_dy = []
    for p in dayun:
        ok, why = valid_pillar(p)
        if not ok: bad_dy.append(why)
    gates["g1_dayun"] = "fail" if bad_dy else "ok"
    if bad_dy: reasons.append("大运干支非法:" + ";".join(bad_dy))

    # ===== 关卡2 =====
    raw_norm = normalize(raw)
    bazi_norm = normalize(bazi_str)
    gates["g2_bazi_in_raw"] = "ok" if (not bazi_norm or bazi_norm in raw_norm) else "fail"
    if gates["g2_bazi_in_raw"] == "fail":
        reasons.append("bazi字段未在raw中出现")

    ana_norm = normalize(analysis)
    ana_trim = re.sub(r"八字[：:]?$", "", ana_norm)
    if not ana_norm:
        gates["g2_analysis_in_raw"] = "empty"
        reasons.append("analysis为空")
    else:
        gates["g2_analysis_in_raw"] = "ok" if (ana_trim and ana_trim in raw_norm) else "fail"
        if gates["g2_analysis_in_raw"] == "fail":
            reasons.append("analysis未在raw中完整出现")

    # ===== 关卡3 =====
    # 3a. 大运行一致性
    m = re.search(r"大运[：:]\s*(.+?)(?:\n|$)", raw)
    if m:
        raw_dy_parts = parse_pillars(m.group(1))
        gates["g3_dayun_match"] = "ok" if raw_dy_parts == dayun else "fail"
        if gates["g3_dayun_match"] == "fail":
            reasons.append(f"大运字段与raw不一致 field={dayun} raw={raw_dy_parts}")
    else:
        # 有些记录raw里大运行没有"大运："前缀, 直接是干支串
        first_line_after_bazi = raw.split("\n")[1] if "\n" in raw else ""
        dy_parts_alt = parse_pillars(first_line_after_bazi)
        if dy_parts_alt == dayun:
            gates["g3_dayun_match"] = "ok_no_label"
        else:
            gates["g3_dayun_match"] = "no_raw_dayun"

    # 3b. 日主一致性 (精化)
    if len(pillars) == 4:
        day_gan = pillars[2][0]
        day_elem = WUXING_GAN[day_gan]
        # analysis 正文 (去掉大运行)
        body = re.sub(r"^大运[：:].*?\n", "", analysis, count=1, flags=re.S)
        body = re.sub(r"^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥](?:\s+[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])+\n", "", body, count=1)
        body_norm = normalize(body)

        # 信号1: 日主天干直接出现
        sig_gan = day_gan in body_norm
        # 信号2: 日干/日主 + 天干 或 五行
        sig_explicit = bool(re.search(rf"(日干|日主|造为?日主?|身主?){day_gan}", analysis))
        sig_elem = bool(re.search(rf"(日干|日主|身主?|此造|其命|此命)[^。]{{0,6}}{day_elem}", analysis))
        # 信号3: 分析中提到的地支是否都在八字地支集合里 (排除常见术语)
        bazi_zhis = set(p[1] for p in pillars)
        mentioned_zhis = set(re.findall(r"[子丑寅卯辰巳午未申酉戌亥]", body))
        # 大运地支不算 (因为分析会讨论大运)
        dayun_zhis = set(p[1] for p in dayun)
        foreign_zhis = mentioned_zhis - bazi_zhis - dayun_zhis
        # 这些"外来"地支如果出现在分析里, 可能是串位信号
        # 但古典文本常提到 "寅卯辰" 方局等, 所以只记录不直接驳回
        sig_foreign = len(foreign_zhis)

        if sig_gan or sig_explicit or sig_elem:
            gates["g3_daymaster"] = "ok"
        else:
            gates["g3_daymaster"] = "suspect"
            reasons.append(f"日主'{day_gan}({day_elem})'未在analysis中明确点出; 外来地支={foreign_zhis if foreign_zhis else '无'}")
            all_suspects_detail.append({
                "case_id": cid, "bazi": bazi_str, "day_gan": day_gan,
                "foreign_zhis": sorted(foreign_zhis),
                "body_head": body[:200].replace("\n", " "),
            })

    # 3c. 截断检测: analysis 过短或以不完整标点结尾
    ana_text = analysis.strip()
    if len(ana_text) < 40:
        gates["g3_truncation"] = "short"
        reasons.append(f"analysis过短({len(ana_text)}字)")
    elif ana_text.endswith(("，", "、", "：", "（", "(")):
        gates["g3_truncation"] = "suspect"
        reasons.append("analysis以不完整标点结尾(可能截断)")
    else:
        gates["g3_truncation"] = "ok"

    # ===== 判定 =====
    hard_fail = any(v in ("fail","empty") for k,v in gates.items() if k in
        ("g1_count","g1_pillars","g1_dayun","g2_bazi_in_raw","g2_analysis_in_raw","g3_dayun_match"))
    suspect = (gates.get("g3_daymaster") == "suspect" or
               gates.get("g3_truncation") in ("suspect","short"))
    if hard_fail:
        verdict = "reject"
    elif suspect:
        verdict = "suspect"
    else:
        verdict = "pass"

    # ===== 关卡5: 有名有姓 =====
    named_hit = TITLE_PAT.search(analysis)
    named_label = None
    if named_hit:
        label = named_hit.group(0)
        # 去掉单字泛称
        if label not in GENERIC and len(label) >= 2:
            named_label = label
            named_cases.append({
                "case_id": cid, "bazi": bazi_str, "named_as": label,
                "line_no": rec.get("line_no"),
                "snippet": analysis[:150].replace("\n"," "),
            })

    results.append({
        "case_id": cid, "line_no": rec.get("line_no"),
        "bazi": bazi_str, "verdict": verdict,
        "gates": gates, "reasons": reasons,
        "named_as": named_label,
    })

# ===== 汇总 =====
vc = Counter(r["verdict"] for r in results)
print("=== 判定汇总 ===")
for k,v in vc.items(): print(f"  {k}: {v}")

dup_bazi = {b:c for b,c in bazi_counter.items() if c>1 and b}
print(f"\n=== 重复八字 {len(dup_bazi)} 组 ===")
for b,c in dup_bazi.items(): print(f"  {b}: {c}次")

print(f"\n=== 关卡5候选(有名有姓) {len(named_cases)} 条 ===")
nc = Counter(x["named_as"] for x in named_cases)
for name, cnt in nc.most_common(40):
    print(f"  {name}: {cnt}")

# 保存
out = {
    "total": len(results), "verdict": dict(vc),
    "dup_bazi": dup_bazi,
    "named_cases": named_cases,
    "results": results,
    "suspects_detail": all_suspects_detail,
}
with open(os.path.join(OUTDIR, "_interim_v2.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("\n=== SUSPECT 清单 ===")
for r in results:
    if r["verdict"] == "suspect":
        print(f"  {r['case_id']} L{r['line_no']} {r['bazi']} | {'; '.join(r['reasons'])}")
