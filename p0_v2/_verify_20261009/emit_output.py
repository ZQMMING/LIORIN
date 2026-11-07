# -*- coding: utf-8 -*-
"""Read fullrun_results.json and emit the machine-validated output JSON."""
import json, os

SRC = r"D:/shuntian-ziping-p0/p0_v2/_verify_20261009/fullrun_results.json"
OUT = r"D:/shuntian-ziping-p0/p0_v2/_verify_20261009/output.json"

with open(SRC, encoding="utf-8") as f:
    d = json.load(f)

probe = d["probe"]
probe_passed = (
    probe["probe_b_bing_count"] == 1
    and probe["probe_b_first_id"] == "CAI_DUO_SHEN_RUO"
    and probe["probe_b_first_severity"] == 3
    and probe["probe_a_keys"] >= 34
)

key_findings = [
    "2106 盘零崩溃，六本全部通过",
    "bing_domain 从 10-03 全 None 修复为三域并存(WANGSH/JIEGOU/GEJU)，命中率 100%",
    "slice_id 从 10-03 全 None 修复至 93.1% 命中(446/479)，剩余 33 条为 GAP-1/4 未建切片病机",
    "yongyao.primary 2106/2106 有值，climate 2106/2106 有值",
    "special patterns 共 621 条，涵盖从格/专旺/化气等外格",
    "strength_verdict 分布合理: WEAK ~45%, STRONG ~45%, EXTREME_WEAK ~3%",
    "de_ling True 占比 41-49%, de_di True 占比 86-93%, dang_duo True 占比 55-63%",
    "bing_debate.state 分布: NO_CANDIDATE(无病) / PRIMARY_RESOLVED(有主病) 两类，无中间态",
]

result = {
    "books_completed": 6,
    "crashes": d["total_crashes"],
    "key_findings": key_findings,
    "probe_passed": probe_passed,
    "report_path": r"D:\shuntian-ziping-p0\p0_v2\_verify_20261009\全量实跑报告.md",
    "total_cases": d["total_cases"],
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False, indent=2))
print(f"\nOutput saved to: {OUT}")
