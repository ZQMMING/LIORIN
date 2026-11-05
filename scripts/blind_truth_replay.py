# -*- coding: utf-8 -*-
"""盲派真值回放（Truth Replay）。

用原典/原著明文案例（cases/truth/blind_truth_cases.json）逐案回放盲派引擎：
四柱 → 求解公历日（已存于 case.solar，回放前再次校验四柱一致）→ BaziEngine →
BlindBaziEngine → 比对 expected 枚举。

输出每案 PASS/FAIL 与残差字段（expected vs actual），exit 1 表示存在残差。
真值口径：只有带原文断语的案例才进本层；Golden v2（引擎自证）不作为真值。

用法:
    python scripts/blind_truth_replay.py            # 全量
    python scripts/blind_truth_replay.py --filter blind-00   # 按 id 前缀过滤
    python scripts/blind_truth_replay.py --dump blind-009     # 打印案例全部做功表
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402
from tongshu.engines.blind_bazi_engine import BlindBaziEngine  # noqa: E402

CASES_PATH = ROOT / "cases" / "truth" / "blind_truth_cases.json"


def _pillar_str(chart) -> str:
    """四柱中文串（BaziChart 的 *_pillar 字段是拼音键, 用 get_pillars_chinese 还原）。"""
    if hasattr(chart, "get_pillars_chinese"):
        p = chart.get_pillars_chinese()
        return " ".join([p["year"], p["month"], p["day"], p["hour"]])
    return " ".join([
        chart.year_pillar.heavenly_stem + chart.year_pillar.earthly_branch,
        chart.month_pillar.heavenly_stem + chart.month_pillar.earthly_branch,
        chart.day_pillar.heavenly_stem + chart.day_pillar.earthly_branch,
        chart.hour_pillar.heavenly_stem + chart.hour_pillar.earthly_branch,
    ])


def _actual(result) -> dict:
    marriage = getattr(result, "marriage_event_structure", {}) or {}
    wealth = getattr(result, "wealth_event_structure", {}) or {}
    official = getattr(result, "official_event_structure", {}) or {}
    body = getattr(result, "body_event_candidate", {}) or {}
    return {
        "zheng_fan_ju": result.zheng_fan_ju,
        "marriage_state": marriage.get("marriage_state"),
        "wealth_state": wealth.get("wealth_state"),
        "official_state": official.get("official_state"),
        "body_candidate": body.get("candidate"),
    }


def _dump(result) -> None:
    print("  做功表:")
    for m, a, d in zip(result.zuo_gong_methods, result.zuo_gong_attributions,
                       result.zuo_gong_detail):
        print(f"    {m} | {a} | {d}")
    print(f"  势: {result.shi_direction} / {result.shi_zhi_jing} / eff={result.work_efficiency}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="")
    ap.add_argument("--dump", default="")
    args = ap.parse_args()

    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    be = BaziEngine()
    bb = BlindBaziEngine(be)

    total = passed = 0
    rows = []
    for case in data["cases"]:
        cid = case["case_id"]
        if args.filter and not cid.startswith(args.filter):
            continue
        total += 1
        solar = tuple(case["solar"])
        gender = case["gender"]
        chart = be.compute(solar, gender=gender)
        actual_pillars = _pillar_str(chart)
        if actual_pillars != case["pillars"]:
            rows.append((cid, "PILLAR_MISMATCH", f"期望 {case['pillars']} 实得 {actual_pillars}"))
            continue
        result = bb.compute_from_chart(chart, gender=gender, birth_year=solar[0])
        actual = _actual(result)
        mismatches = []
        for key, want in case["expected"].items():
            got = actual.get(key)
            if got != want:
                mismatches.append(f"{key}: 期望 {want} 实得 {got}")
        if args.dump and cid.startswith(args.dump):
            _dump(result)
        if mismatches:
            rows.append((cid, "FAIL", "; ".join(mismatches)))
        else:
            passed += 1
            rows.append((cid, "PASS", ""))

    print(f"{'案例':<14}{'结果':<8}残差")
    print("-" * 78)
    for cid, status, detail in rows:
        print(f"{cid:<14}{status:<8}{detail}")
    print("-" * 78)
    print(f"真值回放: {passed}/{total} PASS"
          + ("" if passed == total else f"，{total - passed} 案存在残差"))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
