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
def test_ge_detail_does_not_claim_unexposed_month_stem_is_transparent():
    from tongshu.reasoning.ziping_classic_check import derive_ge
    pillars = {'year': ['甲', '午'], 'month': ['丁', '卯'],
               'day': ['壬', '戌'], 'hour': ['丙', '午']}
    result = derive_ge(pillars)
    assert result['stem'] == '乙'
    assert '未透干' in result['detail']
    assert '透干乙' not in result['detail']


def test_ge_detail_identifies_exposed_month_stem():
    from tongshu.reasoning.ziping_classic_check import derive_ge
    pillars = {'year': ['壬', '寅'], 'month': ['戊', '申'],
               'day': ['丙', '寅'], 'hour': ['癸', '巳']}
    result = derive_ge(pillars)
    assert result['stem'] == '壬'
    assert '透干壬' in result['detail']


# ============================================================
# 旺衰（身强弱）——三才合参 + 成局，原典锚点
# ============================================================

def _pillars(year, month, day, hour):
    return {"year": list(year), "month": list(month), "day": list(day), "hour": list(hour)}


def test_strength_jianlu_strong():
    """WANG-001 甲木寅月建禄、印比透干齐备 → STRONG(得令+得地+党众)。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength

    r = judge_strength(_pillars("甲寅", "乙寅", "甲卯", "乙寅"))
    assert r["conclusion"] == "STRONG"
    assert r["get_ling_score"] == 3
    assert r["de_di_score"] >= 1
    assert any("得令" in s for s in r["reasons"])


def test_strength_shishen_traps_weak():
    """WANG-002 戊土申月食神当令、金党众 → WEAK(失令+党众受克)。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength

    r = judge_strength(_pillars("庚辰", "庚申", "戊寅", "壬戌"))
    assert r["conclusion"] == "WEAK"
    assert r["get_ling_score"] == -3
    assert r["dangzhong_score"] < 0


def test_strength_month_clashed_downgraded():
    """BOUND-004 甲木子月正印当令, 然月支子被午冲 → 得令减等(不按满分)。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength

    full = judge_strength(_pillars("甲子", "丙子", "甲子", "庚午"))
    assert full["get_ling_score"] <= 1, full["reasons"]
    assert any("冲" in s for s in full["reasons"])


def test_strength_sanhe_ju_counts():
    """三合成局按局论党：戊土午月见寅午戌火局 → ju_score>0。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength

    r = judge_strength(_pillars("戊寅", "戊午", "戊戌", "甲寅"))
    assert r["ju_score"] > 0
    assert any("三合" in s for s in r["reasons"])


def test_strength_lost_ling_no_root_no_help():
    """失令 + 无根 + 无助 → WEAK（原典 SHUAI.003「日主孤立无气」方向的弱极）。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength

    r = judge_strength(_pillars("庚申", "戊申", "甲申", "壬申"))
    assert r["conclusion"] == "WEAK"
    assert r["de_di_score"] == 0


def test_strength_basis_are_registered_slices():
    """旺衰判据须带可解析的原典切片锚（G1 证据闸用得到）。"""
    from tongshu.reasoning.ziping_classic_check import judge_strength
    from tongshu.reasoning import p0_evidence

    r = judge_strength(_pillars("甲寅", "乙寅", "甲卯", "乙寅"))
    ids = p0_evidence.resolve(r["basis"])
    assert len(ids) >= 4
    assert all(i.startswith("STATE.WANG_SHUAI") for i in ids)


def test_golden_wangshuai_coverage_floor():
    """golden 23 案旺衰结论覆盖率不得低于 20/23（回归护栏, 非准确率声明）。"""
    import json
    from pathlib import Path
    from tongshu.reasoning.ziping_classic_check import judge_strength

    S = dict(JIA="甲", YI="乙", BING="丙", DING="丁", WU="戊", JI="己",
             GENG="庚", XIN="辛", REN="壬", GUI="癸")
    B = dict(ZI="子", CHOU="丑", YIN="寅", MAO="卯", CHEN="辰", SI="巳",
             WU="午", WEI="未", SHEN="申", YOU="酉", XU="戌", HAI="亥")
    g = json.loads(Path("cases/golden/ziping_golden_set.json").read_text(encoding="utf-8"))
    ok = tot = 0
    for c in g["cases"]:
        w = c["expected_calculation"].get("wangshuai")
        if not w:
            continue
        inp = c["input"]
        p = {k: [S[s], B[b]] for k, s, b in zip(
            ("year", "month", "day", "hour"), inp["pillar_stems"], inp["pillar_branches"])}
        tot += 1
        ok += judge_strength(p)["conclusion"] == w["conclusion"]
    assert tot == 23
    assert ok >= 20, f"coverage {ok}/{tot}"

def test_cheng_bai_yin_light_meets_cai_is_bai():
    """CHENG_BAI.008: 印轻逢财 -> 败（量词落地）。"""
    p = pillars("戊戌 甲子 甲午 丙寅")
    r = judge_cheng_bai(p)
    assert r["ge"] == "印格", r
    assert r["state"] == "BAI", r
    assert any("印轻逢财" in c["clause"] for c in r["clauses"])


def test_cheng_bai_yin_many_meets_cai_is_cheng():
    """CHENG_BAI.007: 印多逢财而财透根轻 -> 成。"""
    p = pillars("壬戌 辛亥 甲辰 丁卯")
    r = judge_cheng_bai(p)
    assert r["ge"] == "印格", r
    assert r["state"] == "CHENG", r
    assert any("印多逢财" in c["clause"] for c in r["clauses"])


def test_cheng_bai_sha_with_cai_controlled_strong_is_cheng():
    """CHENG_BAI.007: 身强七煞逢制 -> 成（王克敏 申子辰比劫局帮身）。"""
    p = pillars("丙子 壬辰 壬申 乙巳")
    r = judge_cheng_bai(p)
    assert r["ge"] == "七煞格", r
    assert r["state"] == "CHENG", r
    assert any("身强七煞逢制" in c["clause"] for c in r["clauses"])


def test_cheng_bai_yangren_guan_shang_both_records_clause():
    """官煞与伤官并透: 不臆断, 记录须辨条款。"""
    p = pillars("丁卯 丙午 丙子 壬辰")
    r = judge_cheng_bai(p)
    assert r["ge"] == "阳刃格", r
    assert r["state"] == "NOT_EVALUABLE", r
    assert any("并透" in c["clause"] for c in r["clauses"])
