"""PZZQ 格成格败 Judgment 测试（Phase 7 §66 ·《论用神成败救应》）。

原文例验证（PZZQ-005-008）：
- 官格成「官逢財印」→ 官印雙全 → 成
- 財格敗「財透七煞」→ 財透七煞 → 敗
- 食格敗「食神逢梟」→ 食神逢梟 → 敗
- 建祿月劫成「透官而逢財印」→ 透官而逢財印 → 成
- 傷官格敗「非金水而見官」→ 非金水而見官 → 敗
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.common.facts_builder import FactsBuilder  # noqa: E402
from engines.ziping_zhenquan.judgment.judgment_builder import (  # noqa: E402
    JudgmentBuilder, _synthesize_conditions,
)


def build_view(pillars):
    """跑 FactsBuilder 得到 view + facts。"""
    fb = FactsBuilder(engine="pzzq")
    chart = {
        "canonical_input": {"ref": "t", "hash": "x" * 12},
        "pillars": pillars,
        "gender": "男",
        "xunkong": {"xun": "甲午旬"},
        "shishen": {},
        "changsheng": {}, "nayin": {}, "relations": {},
    }
    return fb.build(chart)


def test_guan_feng_cai_yin_cheng():
    """官逢財印 → 官印雙全 → 成（原文「官逢財印，官格成也」）。"""
    # 甲日酉月（正官格）：正官透（月干辛）、财透（时干戊）、印透（年干癸）
    res = build_view({
        "year": {"stem": "癸", "branch": "卯"},
        "month": {"stem": "辛", "branch": "酉"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "戊", "branch": "午"},
    })
    view = res.metadata["view"]
    assert view["pattern"] == "正官格"
    j = JudgmentBuilder().build(res)
    vals = {x["condition"]: x["value"] for x in j}
    assert "官印雙全" in vals and vals["官印雙全"] == "成"


def test_cai_tou_qisha_bai():
    """財透七煞 → 敗（原文「財透七煞，財格敗也」）。"""
    # 甲日丑月（財格）：财透（时干戊）、七杀透（年干庚）
    res = build_view({
        "year": {"stem": "庚", "branch": "寅"},
        "month": {"stem": "己", "branch": "丑"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "戊", "branch": "午"},
    })
    view = res.metadata["view"]
    assert view["pattern"] == "財格"
    j = JudgmentBuilder().build(res)
    vals = {x["condition"]: x["value"] for x in j}
    assert "財透七煞" in vals and vals["財透七煞"] == "敗"


def test_shishen_feng_xiao_bai():
    """食神逢梟 → 敗（原文「食神逢梟，食神格敗也」）。"""
    # 甲日巳月（食神格：巳本气丙）：食神透（月干丙）、枭透（年干壬）
    res = build_view({
        "year": {"stem": "壬", "branch": "子"},
        "month": {"stem": "丙", "branch": "巳"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "戊", "branch": "寅"},
    })
    j = JudgmentBuilder().build(res)
    vals = {x["condition"]: x["value"] for x in j}
    assert "食神逢梟" in vals and vals["食神逢梟"] == "敗"


def test_shangguan_feijinshui_jian_guan_bai():
    """傷官非金水而見官 → 敗（原文「傷官非金水而見官，傷官格敗也」）。"""
    # 甲日午月（傷官格：午本气丁）：伤官透（月干丁）、正官透（年干辛）——甲非金水
    res = build_view({
        "year": {"stem": "辛", "branch": "亥"},
        "month": {"stem": "丁", "branch": "午"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "戊", "branch": "寅"},
    })
    j = JudgmentBuilder().build(res)
    vals = {x["condition"]: x["value"] for x in j}
    assert "非金水而見官" in vals and vals["非金水而見官"] == "敗"


def test_jianlu_tou_guan_cai_yin_cheng():
    """建祿月劫透官逢財印 → 成（原文「建祿月劫透官而逢財印，成也」）。"""
    # 甲日寅月（建祿月劫格）：本气甲，透官（辛，非寅藏干）、财（己）、印（癸）
    # 注：透戊（寅余气）会作主为財格，故用己财构造建祿例
    res = build_view({
        "year": {"stem": "癸", "branch": "亥"},
        "month": {"stem": "辛", "branch": "寅"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "己", "branch": "巳"},
    })
    view = res.metadata["view"]
    assert view["pattern"] == "建祿月劫格"
    j = JudgmentBuilder().build(res)
    vals = {x["condition"]: x["value"] for x in j}
    assert "透官而逢財印" in vals and vals["透官而逢財印"] == "成"


def test_evidence_chain():
    """judgment 带 source_ids（PZZQ-005-008）与触发 fact_ids。"""
    res = build_view({
        "year": {"stem": "庚", "branch": "寅"},
        "month": {"stem": "己", "branch": "丑"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "戊", "branch": "午"},
    })
    j = JudgmentBuilder().build(res)
    assert j
    for x in j:
        assert "PZZQ-005-008" in x["source_ids"]
        assert x["fact_ids"]
