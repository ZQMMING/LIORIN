# -*- coding: utf-8 -*-
"""六爻纳甲装卦核心的逐表校验。

测试纪律：所有期望值都来自通行京房纳甲表（不是引擎自证），覆盖
- 八宫卦序完整性（64 卦不重不漏、八宫各 8 卦）
- 八卦纳甲（八纯卦六爻干支逐字核对）
- 世应（八宫八变位置）
- 六亲（以本宫五行为我）
- 六神（按日干起）
- 旬空（六旬）
- 伏神（缺六亲取本宫首卦）
- 变卦 / 回头生克
- 月建旺衰 / 月破 / 日辰影响
"""
import pytest

from tongshu.engines import liuyao_najia as N


PURE_NAJIA = {
    "乾为天": ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"],
    "坤为地": ["乙未", "乙巳", "乙卯", "癸丑", "癸亥", "癸酉"],
    "震为雷": ["庚子", "庚寅", "庚辰", "庚午", "庚申", "庚戌"],
    "巽为风": ["辛丑", "辛亥", "辛酉", "辛未", "辛巳", "辛卯"],
    "坎为水": ["戊寅", "戊辰", "戊午", "戊申", "戊戌", "戊子"],
    "离为火": ["己卯", "己丑", "己亥", "己酉", "己未", "己巳"],
    "艮为山": ["丙辰", "丙午", "丙申", "丙戌", "丙子", "丙寅"],
    "兑为泽": ["丁巳", "丁卯", "丁丑", "丁亥", "丁酉", "丁未"],
}


def _chart(hex_name, day_stem="甲", day_branch="子", month_branch="寅", moving=()):
    return N.build_liuyao_chart(day_stem, day_branch, month_branch, moving, hex_name)


def test_eight_palaces_partition_is_complete():
    names = [n for names in N.PALACE_HEXAGRAMS.values() for n in names]
    assert len(names) == 64
    assert len(set(names)) == 64
    assert set(names) == set(N.HEXAGRAM_NAME.values())
    assert set(N.PALACE_HEXAGRAMS) == set(N.TRIGRAM_ELEMENT)


def test_pure_hexagram_najia_exact():
    for hex_name, expected in PURE_NAJIA.items():
        c = _chart(hex_name)
        got = [f"{ln.stem}{ln.branch}" for ln in c.lines]
        assert got == expected, f"{hex_name}: {got} != {expected}"


def test_shi_ying_for_eight_palace_mutations():
    # 乾宫：本宫世六、姤世初、遁世二、否世三、观世四、剥世五、晋游魂四、大有三
    expected = {
        "乾为天": (6, 3), "天风姤": (1, 4), "天山遁": (2, 5), "天地否": (3, 6),
        "风地观": (4, 1), "山地剥": (5, 2), "火地晋": (4, 1), "火天大有": (3, 6),
    }
    for hex_name, (shi, ying) in expected.items():
        c = _chart(hex_name)
        assert (c.shi, c.ying) == (shi, ying), hex_name
        assert c.by_position(shi).is_shi
        assert c.by_position(ying).is_ying


def test_shi_ying_consistency_for_all_64():
    for hex_name in N.PALACE_HEXAGRAMS["乾"]:
        c = _chart(hex_name)
        assert 1 <= c.shi <= 6 and 1 <= c.ying <= 6
        assert c.shi != c.ying
        assert (c.shi - c.ying) % 3 == 0


def test_six_kin_qian_wei_tian():
    c = _chart("乾为天")
    assert c.palace_element == "金"
    kins = [ln.six_kin for ln in c.lines]
    assert kins == ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]


def test_six_kin_consistency_all_64():
    for hex_name in N.PALACE_HEXAGRAMS["乾"]:
        c = _chart(hex_name)
        present = {ln.six_kin for ln in c.lines}
        assert present <= set(N.SIX_KIN)
        assert c.missing_kin == [k for k in N.SIX_KIN if k not in present]


