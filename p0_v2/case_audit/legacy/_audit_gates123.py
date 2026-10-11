# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
"""
滴天髓阐微 案例库验证脚本
关卡1: 八字自洽 (四柱合法、干支阴阳配对、大运合法)
关卡2: 原文存在 (bazi/analysis 均能在本记录 raw 中对应)
关卡3: 断语归属 (analysis 日主与 bazi 日主一致; 大运行一致)
关卡4: 刘注对照 (canonical 中是否存在同八字 -> 经勘察刘注本无命例, 全部任注独有)
"""
import json, re, os, sys
from collections import Counter, defaultdict

JSONL = r"D:\顺天系统资料\六部经典独立案例\滴天髓阐微\滴天髓阐微.jsonl"
OUTDIR = r"D:\shuntian-ziping-p0\p0_v2\case_audit"
os.makedirs(OUTDIR, exist_ok=True)

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI   = list("子丑寅卯辰巳午未申酉戌亥")
# 阳干 / 阳支
YANG_GAN = set("甲丙戊庚壬")
YANG_ZHI = set("子寅辰午申戌")
YIN_GAN  = set("乙丁己辛癸")
YIN_ZHI  = set("丑卯巳未酉亥")

def valid_pillar(p):
    """返回 (ok, reason). p 如 '甲子'"""
    if len(p) != 2:
        return False, f"柱长异常:{p}"
    g, z = p[0], p[1]
    if g not in TIANGAN:
        return False, f"天干非法:{g}"
    if z not in DIZHI:
        return False, f"地支非法:{z}"
    if g in YANG_GAN and z not in YANG_ZHI:
        return False, f"阳干配阴支:{p}"
    if g in YIN_GAN and z not in YIN_ZHI:
        return False, f"阴干配阳支:{p}"
    return True, ""

def parse_bazi(s):
    """把 '辛卯 丁酉 庚午 丙子' 拆成 4 柱"""
    parts = re.split(r"[\s,，、;；]+", s.strip())
    parts = [p for p in parts if p]
    return parts

def normalize(s):
    """去除空白便于子串比对"""
    return re.sub(r"\s+", "", s)

