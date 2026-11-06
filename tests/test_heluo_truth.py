# -*- coding: utf-8 -*-
"""河洛真值层测试：原典案例逐案回放（对 cases/truth/heluo_truth_cases.json）。

纪律：expected 来自原典/假令复算，不是引擎自证；任何一条不符都应修引擎，不得改 expected。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tongshu.engines.heluo.canonical import HeluoCanonical

CASES_PATH = Path(__file__).resolve().parent.parent / "cases" / "truth" / "heluo_truth_cases.json"
_DATA = json.loads(CASES_PATH.read_text(encoding="utf-8"))
CASES = _DATA["cases"]


@pytest.fixture(scope="module")
def canonical() -> HeluoCanonical:
    return HeluoCanonical()


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_original_text_case(case, canonical):
    result = canonical.calculate(
        [(g, z) for g, z in case["bazi"]],
        case["gender"],
        case["birth_hour"],
        case["era"],
        birth_year=case["birth_year"],
    )
    actual = {
        "tian_shu": result.numbers.tian_shu,
        "di_shu": result.numbers.di_shu,
        "tian_reduced": result.numbers.tian_reduced,
        "di_reduced": result.numbers.di_reduced,
        "prenatal": result.prenatal.hexagram_name,
        "yuantang": result.yuantang.yuantang,
        "yuantang_index": result.yuantang.yuantang_index,
        "postnatal": result.postnatal.hexagram_name,
    }
    for key, want in case["expected"].items():
        assert actual[key] == want, f"{case['case_id']} {key}: got={actual[key]!r} want={want!r}"


def test_truth_cases_are_sourced():
    """每条真值必须带原典出处与原文摘录，防止未来被改成引擎自证。"""
    for case in CASES:
        assert case["source"], case["case_id"]
        assert case["verbatim"], case["case_id"]
        assert case["expected"], case["case_id"]


def test_truth_cases_distinct_bazi():
    seen = set()
    for case in CASES:
        key = tuple(tuple(p) for p in case["bazi"])
        assert key not in seen, f"重复四柱：{key}"
        seen.add(key)
