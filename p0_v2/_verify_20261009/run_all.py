# -*- coding: utf-8 -*-
"""p0_v2 子平引擎 2106 案例全量实跑验证脚本。

只读、只写 _verify_20261009/ 目录，不改代码和数据。
"""
import sys, os, json, time, traceback, collections

ROOT = r"D:/shuntian-ziping-p0"
OUT_DIR = os.path.join(ROOT, "p0_v2", "_verify_20261009")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, ROOT)
from p0_v2.bazi_gate import paipan

BOOKS = [
    ("DTS",    "滴天髓阐微",  "DTS_clean.jsonl", 510),
    ("PZZQ",   "子平真诠",   "PZZQ_clean.jsonl", 319),
    ("QTBJ",   "穷通宝鉴",   "QTBJ_clean.jsonl", 802),
    ("SFTK",   "神峰通考",   "SFTK_clean.jsonl", 155),
    ("SMTH",   "三命通会",   "SMTH_clean.jsonl", 114),
    ("YHZP",   "渊海子平",   "YHZP_clean.jsonl", 206),
]

# ── 探针 ────────────────────────────────────────────────────────────────────
def run_probe():
    """返回探针表（dict），打印结果。"""
    results = {}
    # Probe A: 癸酉丁巳己卯甲戌 → 顶层36键（>=34）
    r = paipan("癸酉丁巳己卯甲戌")
    results["probe_a_keys"] = len(r.keys())
    results["probe_a_bing_list_count"] = len(r.get("bing_list") or [])
    results["probe_a_l3_keys"] = sorted((r.get("l3_contract") or {}).keys())
    results["probe_a_ge_cheng_ge"] = (r.get("ge_cheng") or {}).get("ge")
    results["probe_a_special_count"] = len((r.get("special") or {}).get("patterns") or [])
    results["probe_a_yongyao_primary"] = (r.get("yongyao") or {}).get("primary")
    results["probe_a_climate_has"] = bool(r.get("climate"))
    print("Probe A:", {k: v for k, v in results.items() if k != "probe_a_l3_keys"}, flush=True)
    print("  l3_keys =", results["probe_a_l3_keys"], flush=True)

    # Probe B: 乙酉庚辰丁巳辛亥 → 1 条 bing, CAI_DUO_SHEN_RUO, severity=3
    r2 = paipan("乙酉庚辰丁巳辛亥")
    bl2 = r2.get("bing_list") or []
    results["probe_b_bing_count"] = len(bl2)
    results["probe_b_first_id"] = bl2[0].get("bing_id") if bl2 else None
    results["probe_b_first_severity"] = bl2[0].get("severity") if bl2 else None
    results["probe_b_first_slice_id"] = bl2[0].get("slice_id") if bl2 else None
    results["probe_b_debate_state"] = (r2.get("bing_debate") or {}).get("state")
    print("Probe B:", {k: v for k, v in results.items() if k.startswith("probe_b")}, flush=True)
    return results


# ── 单盘提取字段 ──────────────────────────────────────────────────────────────
def extract(r):
    bl = r.get("bing_list") or []
    bd = r.get("bing_debate") or {}
    gc = r.get("ge_cheng") or {}
    lc = r.get("l3_contract") or {}
    sp = r.get("special") or {}
    yy = r.get("yongyao") or {}
    cl = r.get("climate") or {}
    return {
        "bing_count": len(bl),
        "bing_domains": [b.get("bing_domain") for b in bl],
        "bing_severities": [b.get("severity") for b in bl],
        "bing_slice_ids": [b.get("slice_id") for b in bl],
        "debate_state": bd.get("state"),
        "ge_cheng_ge": gc.get("ge"),
        "de_ling": lc.get("de_ling"),
        "de_di": lc.get("de_di"),
        "dang_duo": lc.get("dang_duo"),
        "strength_verdict": lc.get("strength_verdict"),
        "special_patterns_count": len(sp.get("patterns") or []),
        "yongyao_primary": yy.get("primary"),
        "climate_has": bool(cl),
    }