records = []
with open(JSONL, "r", encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception as e:
            records.append({"_parse_error": True, "_lineno": ln, "_raw": line, "error": str(e)})
            continue
        rec["_lineno"] = ln
        records.append(rec)

print(f"总记录数: {len(records)}")

# ============ 关卡1+2+3 逐案验证 ============
results = []
bazi_counter = Counter()
named_cases = []  # 关卡5候选: 有名有姓/有身份的命例

# 身份/人物模式 (用于关卡5)
NAME_PAT = re.compile(
    r"(某?[一二三四五六七八九十]?[尚书相公卿监督][?相]?|"
    r"某?[进士举人秀才孝廉]|"
    r"[张王李赵刘陈杨黄周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董潘袁蔡蒋余于杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][中堂侍郎中丞太史]?造?|"
    r"[王公侯伯]?[公子王孙]?|"
    r"小姐|夫人|命妇|儒士|布衣|富翁|贫士|僧|道)"
)

for rec in records:
    if rec.get("_parse_error"):
        results.append({
            "case_id": rec.get("case_id", f"L{rec['_lineno']}"),
            "verdict": "reject",
            "gates": {"parse": "JSON解析失败"},
            "reasons": ["JSON解析失败"],
            "raw_snippet": rec.get("_raw", "")[:200],
        })
        continue

    cid = rec.get("case_id", "?")
    bazi_str = rec.get("bazi", "") or ""
    dayun = rec.get("dayun", []) or []
    raw = rec.get("raw", "") or ""
    analysis = rec.get("analysis", "") or ""
    reasons = []
    gates = {}

    # --- 关卡1: 八字自洽 ---
    pillars = parse_bazi(bazi_str)
    if len(pillars) != 4:
        reasons.append(f"八字柱数异常({len(pillars)}):{bazi_str}")
        gates["bazi_count"] = "fail"
    else:
        gates["bazi_count"] = "ok"
        bad = []
        for p in pillars:
            ok, why = valid_pillar(p)
            if not ok:
                bad.append(why)
        if bad:
            reasons.append("干支非法:" + ";".join(bad))
            gates["bazi_pillars"] = "fail"
        else:
            gates["bazi_pillars"] = "ok"
        # 四柱不重复
        if len(set(pillars)) != 4:
            reasons.append("四柱中存在重复柱")
            gates["bazi_dup"] = "warn"
        else:
            gates["bazi_dup"] = "ok"

    # 大运合法性
    bad_dy = []
    for p in dayun:
        ok, why = valid_pillar(p)
        if not ok:
            bad_dy.append(why)
    if bad_dy:
        reasons.append("大运干支非法:" + ";".join(bad_dy))
        gates["dayun"] = "fail"
    else:
        gates["dayun"] = "ok"

    # --- 关卡2: 原文存在 ---
    raw_norm = normalize(raw)
    bazi_norm = normalize(bazi_str)
    if bazi_norm and bazi_norm not in raw_norm:
        reasons.append("bazi字段未在raw中出现(拼接错位)")
        gates["raw_bazi"] = "fail"
    else:
        gates["raw_bazi"] = "ok"
    # analysis 是否是 raw 的子串 (允许末尾"八字："残留)
    ana_norm = normalize(analysis)
    if ana_norm:
        # 去掉 analysis 末尾可能的 "八字" 残留
        ana_trim = re.sub(r"八字[：:]?$", "", ana_norm)
        if ana_trim and ana_trim not in raw_norm:
            reasons.append("analysis字段未在raw中完整出现(拼接错位)")
            gates["raw_analysis"] = "fail"
        else:
            gates["raw_analysis"] = "ok"
    else:
        reasons.append("analysis为空")
        gates["raw_analysis"] = "empty"

    # --- 关卡3: 断语归属 ---
    # 3a. 大运行一致性: raw 中 "大运：..." 行应与 dayun 字段一致
    m = re.search(r"大运[：:]\s*(.+?)(?:\n|$)", raw)
    if m:
        raw_dy_str = m.group(1)
        raw_dy_parts = parse_bazi(raw_dy_str)
        if raw_dy_parts != dayun:
            reasons.append(f"大运字段与raw大运行不一致 field={dayun} raw={raw_dy_parts}")
            gates["dayun_match"] = "fail"
        else:
            gates["dayun_match"] = "ok"
    else:
        gates["dayun_match"] = "no_raw_dayun"

    # 3b. 日主一致性: 第三柱天干应在 analysis 中出现
    if len(pillars) == 4:
        day_gan = pillars[2][0]
        # analysis 正文 (去掉大运行)
        body = re.sub(r"^大运[：:].*?\n", "", analysis, count=1, flags=re.S)
        body_norm = normalize(body)
        # 日主天干在 analysis 中出现 (至少一次)
        if day_gan not in body_norm:
            reasons.append(f"日主天干'{day_gan}'未在analysis正文中出现(断语可能串位)")
            gates["daymaster"] = "suspect"
        else:
            gates["daymaster"] = "ok"
        # 日干X土/水/火/木/金 模式
        wuxing = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土",
                  "庚":"金","辛":"金","壬":"水","癸":"水"}
        dm_wx = wuxing.get(day_gan, "?")
        # 检查 analysis 是否有 "日干X" / "日主X" / "日干X(木火土金水)"
        dm_pattern = re.compile(rf"(日干|日主|日主为?|造为?日主?){day_gan}[{dm_wx}]?")
        if not dm_pattern.search(analysis):
            # 弱信号, 仅记录不驳回
            gates["daymaster_explicit"] = "not_explicit"
        else:
            gates["daymaster_explicit"] = "ok"

    # 3c. 记录重复八字 (同盘多造, 可能是录入重复)
    bazi_counter[bazi_str] += 1

    # --- 关卡5候选: 有名有姓 ---
    if analysis:
        nm = NAME_PAT.search(analysis)
        if nm:
            named_cases.append({
                "case_id": cid,
                "bazi": bazi_str,
                "named_as": nm.group(0),
                "snippet": analysis[:120].replace("\n", " "),
            })

    # --- 判定 ---
    hard_fail = any(v in ("fail", "empty") for k, v in gates.items() if k in
                    ("bazi_count", "bazi_pillars", "dayun", "raw_bazi", "raw_analysis", "dayun_match"))
    suspect = gates.get("daymaster") == "suspect"
    if hard_fail:
        verdict = "reject"
    elif suspect:
        verdict = "suspect"  # 存疑
    else:
        verdict = "pass"

    results.append({
        "case_id": cid,
        "line_no": rec.get("line_no"),
        "bazi": bazi_str,
        "verdict": verdict,
        "gates": gates,
        "reasons": reasons,
        "named": bool(named_cases and named_cases[-1]["case_id"] == cid) if named_cases else False,
    })

# ============ 汇总 ============
verdict_counter = Counter(r["verdict"] for r in results)
print("=== 判定汇总 ===")
for k, v in verdict_counter.items():
    print(f"  {k}: {v}")

# 重复八字
dup_bazi = {b: c for b, c in bazi_counter.items() if c > 1 and b}
print(f"=== 重复八字(同盘多造): {len(dup_bazi)} 个 ===")
for b, c in list(dup_bazi.items())[:20]:
    print(f"  {b}: {c}次")

print(f"=== 关卡5候选(有名有姓): {len(named_cases)} 条 ===")

# 保存中间结果
interim = {
    "total": len(results),
    "verdict": dict(verdict_counter),
    "dup_bazi": dup_bazi,
    "named_cases": named_cases,
    "results": results,
}
with open(os.path.join(OUTDIR, "_interim_gates123.json"), "w", encoding="utf-8") as f:
    json.dump(interim, f, ensure_ascii=False, indent=2)

# 打印 reject/suspect 清单
print("\n=== REJECT / SUSPECT 清单 ===")
for r in results:
    if r["verdict"] != "pass":
        print(f"[{r['verdict'].upper()}] {r['case_id']} L{r['line_no']} {r['bazi']}")
        for reason in r["reasons"]:
            print(f"    - {reason}")
