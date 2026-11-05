# -*- coding: utf-8 -*-
"""盲派真值层测试（cases/truth/blind_truth_cases.json）。

真值来源 = 原典/原著明文断语案例（案例资料集 + 9例对齐反证 + 用户定稿锚点），
不是 Golden v2（引擎自证）。每案：四柱中文复核 + 关键枚举比对。

失败时的处置：只允许改引擎（或按原著明文修订 expected 并注明出处），
禁止为了让测试变绿而放宽断言口径。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402
from tongshu.engines.blind_bazi_engine import BlindBaziEngine  # noqa: E402

CASES_PATH = Path(__file__).parent.parent / "cases" / "truth" / "blind_truth_cases.json"


def _load_cases() -> list:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def _actual(result) -> dict:
    return {
        "zheng_fan_ju": result.zheng_fan_ju,
        "marriage_state": (result.marriage_event_structure or {}).get("marriage_state"),
        "wealth_state": (result.wealth_event_structure or {}).get("wealth_state"),
        "official_state": (result.official_event_structure or {}).get("official_state"),
        "body_candidate": (result.body_event_candidate or {}).get("candidate"),
    }


@pytest.mark.parametrize("case", _load_cases(), ids=[c["case_id"] for c in _load_cases()])
def test_truth_case(case):
    be = BaziEngine()
    bb = BlindBaziEngine(be)
    solar = tuple(case["solar"])
    chart = be.compute(solar, gender=case["gender"])
    pillars = chart.get_pillars_chinese()
    got_pillars = " ".join([pillars["year"], pillars["month"], pillars["day"], pillars["hour"]])
    assert got_pillars == case["pillars"], f"四柱复核失败: {got_pillars} != {case['pillars']}"

    result = bb.compute_from_chart(chart, gender=case["gender"], birth_year=solar[0])
    actual = _actual(result)
    for key, want in case["expected"].items():
        assert actual.get(key) == want, (
            f"{case['case_id']} {key}: 期望 {want} 实得 {actual.get(key)}"
            f"（原文: {case['verbatim'][:50]}…）"
        )
