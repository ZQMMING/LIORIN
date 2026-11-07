#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""子平真值回放：原典四柱 → 公历日 → BaziEngine → ziping_v3 → 比对原典结论。

真值来源 cases/truth/ziping_truth_cases.json（沈孝瞻《子平真诠》原文 + 穷通宝鉴调候双证）。

用法:
    python scripts/ziping_truth_replay.py            # 跑全部断言案
    python scripts/ziping_truth_replay.py --filter ziping-009
    python scripts/ziping_truth_replay.py --dump ziping-001
    python scripts/ziping_truth_replay.py --all      # 含 conflicts 对照输出（不断言）

退出码: 0 = 全 PASS; 1 = 有 FAIL。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import sxtwl  # noqa: E402

from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402
from tongshu.reasoning.ziping_v3.runner import run_ziping  # noqa: E402

CASES = REPO / "cases" / "truth" / "ziping_truth_cases.json"

STEM = "甲乙丙丁戊己庚辛壬癸"
BRANCH = "子丑寅卯辰巳午未申酉戌亥"
STEM_IDX = {c: i for i, c in enumerate(STEM)}
BRANCH_IDX = {c: i for i, c in enumerate(BRANCH)}
# 五鼠遁：日干 → 子时干序
HOUR_STEM_BASE = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4,
                  "丁": 6, "壬": 6, "戊": 8, "癸": 8}
# 时支 → 取中间小时 (子=0, 丑=2, …, 亥=22)
HOUR_BY_BRANCH = {i: (0 if i == 0 else 2 * i) for i in range(12)}

ENGINE = BaziEngine()


def _gz(d, kind: str) -> str:
    if kind == "month":
        g = d.getMonthGZ()
    elif kind == "day":
        g = d.getDayGZ()
    else:
        g = d.getYearGZ()
    return STEM[g.tg] + BRANCH[g.dz]


def hour_pillar(day_stem: str, branch_idx: int) -> str:
    return STEM[(HOUR_STEM_BASE[day_stem] + branch_idx) % 10] + BRANCH[branch_idx]


def solve(pillars: str, start: int = 1850, end: int = 2035, limit: int = 5):
    """四柱 → [(y,m,d,h)]。年界(立春)由 BaziEngine 复核, 不靠 7/1 近似。"""
    want = pillars.split()
    if len(want) != 4:
        raise ValueError(f"四柱格式错误: {pillars}")
    hour_branch = BRANCH_IDX[want[3][1]]
    hits = []
    for year in range(start, end + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    _dt.date(year, month, day)
                except ValueError:
                    continue
                try:
                    d = sxtwl.fromSolar(year, month, day)
                except Exception:
                    continue
                if _gz(d, "day") != want[2]:
                    continue
                if _gz(d, "month") != want[1]:
                    continue
                if hour_pillar(_gz(d, "day")[0], hour_branch) != want[3]:
                    continue
                hour = HOUR_BY_BRANCH[hour_branch]
                chart = ENGINE.compute((year, month, day, hour), gender="male")
                pc = chart.get_pillars_chinese()
                if [pc["year"], pc["month"], pc["day"], pc["hour"]] != want:
                    continue
                hits.append((year, month, day, hour))
                if len(hits) >= limit:
                    return hits
    return hits


def actual(result: dict) -> dict:
    st = (result.get("strength") or {}).get("state")
    ys = result.get("yongshen") or {}
    pat = next((j for j in (result.get("judgments") or [])
                if j.get("domain") == "PATTERN"), {})
    return {
        "strength": st,
        "yongshen": ys.get("main"),
        "yongshen_basis": ys.get("basis"),
        "yongshen_quote": ys.get("classic_quote"),
        "pattern": pat.get("state"),
    }


def run_case(case: dict, dump: bool = False) -> dict:
    hits = solve(case["pillars"])
    if not hits:
        return {"case_id": case["case_id"], "pass": False,
                "reason": f"四柱无解: {case['pillars']}"}
    y, m, d, h = hits[0]
    chart = ENGINE.compute((y, m, d, h), gender="male")
    result = run_ziping(chart, enable_pattern=True)
    got = actual(result)
    checks = []
    ok = True
    for key, want in (case.get("expected") or {}).items():
        have = got.get(key)
        good = have == want
        ok = ok and good
        checks.append({"field": key, "want": want, "got": have, "ok": good})
    if dump:
        print(json.dumps({"case_id": case["case_id"], "solar": [y, m, d, h],
                          "got": got, "want": case.get("expected"),
                          "checks": checks}, ensure_ascii=False, indent=2))
    return {"case_id": case["case_id"], "name": case.get("name"),
            "solar": f"{y}-{m:02d}-{d:02d} {h:02d}:00",
            "pass": ok, "checks": checks,
            "pattern": got.get("pattern"), "basis": got.get("yongshen_basis")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="")
    ap.add_argument("--dump", default="")
    ap.add_argument("--all", action="store_true", help="连 conflicts 一起打印对照")
    args = ap.parse_args()

    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"]
    if args.filter:
        cases = [c for c in cases if c["case_id"] == args.filter]
    if not cases:
        print(f"未找到案件: {args.filter}")
        return 1

    total = 0
    failed = 0
    for case in cases:
        r = run_case(case, dump=(args.dump == case["case_id"]))
        total += 1
        mark = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            failed += 1
        extra = ""
        if r.get("checks"):
            extra = " ".join(f"{c['field']}={c['got']}(want {c['want']})"
                             + ("" if c["ok"] else "✗") for c in r["checks"])
        print(f"[{mark}] {r['case_id']} {r.get('name', '')} {r.get('solar', '')} "
              f"{extra}{(' ' + r['reason']) if r.get('reason') else ''}")
        if r.get("pattern"):
            print(f"        格局={r['pattern']}  用神依据={r.get('basis')}")

    if args.all:
        print("\n--- conflicts (两说冲突, 不作断言) ---")
        for c in data.get("conflicts", []):
            hits = solve(c["pillars"])
            if not hits:
                print(f"[NO-SOLVE] {c['case_id']} {c.get('name')} {c['pillars']}")
                continue
            y, m, d, h = hits[0]
            got = actual(run_ziping(ENGINE.compute((y, m, d, h), gender="male"),
                                    enable_pattern=True))
            print(f"[conflict] {c['case_id']} {c.get('name')} {y}-{m:02d}-{d:02d} "
                  f"沈={c['shen_yongshen']} 调候={c['tiaohou_yongshen']} "
                  f"引擎={got['yongshen']} ({got['yongshen_basis']})")

    print(f"\n{total - failed}/{total} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
