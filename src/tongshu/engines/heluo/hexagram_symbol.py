"""Hexagram Symbol — Module A: Trigram and Hexagram structural data.

Responsibility: Extract the fundamental structural information of hexagrams
from the sixty-four hexagram names. Pure data lookup, no AI involved.
"""

from __future__ import annotations
from .models import HexagramSymbol

# ========== Trigram basic data (English element labels) ==========

# BUG-02 fix: Unified to English elements (WOOD/FIRE/EARTH/METAL/WATER)
# to match the interpreter.py five-element vocabulary.
TRIGRAM_DATA = {
    "乾": {"symbol": "☰", "element": "METAL", "number": 1},
    "兑": {"symbol": "☱", "element": "METAL", "number": 2},
    "离": {"symbol": "☲", "element": "FIRE", "number": 3},
    "震": {"symbol": "☳", "element": "WOOD", "number": 4},
    "巽": {"symbol": "☴", "element": "WOOD", "number": 5},
    "坎": {"symbol": "☵", "element": "WATER", "number": 6},
    "艮": {"symbol": "☶", "element": "EARTH", "number": 7},
    "坤": {"symbol": "☷", "element": "EARTH", "number": 8},
}

# Sixty-four hexagram complete mapping
HEXAGRAM_FULL_DATA: dict[str, dict] = {}

# Generate sixty-four hexagram data
for upper, u_data in TRIGRAM_DATA.items():
    for lower, l_data in TRIGRAM_DATA.items():
        # Construct hexagram name and trigram position
        # Simplified: by sequence number
        pass

# Standard hexagram sequence mapping (cultural Chinese names, preserved)
GUA_SEQUENCE = [
    # 上经（天始，1-30）
    ("乾为天", 1), ("坤为地", 2), ("水雷屯", 3), ("山水蒙", 4), ("天水讼", 5),
    ("地水师", 6), ("水地比", 7), ("风地观", 8), ("火地晋", 9), ("地火明夷", 10),
    ("天火同人", 11), ("地天泰", 12), ("天泽履", 13), ("天地否", 14), ("地山谦", 15),
    ("雷地豫", 16), ("泽雷随", 17), ("山风蛊", 18), ("地泽临", 19), ("风地观", 20),
    ("火雷噬嗑", 21), ("山火贲", 22), ("山地剥", 23), ("地雷复", 24), ("天雷无妄", 25),
    ("山天大畜", 26), ("山雷颐", 27), ("泽风大过", 28), ("水火既济", 29), ("火水未济", 30),
    # 下经（天成，34-64）
    ("泽山咸", 31), ("雷风恒", 32), ("天山遁", 33), ("雷天大壮", 34), ("火地晋", 35),
    ("地火明夷", 36), ("风火家人", 37), ("火泽睽", 38), ("水山蹇", 39), ("雷水解", 40),
    ("山风蛊", 41), ("风雷益", 42), ("泽天夬", 43), ("风地观", 44), ("火天大有", 45),
    ("乾为天", 46), ("坤为地", 47), ("泽地萃", 48), ("水风井", 49), ("泽雷随", 50),
    ("巽为风", 51), ("兑为泽", 52), ("坎为水", 53), ("离为火", 54), ("艮为山", 55),
    ("风山渐", 56), ("雷泽归妹", 57), ("雷火丰", 58), ("火山旅", 59), ("巽为风", 60),
    ("水泽节", 61), ("风泽中孚", 62), ("水天需", 63), ("水地师", 64),
]

# Complete sixty-four hexagram table (upper, lower) → hexagram name
SIXTY_FOUR_MAP: dict[tuple[str, str], str] = {
    ('乾', '乾'): '乾为天', ('乾', '兑'): '天泽履', ('乾', '离'): '天火同人',
    ('乾', '震'): '天雷无妄', ('乾', '巽'): '天风姤', ('乾', '坎'): '天水讼',
    ('乾', '艮'): '天山遁', ('乾', '坤'): '天地否',
    ('兑', '乾'): '泽天夬', ('兑', '兑'): '兑为泽', ('兑', '离'): '泽火革',
    ('兑', '震'): '泽雷随', ('兑', '巽'): '泽风大过', ('兑', '坎'): '泽水困',
    ('兑', '艮'): '泽山咸', ('兑', '坤'): '泽地萃',
    ('离', '乾'): '火天大有', ('离', '兑'): '火泽睽', ('离', '离'): '离为火',
    ('离', '震'): '火雷噬嗑', ('离', '巽'): '火风鼎', ('离', '坎'): '火水未济',
    ('离', '艮'): '火山旅', ('离', '坤'): '火地晋',
    ('震', '乾'): '雷天大壮', ('震', '兑'): '雷泽归妹', ('震', '离'): '雷火丰',
    ('震', '震'): '震为雷', ('震', '巽'): '风雷益', ('震', '坎'): '雷水解',
    ('震', '艮'): '雷山小过', ('震', '坤'): '雷地豫',
    ('巽', '乾'): '风天小畜', ('巽', '兑'): '风泽中孚', ('巽', '离'): '风火家人',
    ('巽', '震'): '风雷益', ('巽', '巽'): '巽为风', ('巽', '坎'): '水风井',
    ('巽', '艮'): '风山渐', ('巽', '坤'): '风地观',
    ('坎', '乾'): '水天需', ('坎', '兑'): '水泽节', ('坎', '离'): '水火既济',
    ('坎', '震'): '水雷屯', ('坎', '巽'): '水风井', ('坎', '坎'): '坎为水',
    ('坎', '艮'): '水山蹇', ('坎', '坤'): '水地比',
    ('艮', '乾'): '山天大畜', ('艮', '兑'): '山泽损', ('艮', '离'): '山火贲',
    ('艮', '震'): '山雷颐', ('艮', '巽'): '山风蛊', ('艮', '坎'): '山水蒙',
    ('艮', '艮'): '艮为山', ('艮', '坤'): '山地剥',
    ('坤', '乾'): '地天泰', ('坤', '兑'): '地泽临', ('坤', '离'): '地火明夷',
    ('坤', '震'): '地雷复', ('坤', '巽'): '地风升', ('坤', '坎'): '地水师',
    ('坤', '艮'): '地山谦', ('坤', '坤'): '坤为地',
}


