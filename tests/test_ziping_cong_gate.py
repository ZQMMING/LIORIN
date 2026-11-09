# -*- coding: utf-8 -*-
"""从格门控：印透干且有根 -> 不从（子平真诠「印无根不得相从」反证）。"""
from __future__ import annotations
import pytest
from engines.production_entry import FrozenCanonicalBaziChart, production_entry


def _ge(pillars: dict) -> dict:
    r = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    return (r.get("engine_result") or {}).get("ge_cheng") or {}


def test_yin_tou_with_root_blocks_cong_er():
    # PZZQ 002 戊子 癸亥 庚寅 戊寅：戊印透干、寅中戊余气根 -> 沈断「泄气太重取戊土扶身制伤」= 正格
    gc = _ge({"year": ["戊", "子"], "month": ["癸", "亥"], "day": ["庚", "寅"], "hour": ["戊", "寅"]})
    assert gc.get("cong_type") in (None, ""), gc
    assert "从" not in str(gc.get("ge", "")), gc
    assert gc.get("ge") in ("食神格", "伤官格"), gc


def test_cong_state_confirmed_requires_no_yin_root():
    # 抗回归：若从格成立必须 cong_state == CONFIRMED 且带 cong_type（二者同现）
    gc = _ge({"year": ["戊", "子"], "month": ["癸", "亥"], "day": ["庚", "寅"], "hour": ["戊", "寅"]})
    if gc.get("cong_type"):
        assert gc.get("cong_state") == "CONFIRMED"
    else:
        assert gc.get("cong_state") in (None, "")
