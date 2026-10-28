# -*- coding: utf-8 -*-
"""ZIPING V3.1 确定性参考表 (纯数据, 非计算).

ARCH-003~006 合规: 本模块只含五部经典通行事实表 (五行/藏干/生克/十神定义),
是排盘层已有的确定性映射, 不是 ZiPing 对 BaziChart 的重算——
BaziChart 字段仍由 BaziEngine 产出, 本表仅用于符号表构造时的
"取值归一" (如 支→五行 归一), 不得用于重新推导任何 Bazi 事实.
"""
from __future__ import annotations

# 天干→五行
STEM_ELEMENT = {
    "JIA": "WOOD", "YI": "WOOD", "BING": "FIRE", "DING": "FIRE",
    "WU": "EARTH", "JI": "EARTH", "GENG": "METAL", "XIN": "METAL",
    "REN": "WATER", "GUI": "WATER",
}

# 地支→五行 (本气口径)
BRANCH_ELEMENT = {
    "YIN": "WOOD", "MAO": "WOOD", "CHEN": "EARTH", "SI": "FIRE",
    "WU": "FIRE", "WEI": "EARTH", "SHEN": "METAL", "YOU": "METAL",
    "XU": "EARTH", "HAI": "WATER", "ZI": "WATER", "CHOU": "EARTH",
}

# 地支藏干 (main/middle/residual), 通行口径
BRANCH_HIDDEN: dict[str, dict[str, str]] = {
    "YIN": {"main": "JIA", "middle": "BING", "residual": "WU"},
    "MAO": {"main": "YI", "middle": "", "residual": ""},
    "CHEN": {"main": "WU", "middle": "YI", "residual": "GUI"},
    "SI": {"main": "BING", "middle": "WU", "residual": "GENG"},
    "WU": {"main": "DING", "middle": "JI", "residual": ""},
    "WEI": {"main": "JI", "middle": "DING", "residual": "YI"},
    "SHEN": {"main": "GENG", "middle": "REN", "residual": "WU"},
    "YOU": {"main": "XIN", "middle": "", "residual": ""},
    "XU": {"main": "WU", "middle": "XIN", "residual": "DING"},
    "HAI": {"main": "REN", "middle": "JIA", "residual": ""},
    "ZI": {"main": "GUI", "middle": "", "residual": ""},
    "CHOU": {"main": "JI", "middle": "GUI", "residual": "XIN"},
}

# 五行相生 (A生B: key 生 value)
GENERATES = {
    "WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL",
    "METAL": "WATER", "WATER": "WOOD",
}
# 五行相克 (A克B: key 克 value)
CONTROLS = {
    "WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE",
    "FIRE": "METAL", "METAL": "WOOD",
}

# 天干顺序 (贴位判断 INORDER-004/005 用: 年月日时 干位序列)
PILLAR_ORDER = ("YEAR", "MONTH", "DAY", "HOUR")

# 墓库支
STORE_BRANCHES = {"CHEN", "XU", "CHOU", "WEI"}

# 四时归类 (月支→季)
SEASON_OF_MONTH = {
    "YIN": "SPRING", "MAO": "SPRING", "CHEN": "SPRING",
    "SI": "SUMMER", "WU": "SUMMER", "WEI": "SUMMER",
    "SHEN": "AUTUMN", "YOU": "AUTUMN", "XU": "AUTUMN",
    "HAI": "WINTER", "ZI": "WINTER", "CHOU": "WINTER",
}