def get_hexagram_symbol(name: str) -> HexagramSymbol:
    """Get hexagram symbol structure from sixty-four hexagram name. Pure data lookup, no AI."""
    # Reverse lookup of upper and lower trigrams
    upper = lower = "?"
    for (u, l), n in SIXTY_FOUR_MAP.items():
        if n == name or n.endswith(name[-2:] if len(name) >= 2 else name):
            upper, lower = u, l
            break
    
    # Use built-in data
    upper_data = TRIGRAM_DATA.get(upper, {"symbol": "?", "element": "?"})
    lower_data = TRIGRAM_DATA.get(lower, {"symbol": "?", "element": "?"})
    
    # Ti-yong relationship
    ti_yong = get_ti_yong_relation(upper, lower)
    
    # Auxiliary: cuo-gua, zong-gua, hu-gua
    hu = _get_hu_gua(upper, lower)
    cuo = _get_cuo_gua(upper, lower)
    zong = _get_zong_gua(upper, lower)
    
    return HexagramSymbol(
        name=name,
        hexagram_number=0,  # Simplified version not numbering
        sequence_position=0,
        upper_trigram=upper,
        lower_trigram=lower,
        upper_symbol=upper_data["symbol"],
        lower_symbol=lower_data["symbol"],
        upper_element=upper_data["element"],
        lower_element=lower_data["element"],
        cuo_gua=cuo,
        zong_gua=zong,
        hu_gua=hu,
        ti=lower,
        yong=upper,
        ti_yong_relation=ti_yong,
    )


# BUG-02: English element names to match unified five-element vocabulary
_ELEMENT_GENERATES: dict[str, str] = {
    "WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL", "METAL": "WATER", "WATER": "WOOD",
}

_ELEMENT_OVERCOMES: dict[str, str] = {
    "WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE", "FIRE": "METAL", "METAL": "WOOD",
}


def get_ti_yong_relation(upper: str, lower: str) -> str:
    """Analyze ti-yong (体用) generating/overcoming relationship.
    
    Ti (体, lower trigram) is the subject; Yong (用, upper trigram) is the external environment.
    
    Returns English-labeled relationship strings to match interpreter.py five-element vocabulary.
    """
    from ..heluo.numbers import TRIGRAM_ELEMENT
    ti_elem = TRIGRAM_ELEMENT.get(lower, "?")
    yong_elem = TRIGRAM_ELEMENT.get(upper, "?")
    
    if _ELEMENT_GENERATES.get(ti_elem) == yong_elem:
        return "YONG_GENERATES_TI (beneficial)"
    elif _ELEMENT_OVERCOMES.get(ti_elem) == yong_elem:
        return "YONG_OVERCOMES_TI (challenging)"
    elif _ELEMENT_GENERATES.get(yong_elem) == ti_elem:
        return "TI_GENERATES_YONG (supporting)"
    elif _ELEMENT_OVERCOMES.get(yong_elem) == ti_elem:
        return "TI_OVERCOMES_YONG (draining)"
    else:
        return "BALANCED (neutral)"


def _get_cuo_gua(upper: str, lower: str) -> str:
    """Cuo-gua (错卦): opposite yin-yang for all lines."""
    swap = {
        "乾": "坤", "坤": "乾", "兑": "艮", "艮": "兑",
        "震": "巽", "巽": "震", "坎": "离", "离": "坎",
    }
    cuo_upper = swap.get(upper, upper)
    cuo_lower = swap.get(lower, lower)
    return SIXTY_FOUR_MAP.get((cuo_upper, cuo_lower), f"{cuo_upper}{cuo_lower}")


def _get_zong_gua(upper: str, lower: str) -> str:
    """Zong-gua (综卦): upper and lower trigrams swapped."""
    return SIXTY_FOUR_MAP.get((lower, upper), f"{lower}{upper}")


def _get_hu_gua(upper: str, lower: str) -> str:
    """Hu-gua (互卦): simplified implementation."""
    return ""
