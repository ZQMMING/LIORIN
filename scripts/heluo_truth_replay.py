# -*- coding: utf-8 -*-
"""河洛真值回放：逐案跑引擎，比对原典 expected（不是引擎自证）。

用法：
    python scripts/heluo_truth_replay.py            # 全量回放
    python scripts/heluo_truth_replay.py --filter 1980
    python scripts/heluo_truth_replay.py --dump heluo-002   # 打印单案全字段
退出码：全部通过 0，任何不符 1。
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
CASES_PATH = REPO / "cases" / "truth" / "heluo_truth_cases.json"

sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical  # noqa: E402


def _actual(result) -> dict:
    return {
        "tian_shu": result.numbers.tian_shu,
        "di_shu": result.numbers.di_shu,
        "tian_reduced": result.numbers.tian_reduced,
        "di_reduced": result.numbers.di_reduced,
        "prenatal": result.prenatal.hexagram_name,
        "yuantang": result.yuantang.yuantang,
        "yuantang_index": result.yuantang.yuantang_index,
        "postnatal": result.postnatal.hexagram_name,
    }


def _bazi(raw) -> list[tuple[str, str]]:
    return [(g, z) for g, z in raw]


def run_case(case, canonical: HeluoCanonical) -> tuple[bool, list[str], dict]:
    result = canonical.calculate(
        _bazi(case["bazi"]),
        case["gender"],
        case["birth_hour"],
        case["era"],
        birth_year=case["birth_year"],
    )
    actual = _actual(result)
    expected = case["expected"]
    problems = []
    for key, want in expected.items():
        got = actual.get(key)
        if got != want:
            problems.append(f"{key}: got={got!r} want={want!r}")
    return (not problems), problems, actual


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="", help="按 case_id / label 子串过滤")
    ap.add_argument("--dump", default="", help="打印指定 case_id 的全部字段")
    args = ap.parse_args()

    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    canonical = HeluoCanonical()

    if args.dump:
        for case in cases:
            if case["case_id"] == args.dump:
                _, _, actual = run_case(case, canonical)
                print(json.dumps(actual, ensure_ascii=False, indent=2))
                return 0
        print(f"未找到 case_id={args.dump}")
        return 2

    if args.filter:
        cases = [c for c in cases if args.filter in c["case_id"] or args.filter in c["label"]]

    total = 0
    passed = 0
    for case in cases:
        total += 1
        ok, problems, actual = run_case(case, canonical)
        if ok:
            passed += 1
            print(f"[PASS] {case['case_id']} {case['label']}")
        else:
            print(f"[FAIL] {case['case_id']} {case['label']}")
            for p in problems:
                print(f"        {p}")
            print(f"        actual={json.dumps(actual, ensure_ascii=False)}")

    print(f"\n{passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