# ── 逐本全量跑 ───────────────────────────────────────────────────────────────
def run_book(book_key, filename):
    path = os.path.join(ROOT, "p0_v2", "case_audit", filename)
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    print(f"\n=== {book_key} ({filename}): {len(rows)} cases ===", flush=True)

    stats = {
        "crash": 0,
        "bing_dist": collections.Counter(),   # 0 / 1 / >=2
        "slice_none": 0,
        "slice_total": 0,
        "domain_dist": collections.Counter(),
        "severity_dist": collections.Counter(),
        "debate_state_dist": collections.Counter(),
        "ge_dist": collections.Counter(),
        "de_ling_true": 0, "de_di_true": 0, "dang_duo_true": 0,
        "strength_verdict_dist": collections.Counter(),
        "special_count": 0,
        "yongyao_primary_dist": collections.Counter(),
        "climate_present": 0,
    }
    anomalies = []  # (case_id, bazi, error or phenomenon)

    for d in rows:
        bz_raw = (d.get("bazi") or "").strip()
        bz = "".join(bz_raw.split())
        cid = d.get("case_id", "?")
        if len(bz) != 8:
            anomalies.append((cid, bz_raw, "bazi length != 8"))
            continue
        try:
            r = paipan(bz)
        except Exception as e:
            stats["crash"] += 1
            anomalies.append((cid, bz_raw, f"{type(e).__name__}: {str(e)[:120]}"))
            continue
        ex = extract(r)
        # bing dist
        bc = ex["bing_count"]
        stats["bing_dist"][str(bc) + ("+" if bc >= 2 else "")] += 1
        # slice
        for sid in ex["bing_slice_ids"]:
            stats["slice_total"] += 1
            if sid is None:
                stats["slice_none"] += 1
        # domain
        for dom in ex["bing_domains"]:
            stats["domain_dist"][str(dom)] += 1
        # severity
        for sev in ex["bing_severities"]:
            stats["severity_dist"][str(sev)] += 1
        # debate
        stats["debate_state_dist"][str(ex["debate_state"])] += 1
        # ge
        if ex["ge_cheng_ge"]:
            stats["ge_dist"][ex["ge_cheng_ge"]] += 1
        # l3_contract booleans
        if ex["de_ling"] is True:
            stats["de_ling_true"] += 1
        if ex["de_di"] is True:
            stats["de_di_true"] += 1
        if ex["dang_duo"] is True:
            stats["dang_duo_true"] += 1
        stats["strength_verdict_dist"][str(ex["strength_verdict"])] += 1
        # special
        stats["special_count"] += ex["special_patterns_count"]
        # yongyao
        stats["yongyao_primary_dist"][str(ex["yongyao_primary"])] += 1
        # climate
        if ex["climate_has"]:
            stats["climate_present"] += 1

    return stats, anomalies


# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    probe = run_probe()
    all_results = {"probe": probe, "books": {}}
    total_cases = 0
    total_crashes = 0
    all_anomalies = []

    for bk, nm, fn, expected_n in BOOKS:
        stats, anomalies = run_book(bk, fn)
        n = sum(stats["bing_dist"].values())
        total_cases += n
        total_crashes += stats["crash"]
        all_anomalies.extend(anomalies)
        all_results["books"][bk] = {
            "name": nm, "cases": n, "crashes": stats["crash"],
            "bing_dist": dict(stats["bing_dist"]),
            "slice_none": stats["slice_none"],
            "slice_total": stats["slice_total"],
            "domain_dist": dict(stats["domain_dist"]),
            "severity_dist": dict(stats["severity_dist"]),
            "debate_state_dist": dict(stats["debate_state_dist"]),
            "ge_top10": dict(stats["ge_dist"].most_common(10)),
            "de_ling_true_pct": round(stats["de_ling_true"] / n * 100, 2) if n else 0,
            "de_di_true_pct": round(stats["de_di_true"] / n * 100, 2) if n else 0,
            "dang_duo_true_pct": round(stats["dang_duo_true"] / n * 100, 2) if n else 0,
            "strength_verdict_dist": dict(stats["strength_verdict_dist"]),
            "special_total": stats["special_count"],
            "yongyao_primary_dist": dict(stats["yongyao_primary_dist"]),
            "climate_present": stats["climate_present"],
        }
        print(f"  {bk}: cases={n} crash={stats['crash']} "
              f"bing={dict(stats['bing_dist'])} "
              f"slice_none={stats['slice_none']}/{stats['slice_total']} "
              f"ge_top3={list(stats['ge_dist'].most_common(3))}",
              flush=True)

    all_results["total_cases"] = total_cases
    all_results["total_crashes"] = total_crashes
    all_results["anomalies"] = all_anomalies[:100]  # cap for JSON size
    all_results["anomaly_total"] = len(all_anomalies)

    out_json = os.path.join(OUT_DIR, "fullrun_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved: {out_json}", flush=True)
    print(f"Elapsed: {time.time() - t0:.1f}s", flush=True)

    # Print summary
    print("\n========== SUMMARY ==========")
    print(f"Total cases: {total_cases}")
    print(f"Total crashes: {total_crashes}")
    print(f"Anomalies: {len(all_anomalies)}")
    for bk in ["DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP"]:
        b = all_results["books"][bk]
        print(f"\n--- {bk} ({b['name']}) ---")
        print(f"  cases={b['cases']} crash={b['crashes']}")
        print(f"  bing_dist={b['bing_dist']}")
        print(f"  slice: none={b['slice_none']}/{b['slice_total']} ({round(b['slice_none']/max(b['slice_total'],1)*100,1)}%)")
        print(f"  domain={b['domain_dist']}")
        print(f"  severity={b['severity_dist']}")
        print(f"  debate_state={b['debate_state_dist']}")
        print(f"  ge_top10={b['ge_top10']}")
        print(f"  de_ling_true={b['de_ling_true_pct']}%  de_di_true={b['de_di_true_pct']}%  dang_duo_true={b['dang_duo_true_pct']}%")
        print(f"  strength_verdict={b['strength_verdict_dist']}")
        print(f"  special_total={b['special_total']}")
        print(f"  yongyao_primary={b['yongyao_primary_dist']}")
        print(f"  climate_present={b['climate_present']}/{b['cases']}")


if __name__ == "__main__":
    main()