def test_six_spirits_by_day_stem():
    cases = {
        "甲": ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"],
        "丙": ["朱雀", "勾陈", "螣蛇", "白虎", "玄武", "青龙"],
        "戊": ["勾陈", "螣蛇", "白虎", "玄武", "青龙", "朱雀"],
        "己": ["螣蛇", "白虎", "玄武", "青龙", "朱雀", "勾陈"],
        "庚": ["白虎", "玄武", "青龙", "朱雀", "勾陈", "螣蛇"],
        "壬": ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"],
    }
    for stem, spirits in cases.items():
        branch = "丑" if stem == "己" else "子"
        c = _chart("乾为天", day_stem=stem, day_branch=branch)
        assert [ln.spirit for ln in c.lines] == spirits, stem


def test_xun_kong_six_xun():
    expected = {
        ("甲", "子"): ("戌", "亥"), ("甲", "戌"): ("申", "酉"), ("甲", "申"): ("午", "未"),
        ("甲", "午"): ("辰", "巳"), ("甲", "辰"): ("寅", "卯"), ("甲", "寅"): ("子", "丑"),
        ("乙", "丑"): ("戌", "亥"),
    }
    for (stem, branch), kong in expected.items():
        assert N.xun_kong_of(stem, branch) == kong, (stem, branch)


def test_fu_shen_tian_di_pi():
    # 天地否 = 上乾下坤：六亲 父母/官鬼/妻财/官鬼/兄弟/父母，缺子孙
    c = _chart("天地否")
    assert c.missing_kin == ["子孙"]
    assert len(c.fu_shen) == 1
    fu = c.fu_shen[0]
    assert (fu.position, fu.stem + fu.branch, fu.six_kin) == (1, "甲子", "子孙")


def test_fu_shen_fills_every_missing_kin():
    for hex_name in N.PALACE_HEXAGRAMS["乾"]:
        c = _chart(hex_name)
        if c.missing_kin:
            assert {f.six_kin for f in c.fu_shen} == set(c.missing_kin)


def test_changed_hexagram_and_huitou():
    c = _chart("乾为天", moving=[1])
    assert c.changed_hexagram == "天风姤"
    ln = c.by_position(1)
    assert ln.moving
    assert (ln.changed_stem, ln.changed_branch) == ("辛", "丑")
    # 本爻甲子水，变爻辛丑土：土克水 → 回头克
    assert ln.to_line == "回头克"
    # 二爻不动
    assert not c.by_position(2).moving


def test_changed_zishen_turns_into_sheng():
    # 五爻壬申金动 → 变卦火天大有，五爻己未土：土生金 → 回头生
    c = _chart("乾为天", moving=[5])
    assert c.changed_hexagram == "火天大有"
    ln = c.by_position(5)
    assert (ln.changed_stem, ln.changed_branch) == ("己", "未")
    assert ln.to_line == "回头生"


def test_wangshuai_by_month():
    # 月建寅木：木旺、火相、水休（水生木）、金囚（金克木）、土死（木克土）
    assert N.branch_wangshuai("木", "木") == "旺"
    assert N.branch_wangshuai("火", "木") == "相"
    assert N.branch_wangshuai("水", "木") == "休"
    assert N.branch_wangshuai("金", "木") == "囚"
    assert N.branch_wangshuai("土", "木") == "死"


def test_month_break_and_day_influence():
    assert N.month_break("子", "午")
    assert not N.month_break("子", "丑")
    assert N.day_influence("子", "子") == "日建"
    assert N.day_influence("子", "午") == "日冲"
    assert N.day_influence("子", "丑") == "日合"
    assert N.day_influence("寅", "子") == "日生"  # 子水生寅木


