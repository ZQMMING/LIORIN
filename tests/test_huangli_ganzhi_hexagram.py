# -*- coding: utf-8 -*-
"""黄历·六十甲子配卦（值日卦）全表校验。

口径：《道藏》正一部所收「六十甲子配卦口诀」——「甲子开蒙《坤》卦起…
甲寅水火《既济》局…甲申《未济》丙申《解》…癸亥配卦山地《剥》」。
原实现把 甲申 误录为「水火既济」，与 甲寅 重复，致 60 甲子只覆盖 59 卦；
2026-11-07 按口诀改正为「火水未济」。
"""
from __future__ import annotations

import pytest

from tongshu.engines.huangli_engine import (
    _GANZHI_HEXAGRAM,
    _ganzhi_daily_hexagram,
    _NAME_TO_TRIGRAMS,
)
from tongshu.engines.yi.hexagram_symbol import SIXTY_FOUR_MAP

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIAZI_60 = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]

# 口诀明文锚点（含唯一一处历史错录的更正）
ANCHORS = {
    "甲子": "坤为地",
    "甲午": "乾为天",
    "甲寅": "水火既济",
    "甲申": "火水未济",
    "癸酉": "风山渐",
    "癸卯": "雷泽归妹",
    "癸亥": "山地剥",
    "丙子": "山雷颐",  # 口诀「丙子《臣页》卦」＝「頤」拆字，即 颐
}


def test_table_covers_all_sixty_ganzhi() -> None:
    assert len(_GANZHI_HEXAGRAM) == 60
    assert set(_GANZHI_HEXAGRAM) == set(JIAZI_60), "六十甲子必须全表覆盖，无缺无重"


def test_table_has_sixty_distinct_hexagrams() -> None:
    names = list(_GANZHI_HEXAGRAM.values())
    assert len(set(names)) == 60, f"卦名重复：{sorted({n for n in names if names.count(n) > 1})}"
    assert set(names) <= set(SIXTY_FOUR_MAP.values()), "不得出现 64 卦之外的卦名"
    # 本表不配 复/姤/蒙/革（60 甲子 ↔ 60 卦一一对应）
    for missing in ("地雷复", "天风姤", "山水蒙", "泽火革"):
        assert missing not in set(names), f"{missing} 按口诀不配六十甲子"


@pytest.mark.parametrize("ganzhi,expect", ANCHORS.items())
def test_book_mouth_anchors(ganzhi: str, expect: str) -> None:
    assert _GANZHI_HEXAGRAM[ganzhi] == expect


def test_every_entry_resolves_trigrams() -> None:
    for ganzhi, name in _GANZHI_HEXAGRAM.items():
        assert name in _NAME_TO_TRIGRAMS or any(n == name for n in SIXTY_FOUR_MAP.values())
        got = _ganzhi_daily_hexagram(ganzhi)
        assert got["name"] == name
        assert got["upper"] and got["lower"], f"{ganzhi} 未解析出上下卦"


def test_unknown_ganzhi_is_empty_not_fabricated() -> None:
    got = _ganzhi_daily_hexagram("甲子甲")
    assert got["name"] == "" and got["upper"] == "" and got["lower"] == ""
