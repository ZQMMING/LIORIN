# -*- coding: utf-8 -*-
"""盲派「引擎签名快照」回归测试。

本层**不是真值**：快照只记录引擎当前输出签名（信号数/强度区间/结构字段/正反局），
用于发现无意漂移。语义正确性由 `tests/test_blind_truth.py`（原著明文断语 11 案）负责。

快照重录：`python scripts/blind_snapshot_record.py`（改动引擎且确认是改进后才重录）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from tongshu.engines.blind_bazi_engine import compute_blind_bazi  # noqa: E402

SNAPSHOT_FILE = _ROOT / "cases" / "golden" / "blind_engine_snapshot.json"
SNAPSHOT = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))


def _signature(result) -> dict:
    strengths = [round(float(s.strength), 4) for s in (result.signals or [])]
    return {
        "signal_count": len(result.signals or []),
        "strength_range": [min(strengths) if strengths else None,
                           max(strengths) if strengths else None],
        "has_zuo_gong": bool(result.zuo_gong_type),
        "has_main_branches": bool(result.main_branches),
        "has_guest_branches": bool(result.guest_branches),
        "has_ti_yong": bool(result.ti_branches) and bool(result.yong_branches),
        "zuo_gong_methods_count": len(result.zuo_gong_methods or []),
        "zheng_fan_ju": result.zheng_fan_ju,
    }


def test_snapshot_is_not_truth():
    """防回归：快照不得再被当成真值资产。"""
    meta = SNAPSHOT["metadata"]
    assert meta["kind"] == "engine_snapshot"
    assert "不是真值" in meta["notice"]
    assert "cases/truth/blind_truth_cases.json" in meta["notice"]
    for case in SNAPSHOT["cases"]:
        assert "expected_calculation" not in case, (
            f"{case['case_id']}: 快照不得使用 expected_calculation（真值语义只属于 cases/truth/）")


def test_truth_layer_exists_and_is_separate():
    truth = _ROOT / "cases" / "truth" / "blind_truth_cases.json"
    assert truth.is_file(), "真值层缺失：cases/truth/blind_truth_cases.json"
    data = json.loads(truth.read_text(encoding="utf-8"))
    assert data["schema"] == "blind-truth-cases-v1"
    assert len(data["cases"]) >= 11


@pytest.mark.parametrize("case", SNAPSHOT["cases"], ids=[c["case_id"] for c in SNAPSHOT["cases"]])
def test_snapshot_signature(case):
    inp = case["input"]
    result = compute_blind_bazi(
        (inp["birth_year"], inp["birth_month"], inp["birth_day"], inp["birth_hour"]),
        inp["gender"],
    )
    got = _signature(result)
    want = case["snapshot"]
    assert want, f"{case['case_id']}: 快照为空，请先跑 scripts/blind_snapshot_record.py"
    for key, expected in want.items():
        actual = got.get(key)
        assert actual == expected, (
            f"{case['case_id']} 漂移 {key}: 快照 {expected} 实得 {actual}"
            f"（确认是改进后用 scripts/blind_snapshot_record.py 重录）")
