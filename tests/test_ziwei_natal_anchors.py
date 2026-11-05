# -*- coding: utf-8 -*-
"""紫微原生排盘锚点回归（不依赖 node/iztro）。

锚点来源：
1. 《紫微斗数全书》起紫微星诀原文所附三例：
   - 27 日生木三局 → 紫微在戌；
   - 13 日生火六局 → 紫微在亥；
   - 6 日生土五局 → 紫微在未。
2. 命宫/身宫口诀（寅起正月顺数生月、起子时逆/顺数生时）。
3. 十四主星安星诀（紫微逆一机、逆三阳、逆四武、逆五同、逆八廉；
   天府与紫微寅申对称、顺行太阴贪狼巨门天相天梁七杀、破军隔三）。
4. 通行本十干四化。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.ziwei_natal import (  # noqa: E402
    BRANCHES, SIHUA_BY_STEM, build_natal_chart, soul_branch, body_branch,
    fourteen_main_stars, ziwei_branch,
)


def test_ziwei_pos_textbook_examples():
    """起紫微星诀三例（原典自带验算）。"""
    assert BRANCHES[ziwei_branch(3, 27)] == "戌"   # 木三局 27 日
    assert BRANCHES[ziwei_branch(6, 13)] == "亥"   # 火六局 13 日
    assert BRANCHES[ziwei_branch(5, 6)] == "未"    # 土五局 6 日


def test_soul_body_branches():
    # 正月子时：命宫在寅、身宫在寅
    assert BRANCHES[soul_branch(1, 0)] == "寅"
    assert BRANCHES[body_branch(1, 0)] == "寅"
    # 正月午时(6)：命宫 = 寅 - 6 = 申；身宫 = 寅 + 6 = 申
    assert BRANCHES[soul_branch(1, 6)] == "申"
    assert BRANCHES[body_branch(1, 6)] == "申"
    # 七月子时：命宫 = 寅 + 6 = 申；身宫同申
    assert BRANCHES[soul_branch(7, 0)] == "申"
    assert BRANCHES[body_branch(7, 0)] == "申"


def test_fourteen_stars_layout():
    """紫微在子：天机亥、太阳酉、武曲申、天同未、廉贞辰；天府辰、太阴巳…"""
    stars = fourteen_main_stars(BRANCHES.index("子"))
    assert BRANCHES[stars["紫微"]] == "子"
    assert BRANCHES[stars["天机"]] == "亥"
    assert BRANCHES[stars["太阳"]] == "酉"
    assert BRANCHES[stars["武曲"]] == "申"
    assert BRANCHES[stars["天同"]] == "未"
    assert BRANCHES[stars["廉贞"]] == "辰"
    # 天府与紫微寅申对称：紫微子 → 天府辰；天府系顺行
    assert BRANCHES[stars["天府"]] == "辰"
    assert BRANCHES[stars["太阴"]] == "巳"
    assert BRANCHES[stars["贪狼"]] == "午"
    assert BRANCHES[stars["巨门"]] == "未"
    assert BRANCHES[stars["天相"]] == "申"
    assert BRANCHES[stars["天梁"]] == "酉"
    assert BRANCHES[stars["七杀"]] == "戌"
    assert BRANCHES[stars["破军"]] == "寅"


def test_sihua_table_classic():
    """通行本十干四化（与产品 GAN_SIHUA 同源）。SIHUA_BY_STEM 按天干序号 0=甲。"""
    expected = {
        "甲": ("廉贞", "破军", "武曲", "太阳"),
        "乙": ("天机", "天梁", "紫微", "太阴"),
        "丙": ("天同", "天机", "文昌", "廉贞"),
        "丁": ("太阴", "天同", "天机", "巨门"),
        "戊": ("贪狼", "太阴", "右弼", "天机"),
        "己": ("武曲", "贪狼", "天梁", "文曲"),
        "庚": ("太阳", "武曲", "太阴", "天同"),
        "辛": ("巨门", "太阳", "文曲", "文昌"),
        "壬": ("天梁", "紫微", "左辅", "武曲"),
        "癸": ("破军", "巨门", "太阴", "贪狼"),
    }
    from tongshu.engines.ziwei_natal import STEMS

    got = {STEMS[i]: SIHUA_BY_STEM[i] for i in range(10)}
    assert got == expected


def test_leap_month_split_rule():
    """闰月：前半月按本月、后半月按次月（与生产 fixLeap=true 同口径）。"""
    early = build_natal_chart(1995, 8, 10, 3, "male", is_leap=True)
    late = build_natal_chart(1995, 8, 18, 3, "male", is_leap=True)
    normal = build_natal_chart(1995, 8, 10, 3, "male", is_leap=False)
    assert early.soul == normal.soul                      # 前半月=本月
    assert late.soul == (normal.soul + 1) % 12            # 后半月=次月


def test_leap_month_classic_rule():
    """闰月原典口径：整体作次月（《紫微斗数全书》「凡有闰月具要依此为例」）。"""
    normal = build_natal_chart(1995, 9, 10, 3, "male", is_leap=False)
    for day in (3, 10, 18, 25):
        ch = build_natal_chart(1995, 8, day, 3, "male",
                               is_leap=True, leap_mode="classic")
        assert ch.soul == normal.soul, f"闰八月{day}日应整体作九月"
        assert ch.ju == normal.ju
    # 与默认半月口径在「前半月」上不同（这正是两口径必须显式切换的原因）
    early = build_natal_chart(1995, 8, 10, 3, "male", is_leap=True)  # half_month
    classic = build_natal_chart(1995, 8, 10, 3, "male", is_leap=True,
                               leap_mode="classic")
    assert early.soul != classic.soul
    try:
        build_natal_chart(1995, 8, 10, 3, "male", is_leap=True, leap_mode="bogus")
    except ValueError as exc:
        assert "leap_mode" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("非法 leap_mode 必须报错")


def test_twelve_gods_start_and_direction():
    """四组十二神起例与顺逆（阳男阴女顺、阴男阳女逆）。"""
    from tongshu.engines.ziwei_natal import BRANCHES, CS12

    # 1990-1-1 子时：命宫寅（戊寅纳音土）→ 土五局，长生在申；庚年阳男顺行
    ch = build_natal_chart(1990, 1, 1, 0, "male")
    assert ch.ju == 5
    cs = ch.twelve_gods["changsheng"]
    assert cs[BRANCHES.index("申")] == "长生"
    assert cs[BRANCHES.index("酉")] == "沐浴"
    # 同盘女命（阳女）逆行
    chf = build_natal_chart(1990, 1, 1, 0, "female")
    cs_f = chf.twelve_gods["changsheng"]
    assert cs_f[BRANCHES.index("申")] == "长生"
    assert cs_f[BRANCHES.index("未")] == "沐浴"
    # 博士自禄存起（庚禄在申）
    assert ch.twelve_gods["boshi"][BRANCHES.index("申")] == "博士"
    # 岁前自年支起（庚午：午=岁建）
    assert ch.twelve_gods["suiqian"][BRANCHES.index("午")] == "岁建"
    # 将前自三合帝旺起（寅午戌将星在午）
    assert ch.twelve_gods["jiangqian"][BRANCHES.index("午")] == "将星"
    assert len(CS12) == 12
