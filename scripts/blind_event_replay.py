#!/usr/bin/env python
"""盲派应期层真值回放（blind_event_cases.json）.

比结构层真值（blind_truth_cases.json）多走一层：排盘 → 盲派结构 → 应期(yq.analyze)。
断言某年必须出现某域、某事件性质、某方向的事件（原书明文『某年发生某事』）。

用法::

    python scripts/blind_event_replay.py              # 全部
    python scripts/blind_event_replay.py --filter e001
    python scripts/blind_event_replay.py --dump e002  # 打印该案全部事件
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

CASES_PATH = REPO / "cases" / "truth" / "blind_event_cases.json"


def _load():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def _build(case):
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.engines.blind_yingqi import BlindYingqiEngine

    bazi = BaziEngine()
    yq = BlindYingqiEngine(bazi)
    y, m, d, h = case["solar"]
    return yq.analyze((y, m, d, h), case["gender"], target_year=case["event_year"])


def _check(result, case):
    exp = case["expected"]
    year = case["event_year"]
    hit = [
        e for e in result.yingqi_events
        if e.get("year") == year
        and e.get("domain") == exp["domain"]
        and e.get("direction") == exp["direction"]
        and (not exp.get("event_topic") or e.get("event_topic") == exp["event_topic"])
    ]
    problems = []
    if not hit:
        problems.append(
            f"未命中：{year} 年没有 domain={exp['domain']} direction={exp['direction']}"
            f" topic={exp.get('event_topic')} 的事件"
        )
    want_age = case.get("expected_nominal_age")
    if want_age is not None and result.nominal_age != want_age:
        problems.append(f"虚岁不符: 期望 {want_age}, 实得 {result.nominal_age}")
    return hit, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="")
    ap.add_argument("--dump", default="")
    args = ap.parse_args()

    data = _load()
    cases = [c for c in data["cases"] if args.filter in c["case_id"]]
    if not cases:
        print("没有匹配案例", file=sys.stderr)
        return 2

    failed = 0
    for case in cases:
        result = _build(case)
        if args.dump and args.dump in case["case_id"]:
            print(f"== {case['case_id']} {case['pillars']} {case['event_year']}")
            print(f"   age={result.age} nominal={result.nominal_age} "
                  f"daxian={result.daxian_pillar} luck={result.luck_stem}{result.luck_branch}")
            for e in result.yingqi_events:
                print(f"   {e.get('year')} {e.get('domain')} {e.get('event_topic')} "
                      f"{e.get('direction')} {e.get('severity')} {e.get('mechanism')} "
                      f"{e.get('mech', '')[:60]}")
            continue

        hit, problems = _check(result, case)
        status = "PASS" if not problems else "FAIL"
        print(f"[{status}] {case['case_id']} {case['pillars']} {case['event_year']}年 "
              f"期望 {case['expected']}")
        if problems:
            failed += 1
            for p in problems:
                print(f"        {p}")
            cand = [e for e in result.yingqi_events if e.get("year") == case["event_year"]]
            for e in cand:
                print(f"        got: {e.get('domain')} {e.get('event_topic')} "
                      f"{e.get('direction')} {e.get('mechanism')}")
        else:
            for e in hit:
                print(f"        hit: {e.get('domain')} {e.get('event_topic')} "
                      f"{e.get('direction')} {e.get('mechanism')} {e.get('mech', '')[:50]}")

    print(f"\n{len(cases) - failed}/{len(cases)} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
