# -*- coding: utf-8 -*-
"""
Qintian Feature Resolver — 钦天门特征查询（Z44 蔡明宏主源版）

严格工程边界：
- 只产生事实，不解释。
- 不得修改 FrozenZiweiChart 字段。
- 不得修改公共事实层（FlyingTransformFact）。
- 所有查询都是只读 + 纯函数。
- 失败/缺失时返回 None 或空集合（fail-closed）。

钦天门事实层 = 复用飞星派 Z13-B FlyingTransformFact（钦天四化与飞星共用四化基础）
Z44：清除许铨仁体系逻辑（立太极/子丑例外/六亲亏欠），主源=蔡明宏《悟我十八年》。
"""

from __future__ import annotations

from typing import List, Optional

from ..feixing_rule_graph import FlyingTransformFact, PalaceStemFact


def get_laiyin_palace(birth_year: int, palace_stems: List[PalaceStemFact]) -> Optional[str]:
    """来因宫 = 生年干所在宫位

    蔡明宏原文：太极若引用在斗数上，所指的就是来因宫。（即宫位与出生的天干相同的宫位）。
    每个人于命盘都有来因宫（无子/丑例外）。

    Args:
        birth_year: 阳历出生年
        palace_stems: 12 宫宫干事实列表

    Returns:
        来因宫名 (e.g. "命宫", "官禄宫") 或 None
    """
    if not palace_stems:
        return None

    # 生年干公式 (与 P0-3 一致)
    birth_stem_idx = (birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]

    # 找到宫干 = birth_stem 的宫位（人人都有来因宫，无例外）
    for pf in palace_stems:
        if pf.stem == birth_stem:
            return pf.palace_name

    return None


def get_self_mutagen(chart) -> List[FlyingTransformFact]:
    """自化 = 本宫宫干四化出的星恰在本宫星曜中（钦天原著定义）

    蔡明宏原文：自化，是指一件事物现象本俱该有的平衡原理……一切自化的原理都是时间性的。

    某宫宫干使某星化X，若该星正在此宫，则此星"自化X"（时间维度的"用"）。

    Returns:
        自化事实列表 (direction="self" 的 FlyingTransformFact 构造体)
    """
    from ....ziwei_engine import GAN_SIHUA

    result: List[FlyingTransformFact] = []
    for pf in chart.palace_stems:
        if not pf.stem:
            continue
        sihua = GAN_SIHUA.get(pf.stem, ())
        if len(sihua) < 4:
            continue
        for key, star in (("化禄", sihua[0]), ("化权", sihua[1]),
                          ("化科", sihua[2]), ("化忌", sihua[3])):
            if star in pf.major_stars:
                result.append(FlyingTransformFact(
                    source_palace=pf.palace_name,
                    source_stem=pf.stem,
                    transformation=key,
                    target_star=star,
                    target_palace=pf.palace_name,
                    direction="self",
                ))
    return result


def get_xiangxin_mutagen(chart) -> List[FlyingTransformFact]:
    """向心自化 = 箭头向内（本宫发射到对宫）

    蔡明宏原文：箭头向内（向心力）→物质的凝聚。

    Returns:
        所有目标在正对宫的自化事实
    """
    OPPOSITE_PAIRS = {
        "命": "迁移", "迁移": "命",
        "兄弟": "仆役", "仆役": "兄弟",
        "夫妻": "官禄", "官禄": "夫妻",
        "子女": "田宅", "田宅": "子女",
        "财帛": "福德", "福德": "财帛",
        "疾厄": "父母", "父母": "疾厄",
    }

    result = []
    for ft in chart.flying_transforms:
        target_norm = (ft.target_palace or "").rstrip("宫")
        source_norm = (ft.source_palace or "").rstrip("宫")
        if OPPOSITE_PAIRS.get(source_norm) == target_norm:
            result.append(ft)
    return result


def get_lixin_mutagen(chart) -> List[FlyingTransformFact]:
    """离心自化 = 箭头向外（本宫星曜被本宫宫干自化，非对宫）

    蔡明宏原文：箭头向外（离心力）→物质的分散。把已有的事物现象变成没有 或改变另一种模式。

    Returns:
        离心自化事实列表（自化中目标非对宫者）
    """
    self_mutagens = get_self_mutagen(chart)
    # Z80-F（2026-10-14）：此前用 id(ft) 做集合差，但 get_self_mutagen 与
    # get_xiangxin_mutagen 各自新建 FlyingTransformFact 对象，两者 id 恒不
    # 相等 → 过滤永不生效，本函数实际恒等于 get_self_mutagen，与「排除向心」
    # 的语义矛盾。改为按飞化四要素（值）比对。
    xiangxin_keys = {
        (ft.source_palace, ft.source_stem, ft.transformation,
         ft.target_star, ft.target_palace)
        for ft in get_xiangxin_mutagen(chart)
    }
    return [
        ft for ft in self_mutagens
        if (ft.source_palace, ft.source_stem, ft.transformation,
            ft.target_star, ft.target_palace) not in xiangxin_keys
    ]
