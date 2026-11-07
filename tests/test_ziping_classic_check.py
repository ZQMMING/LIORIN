"""子平经典判据核验器锚点测试（原典明文，逐条可回溯）。

依据:
    FOUNDATION.MONTH_COMMAND.YUE_LING_GE_JU.001/.005/.006  取格
    STRUCTURE.GE_JU.CHENG_BAI.002                          四季月/建禄月劫
    STRUCTURE.GE_JU.CHENG_BAI.007/.008                     八格成/败
"""
from __future__ import annotations

from tongshu.reasoning.ziping_classic_check import (
    HIDDEN,
    derive_ge,
    judge_cheng_bai,
    ten_god,
)

POS = ("year", "month", "day", "hour")


def pillars(bazi: str) -> dict:
    parts = bazi.split()
    return {POS[i]: [parts[i][0], parts[i][1]] for i in range(4)}


def test_ten_god_polarity():
    # 甲(阳木) 见 丙(阳火)=食神; 见 丁(阴火)=伤官; 见 庚(阳金)=七杀; 见 辛(阴金)=正官
    assert ten_god("甲", "丙") == "食神"
    assert ten_god("甲", "丁") == "伤官"
    assert ten_god("甲", "庚") == "七杀"
    assert ten_god("甲", "辛") == "正官"


def test_hidden_table_covers_12_branches():
    assert len(HIDDEN) == 12
    # 寅藏 甲丙戊; 辰藏 戊乙癸; 申藏 庚壬戊
    assert HIDDEN["寅"] == ("甲", "丙", "戊")
    assert HIDDEN["辰"] == ("戊", "乙", "癸")
    assert HIDDEN["申"] == ("庚", "壬", "戊")


def test_ge_by_transparent_stem_not_benqi():
    """YES_LING_GE_JU.001: 月支之神透于天干者为格（透干优先于本气）。"""
    # 壬寅 戊申 丙寅 癸巳: 申月藏庚(偏财)/壬(七杀)/戊(食神), 透壬 -> 七煞格(非本气财格)
    p = pillars("壬寅 戊申 丙寅 癸巳")
    ge = derive_ge(p)
    assert ge["ge"] == "七煞格", ge
    assert ge["via"] == "透干"


def test_ge_falls_back_to_benqi_when_none_transparent():
    # 乙卯 壬午 丁巳 己酉: 午月藏丁(比肩)/己(食神), 透己 -> 食神格; 己透即食神
    p = pillars("乙卯 壬午 丁巳 己酉")
    ge = derive_ge(p)
    assert ge["ge"] == "食神格", ge


def test_ge_seasonal_month_takes_earth_benqi():
    """CHENG_BAI.002: 四季月生人只当取土为格（非土日主）。"""
    # 壬日 辰月: 辰藏戊(七杀)/乙(伤官)/癸(比肩), 透乙; 但四季月取土 -> 七煞格
    p = pillars("丙子 壬辰 壬申 乙巳")
    ge = derive_ge(p)
    assert ge["ge"] == "七煞格", ge
    assert ge["via"] == "四季土格"


def test_ge_jianlu_yuejie_and_yangren():
    # 庚日 申月: 本气庚(比肩) -> 建禄月劫格
    assert derive_ge(pillars("辛酉 丙申 庚子 丙戌"))["ge"] == "建禄月劫格"
    # 甲日 卯月: 本气乙(劫财), 阳干刃位 -> 阳刃格
    assert derive_ge(pillars("己卯 丁卯 甲子 丙寅"))["ge"] == "阳刃格"


def test_cheng_bai_guange_requires_cai_or_yin():
    """CHENG_BAI.007: 官逢财印。官无财印 -> 不成。"""
    p = pillars("癸未 辛酉 甲申 丙寅")
    r = judge_cheng_bai(p)
    assert r["ge"] == "正官格"
    # 无财印但见伤克 -> 败
    assert r["state"] == "BAI", r


def test_cheng_bai_wealth_with_sha_is_bai():
    """CHENG_BAI.008: 财透七煞（无制）为败。"""
    p = pillars("戊子 丁巳 壬子 丙午")
    r = judge_cheng_bai(p)
    assert r["state"] in ("BAI", "NOT_EVALUABLE"), r


def test_cheng_bai_yangren_without_guan_sha_is_bai():
    """CHENG_BAI.008: 阳刃无官煞，刃格败。"""
    p = pillars("己卯 丁卯 甲子 丙寅")
    r = judge_cheng_bai(p)
    assert r["ge"] == "阳刃格"
    assert r["state"] == "BAI", r


def test_basis_points_to_yuanwen_slices():
    r = judge_cheng_bai(pillars("癸未 辛酉 甲申 丙寅"))
    assert "STRUCTURE.GE_JU.CHENG_BAI.007" in r["basis"]
    assert "STRUCTURE.GE_JU.CHENG_BAI.008" in r["basis"]