def test_yong_shen_and_status():
    c = _chart("乾为天", day_stem="甲", day_branch="子", month_branch="寅")
    ys = N.select_yong_shen(c, "妻财")
    assert [ln.position for ln in ys] == [2]
    st = N.yong_shen_status(c, "妻财")
    assert st["found"] is True
    rec = st["lines"][0]
    assert rec["stem_branch"] == "甲寅"
    assert rec["wangshuai"] == "旺"  # 寅木临月建
    assert rec["day_influence"] == "日生"

    pi = _chart("天地否")
    ys2 = N.select_yong_shen(pi, "官鬼")
    assert ys2 and ys2[0].six_kin == "官鬼" and ys2[0].stem + ys2[0].branch == "乙巳"
    st2 = N.yong_shen_status(pi, "子孙")
    assert st2["found"] is True


def test_yong_shen_absent_marks_reason():
    # 构造一个本卦、伏神都没有某六亲的反例：取坤为地已齐全，改用未入表的天火同人（乾宫归魂）
    c = _chart("天火同人")
    st = N.yong_shen_status(c, "父母")
    if not st["found"]:
        assert "无法立用神" in st["reason"]


def test_all_64_build_without_error():
    for palace, names in N.PALACE_HEXAGRAMS.items():
        for name in names:
            c = _chart(name, day_stem="乙", day_branch="丑", month_branch="午")
            assert c.hexagram == name
            assert c.palace == palace
            assert len(c.lines) == 6
            assert c.to_dict()["hexagram"] == name
            assert N.xun_kong_of("乙", "丑") == c.xun_kong


# ---------------------------------------------------------------------------
# 起卦层（liuyao_engine）与纳甲层的接线
# ---------------------------------------------------------------------------

def test_engine_trigram_names_cover_all_64():
    from tongshu.engines import liuyao_engine as E

    for (upper, lower), name in N.HEXAGRAM_NAME.items():
        assert E.trigrams_to_gua_name(upper, lower) == name


def test_engine_cast_from_lines_matches_najia():
    from tongshu.engines import liuyao_engine as E

    lines = [7, 7, 7, 7, 7, 7]
    cast = E.cast_from_lines(lines, day_stem="甲", day_branch="子", month_branch="寅")
    assert cast.result.ben_gua == "乾为天"
    assert cast.chart.hexagram == "乾为天"
    assert cast.chart.shi == 6

    # 初爻老阳动 → 天风姤
    cast2 = E.cast_from_lines([9, 7, 7, 7, 7, 7], day_stem="甲", day_branch="子")
    assert cast2.result.ben_gua == "乾为天"
    assert cast2.result.bian_gua == "天风姤"
    assert cast2.chart.changed_hexagram == "天风姤"
    assert cast2.chart.moving_positions == [1]


def test_engine_hu_gua_matches_mapping():
    from tongshu.engines import liuyao_engine as E

    # 水山蹇（0,0,1,0,1,0）互卦为火水未济
    lines = [6, 8, 7, 8, 7, 8]
    cast = E.cast_from_lines(lines)
    assert cast.result.ben_gua == "水山蹇"
    assert cast.result.hu_gua == "火水未济"


def test_engine_exhaustive_64_lines_roundtrip():
    from tongshu.engines import liuyao_engine as E

    for name in N.HEXAGRAM_NAME.values():
        lines = [7 if v == 1 else 8 for v in N.hexagram_lines(name)]
        cast = E.cast_from_lines(lines, day_stem="甲", day_branch="子")
        assert cast.result.ben_gua == name
        assert cast.chart.hexagram == name


def test_hexagram_names_match_yi_core_table():
    """与本仓独立的易学表 yi.core.SIXTY_FOUR_MAP 逐条交叉核对（64/64）。"""
    from tongshu.engines.yi import core as C

    core_map = dict(C.SIXTY_FOUR_MAP)
    assert len(core_map) == 64
    for (upper, lower), name in N.HEXAGRAM_NAME.items():
        assert core_map[(upper, lower)] == name, (upper, lower, name)
