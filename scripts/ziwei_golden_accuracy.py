#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微 Golden 80 案准确率回放（逐字段对照 `expected_calculation`）。

**为什么单独做这个**：`scripts/golden_replay.py` 只算输出 hash，不比对期望值；
而 Golden 集的 `input.birth_hour` 是**时辰序号**（数据集语义），若直接当 24h 小时
喂生产适配器，会系统性偏 1–2 个时辰（2026-11-04 审计实录：68/80 命宫错位）。
本脚本显式换算语义再逐字段比对，给出可读的准确率。

用法：
    $env:PYTHONPATH='src;.'; $env:PYTHONUTF8='1'
    python scripts/ziwei_golden_accuracy.py

注意：该 Golden 的 expected 由 iztro 生成（非人工命图），因此本脚本证明的是
「生产实现与数据集生成实现一致」，不是「与原典一致」；原典口径由
`scripts/ziwei_natal_verify.py` 与 `tests/test_ziwei_natal_anchors.py` 覆盖。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

GOLDEN = ROOT / "cases" / "golden" / "ziwei_golden_set.json"
HOUR24 = [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
JU = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}


def main() -> int:
    from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter
    from tongshu.engines.ziwei_engine import CHINESE_STAR_TO_KEY

    key2zh = {v: k for k, v in CHINESE_STAR_TO_KEY.items()}
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if isinstance(cases, dict):
        cases = cases.get("cases", [])

    ad = ZiweiSolarAdapter()
    miss = Counter()
    fails: list[str] = []
    n = 0

    for c in cases:
        inp, exp = c["input"], c["expected_calculation"]
        h24 = HOUR24[int(inp["birth_hour"])]
        ch = ad.compute(inp["birth_year"], inp["birth_month"], inp["birth_day"],
                        h24, inp.get("gender", "male"))
        n += 1
        probs = []
        if ch.soul_earthly_branch != exp["ming_gong_branch"]:
            miss["命宫支"] += 1
            probs.append(f"命宫 {exp['ming_gong_branch']}→{ch.soul_earthly_branch}")
        if ch.body_earthly_branch != exp["shen_gong_branch"]:
            miss["身宫支"] += 1
            probs.append(f"身宫 {exp['shen_gong_branch']}→{ch.body_earthly_branch}")
        if JU.get(ch.fiveElementsClass) != JU.get(exp["wuxing_ju"]):
            miss["五行局"] += 1
            probs.append(f"局 {exp['wuxing_ju']}→{ch.fiveElementsClass}")

        by_branch = {p.get("branch"): p for p in ch.palaces.values()}
        ziwei = next((b for b, p in by_branch.items() if "ZIWEI" in (p.get("major") or [])), "")
        if ziwei != exp["ziwei_star_branch"]:
            miss["紫微星"] += 1
            probs.append(f"紫微 {exp['ziwei_star_branch']}→{ziwei}")

        for ep in exp["palaces"]:
            p = by_branch.get(ep["branch"])
            if not p:
                miss["宫位"] += 1
                probs.append(f"缺{ep['name']}@ {ep['branch']}")
                continue
            got = sorted(key2zh.get(k, k) for k in (p.get("major") or []))
            if got != sorted(ep["major_stars"]):
                miss["宫主星"] += 1
                probs.append(f"{ep['name']}星 {ep['major_stars']}→{got}")
        if probs:
            fails.append(f"{c['case_id']}: " + "; ".join(probs))

    print(f"Golden 案例 = {n}")
    for k, v in miss.most_common():
        print(f"  {k:6s} 不一致 {v:4d}  准确率 {100 * (n - v) / n:6.1f}%")
    if not miss:
        print("  逐字段全部一致（命宫/身宫/五行局/紫微星/十二宫主星）")
    for line in fails[:15]:
        print("  " + line)
    return 0 if not miss else 1


if __name__ == "__main__":
    raise SystemExit(main())
