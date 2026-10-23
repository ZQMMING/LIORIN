"""Bazi 十神 (ten gods) + 地支藏干 (hidden stems) — deterministic lookup tables (T301).

These are standard, definitional relations of 子平命理 (fixed data, not
invented semantics):
    - 五行相生 GENERATES: X 生 GENERATES[X]
    - 五行相克 CONTROLS:  X 克 CONTROLS[X]
    - 地支藏干 BRANCH_HIDDEN_STEMS: standard 藏干 table (主气/中气/余气)
    - 季节 SEASON_BY_BRANCH: derived from 月支

十神 relation of a stem to the 日主 (same element / generates me / I generate /
controls me / I control), modulated by 阴阳同异.
"""

from __future__ import annotations

# 五行相生链
GENERATES = {
    "WOOD": "FIRE",
    "FIRE": "EARTH",
    "EARTH": "METAL",
    "METAL": "WATER",
    "WATER": "WOOD",
}

# 五行相克链
CONTROLS = {
    "WOOD": "EARTH",
    "EARTH": "WATER",
    "WATER": "FIRE",
    "FIRE": "METAL",
    "METAL": "WOOD",
}

# 地支藏干 (主气 first). Standard table.
BRANCH_HIDDEN_STEMS = {
    "ZI": [("GUI", "main")],
    "CHOU": [("JI", "main"), ("GUI", "middle"), ("XIN", "residual")],
    "YIN": [("JIA", "main"), ("BING", "middle"), ("WU", "residual")],
    "MAO": [("YI", "main")],
    "CHEN": [("WU", "main"), ("YI", "middle"), ("GUI", "residual")],
    "SI": [("BING", "main"), ("WU", "middle"), ("GENG", "residual")],
    "WU": [("DING", "main"), ("JI", "middle")],
    "WEI": [("JI", "main"), ("DING", "middle"), ("YI", "residual")],
    "SHEN": [("GENG", "main"), ("REN", "middle"), ("WU", "residual")],
    "YOU": [("XIN", "main")],
    "XU": [("WU", "main"), ("XIN", "middle"), ("DING", "residual")],
    "HAI": [("REN", "main"), ("JIA", "middle")],
}

# 季节 by 月支
SEASON_BY_BRANCH = {
    "YIN": "SPRING", "MAO": "SPRING", "CHEN": "SPRING",
    "SI": "SUMMER", "WU": "SUMMER", "WEI": "SUMMER",
    "SHEN": "AUTUMN", "YOU": "AUTUMN", "XU": "AUTUMN",
    "HAI": "WINTER", "ZI": "WINTER", "CHOU": "WINTER",
}

# 杂气月(辰戌丑未)——《论杂气如何取用》专题处理
ZAGI_BRANCHES = {"CHEN", "XU", "CHOU", "WEI"}

# Reuse bazi_facts tables to keep single source of truth.
# P0-FNDR-03 (R-09 ⑦ 十神 audit fix): 反转依赖方向
# 之前: from ..engines.bazi_engine import STEM_ELEMENT, STEM_POLARITY  # 循环依赖根因
# 现在: 从基础事实层导入, 消除 bazi_engine ↔ bazi_ten_gods 循环依赖
# 依赖图: facts → reasoning.bazi_ten_gods → engines.bazi_engine
from ..facts.bazi_facts import (  # noqa: E402
    STEM_ELEMENT,
    STEM_POLARITY,
    BRANCH_HIDDEN_STEMS,
    GENERATES,
    CONTROLS,
)


def hidden_main_stem(branch: str) -> str:
    """主气藏干 of an earthly branch (first hidden stem)."""
    return BRANCH_HIDDEN_STEMS[branch][0][0]


def hidden_stems_all(branch: str) -> list[str]:
    """所有藏干 (含本气/中气/余气), 按层级顺序返回天干列表.

    P0-FNDR-04 (R-10 ⑧ 藏干 audit fix): 提供统一的"获取所有藏干"接口.
    """
    return [stem for stem, _role in BRANCH_HIDDEN_STEMS[branch]]


def hidden_main_role(branch: str) -> str:
    """主气藏干的角色 (固定为 'main')."""
    return BRANCH_HIDDEN_STEMS[branch][0][1]


def hidden_main_stem_is_transparent(branch: str, stems: list[str]) -> bool:
    """月支主气藏干是否透于四柱天干(《论杂气如何取用》:杂气本气透干方成格).

    非杂气月(当令之支)主气天然司权,无需此判定;仅杂气月(辰戌丑未)
    需要主气透干(或会支,本实现只做透干这一确定性判据)才取格。
    """
    return hidden_main_stem(branch) in stems


def ten_god(day_master: str, other_stem: str) -> str:
    """十神 of other_stem relative to day_master (definitional relation).

    Returns one of: 比肩 劫财 食神 伤官 偏印 正印 七杀 正官 偏财 正财.
    """
    dm_el = STEM_ELEMENT[day_master]
    ot_el = STEM_ELEMENT[other_stem]
    same_polarity = (STEM_POLARITY[day_master] == STEM_POLARITY[other_stem])

    if ot_el == dm_el:
        return "比肩" if same_polarity else "劫财"
    if GENERATES.get(dm_el) == ot_el:      # 我生
        return "食神" if same_polarity else "伤官"
    if GENERATES.get(ot_el) == dm_el:      # 生我
        return "偏印" if same_polarity else "正印"
    if CONTROLS.get(ot_el) == dm_el:       # 克我
        return "七杀" if same_polarity else "正官"
    if CONTROLS.get(dm_el) == ot_el:       # 我克
        return "偏财" if same_polarity else "正财"
    raise ValueError(  # pragma: no cover — all five-element pairs are covered
        f"cannot determine 十神 for day_master={day_master} other={other_stem}"
    )


def transparent_ten_gods(
    day_master: str, year_stem: str, month_stem: str, hour_stem: str
) -> list[str]:
    """年月时三干对日主的十神列表(透干显性;日主不参与透干).

    子平以日主为「我」,透干指年月时三干(非日干)所透之十神。
    梯二「非当令十神透干显性」(ZPZ-121~130,透则显)使用此字段。

    UR-012 缓接:build_rule_context **刻意不填充**此字段,实时上下文恒 None
    -> 梯二规则不触发;仅单测显式构造 RuleContext 时求值。
    """
    out = []
    for stem in (year_stem, month_stem, hour_stem):
        if not stem:
            continue
        out.append(ten_god(day_master, stem))
    return out


def month_hidden_main_ten_god(day_master: str, month_branch: str) -> str:
    """十神 of the month branch's 主气藏干 relative to the day master.

    This is the standard 月令司权 basis (《子平真诠》: 以月令定格局).
    """
    return ten_god(day_master, hidden_main_stem(month_branch))
