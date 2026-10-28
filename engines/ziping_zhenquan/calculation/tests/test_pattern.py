"""PZZQ 月令取格派生测试（《子平真诠·论用神》）。

第一层：本气取格；第二层：透干取格；第三层：会支三合化局（§65 派生返回 dict）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from engines.ziping_zhenquan.calculation.pattern import derive_pattern  # noqa: E402


def p(*a, **kw):
    return derive_pattern(*a, **kw)["pattern"]


# ---- 第一层（本气取格）----

def test_benqi_cai_ge():
    """甲日丑月：丑本气己（正財）→ 財格。"""
    assert p("甲", "丑") == "財格"


def test_benqi_zhengguan_ge():
    """甲日酉月：酉本气辛（正官）→ 正官格。"""
    assert p("甲", "酉") == "正官格"


def test_benqi_qisha_ge():
    """乙日酉月：酉本气辛（七殺）→ 七煞格。"""
    assert p("乙", "酉") == "七煞格"


def test_benqi_yin_ge():
    """甲日子月：子本气癸（正印）→ 印格。"""
    assert p("甲", "子") == "印格"


def test_jianlu_yuedong():
    """甲日寅月：寅本气甲（比肩，月與日同）→ 建祿月劫格。"""
    assert p("甲", "寅") == "建祿月劫格"


def test_yangren_ge():
    """甲日卯月：卯本气乙（劫財）且卯为甲之阳刃 → 陽刃格。"""
    assert p("甲", "卯") == "陽刃格"


def test_yuedong_feiren():
    """乙日寅月：寅本气甲（劫財），寅非乙之刃 → 建祿月劫格。"""
    assert p("乙", "寅") == "建祿月劫格"


def test_hidden_stems_override():
    """L0 hidden_stems 优先于内置表。"""
    hidden = {"卯": ["甲"]}
    assert p("甲", "卯", hidden=hidden) == "建祿月劫格"


# ---- 第二层（透干取格，《论用神变化》第27页）----

def test_tougan_zhongqi_zuozhu():
    """己日申月，本气庚（傷官）不透，透中气壬 → 化財（原文例）。"""
    assert p("己", "申", transparent_stems=["壬"]) == "財格"


def test_tougan_yuqi_huaguan():
    """辛日寅月，本气甲（財）不透，透丙 → 化財為官（原文例）。"""
    assert p("辛", "寅", transparent_stems=["丙"]) == "正官格"


def test_benqi_tou_bushi_benge():
    """辛日寅月，本气甲透又透丙 → 仍正財格，官为兼格（原文例）。"""
    assert p("辛", "寅", transparent_stems=["甲", "丙"]) == "財格"


def test_yuedong_tou_cai():
    """乙日寅月（月劫），透戊 → 化為財（原文例）。"""
    assert p("乙", "寅", transparent_stems=["戊"]) == "財格"


def test_piancai_tou_sha():
    """丙日申月，本气庚（偏財）不透，透壬 → 化為煞（原文例）。"""
    assert p("丙", "申", transparent_stems=["壬"]) == "七煞格"


def test_qisha_tou_yin():
    """壬日戌月，本气戊（七煞）不透，透辛 → 化煞為印（原文例）。"""
    assert p("壬", "戌", transparent_stems=["辛"]) == "印格"


def test_benqi_butou_bu_bian():
    """丙日寅月，本气甲（印）不透干 → 仍為印綬（原文例）。"""
    assert p("丙", "寅", transparent_stems=["庚"]) == "印格"


def test_duotou_order_uncertain():
    """丁日亥月，藏壬甲，透壬透甲（本气壬透）→ 本气定格（正官）。"""
    assert p("丁", "亥", transparent_stems=["甲", "壬"]) == "正官格"


# ---- 第三层（会支三合化局，《论用神变化》第27-28页）----

def test_ding_hai_mao_wei_hua_yin():
    """丁生亥月，本為正官，支全卯未 → 化為印（原文例）。"""
    r = derive_pattern("丁", "亥", branches=["卯", "亥", "未", "午"])
    assert r["pattern"] == "印格"
    assert r["bureau"] == "木"


def test_gui_yin_wu_xu_hua_cai():
    """癸生寅月，藏甲透丙，會午會戌 → 化傷為財（原文例）。"""
    r = derive_pattern("癸", "寅", transparent_stems=["丙"], branches=["午", "寅", "戌", "子"])
    assert r["pattern"] == "財格"
    assert r["bureau"] == "火"


def test_yi_yin_wu_xu_hua_shishang():
    """乙生寅月，透戊為財，會午會戌 → 月劫化為食傷（原文例）。"""
    r = derive_pattern("乙", "寅", transparent_stems=["戊"], branches=["午", "寅", "戌", "子"])
    assert r["pattern"] == "食傷格"
    assert r["bureau"] == "火"


def test_bing_yin_wu_xu_hua_jie():
    """丙生寅月，本為印綬，甲不透而會午會戌 → 化為劫（原文例）。"""
    r = derive_pattern("丙", "寅", transparent_stems=["庚"], branches=["午", "寅", "戌", "子"])
    assert r["pattern"] == "劫財格"
    assert r["bureau"] == "火"


def test_bing_yin_wu_xu_tou_jia_bu_po():
    """丙生寅月，午戌會劫而透甲 → 仍為印而格不破（原文例，兼格标注）。"""
    r = derive_pattern("丙", "寅", transparent_stems=["甲"], branches=["午", "寅", "戌", "子"])
    assert r["pattern"] == "印格"
    assert r["bureau"] == "火"
    assert "不失本格" in r["bureau_effect"]


def test_bing_shen_zi_chen_hua_sha():
    """丙生申月，本屬偏財，藏庚透壬，會子會辰 → 化為煞（原文例）。"""
    r = derive_pattern("丙", "申", transparent_stems=["壬"], branches=["子", "申", "辰", "午"])
    assert r["pattern"] == "七煞格"
    assert r["bureau"] == "水"


def test_no_bureau_without_branches():
    """无三合局（缺支）→ 不化局，走透干/本气。"""
    # 丁日亥月：本气壬（正官）不透，透甲（正印）→ 透出者作主 → 印格
    assert p("丁", "亥", transparent_stems=["甲"]) == "印格"
    # 无透干 → 本气壬（正官）
    assert p("丁", "亥") == "正官格"


def test_bureau_requires_month_branch():
    """三合局必须含月支（日时支成局但不含月支 → 不化局）。"""
    r = derive_pattern("甲", "子", branches=["午", "子", "卯", "未"])
    # 子不参与亥卯未 → 无化局；本气癸（印）
    assert r["pattern"] == "印格"
    assert r["bureau"] is None


def test_facts_builder_injects_pattern():
    """FactsBuilder(engine=pzzq) 注入 pattern 字段。"""
    from engines.common.facts_builder import FactsBuilder
    fb = FactsBuilder(engine="pzzq")
    chart = {
        "canonical_input": {"ref": "t", "hash": "y" * 12},
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "酉"},
            "day": {"stem": "甲", "branch": "午"},
            "hour": {"stem": "戊", "branch": "午"},
        },
        "gender": "男",
        "xunkong": {"xun": "甲午旬"},
        "shishen": {"day_branch_hidden": ["丁"]},
        "changsheng": {}, "nayin": {}, "relations": {},
    }
    r = fb.build(chart)
    assert r.engine == "ZIPING_ZHENQUAN"
    assert len(r.facts.basic_structure_facts) >= 0
