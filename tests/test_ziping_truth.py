# -*- coding: utf-8 -*-
"""子平真值层测试: 原典四柱 → 公历 → 引擎 → 原典结论。

真值资产 cases/truth/ziping_truth_cases.json（沈孝瞻《子平真诠》原文 + 穷通宝鉴调候双证）。
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402
from tongshu.reasoning.ziping_v3.runner import run_ziping  # noqa: E402

TRUTH = REPO / "cases" / "truth" / "ziping_truth_cases.json"


def _load_replay():
    path = REPO / "scripts" / "ziping_truth_replay.py"
    spec = importlib.util.spec_from_file_location("ziping_truth_replay", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DATA = json.loads(TRUTH.read_text(encoding="utf-8"))
CASES = DATA["cases"]


def test_truth_asset_shape():
    assert DATA["schema"] == "ziping-truth-cases-v1"
    assert DATA["primary_source"]
    ids = [c["case_id"] for c in CASES + DATA.get("conflicts", [])]
    assert len(ids) == len(set(ids)), "case_id 必须唯一"
    for case in CASES:
        assert case["pillars"].count(" ") == 3, "四柱必须是四个干支"
        assert case["source"], "每条真值必须带原典出处"
        assert case["verbatim"], "每条真值必须带原文"
        assert case["expected"], "断言案必须有 expected"


def test_conflicts_are_not_asserted():
    asserted = {c["case_id"] for c in CASES}
    for c in DATA.get("conflicts", []):
        assert c["case_id"] not in asserted, "两说冲突案不得进入断言"
        assert c["shen_yongshen"] and c["tiaohou_yongshen"]
        assert c["data_issue"], "冲突案必须登记 data_issue"


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_case_against_classical_text(case):
    """四柱求解 → 引擎 → 与原典结论逐字段比对。"""
    mod = _load_replay()
    hits = mod.solve(case["pillars"])
    assert hits, f"四柱无解: {case['pillars']}"
    y, m, d, h = hits[0]
    chart = BaziEngine().compute((y, m, d, h), gender="male")
    # 排盘层四柱复核 (年界/立春)
    pc = chart.get_pillars_chinese()
    assert [pc["year"], pc["month"], pc["day"], pc["hour"]] == case["pillars"].split()
    got = mod.actual(run_ziping(chart, enable_pattern=True))
    for key, want in case["expected"].items():
        assert got.get(key) == want, (
            f"{case['name']} {key}: 引擎={got.get(key)} 原典={want} "
            f"(依据 {got.get('yongshen_basis')})")
