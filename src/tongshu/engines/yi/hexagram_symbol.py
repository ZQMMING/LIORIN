"""层 A：卦象层（Hexagram Symbol）

职责：从六十四卦名解析出卦的基本结构信息
约束：无 AI 介入，纯数据查询
"""

from __future__ import annotations
from .models import HexagramSymbol

# ========== 八卦基础数据 ==========

TRIGRAM_DATA = {
    "乾": {"symbol": "☰", "element": "金", "number": 1},
    "兑": {"symbol": "☱", "element": "金", "number": 2},
    "离": {"symbol": "☲", "element": "火", "number": 3},
    "震": {"symbol": "☳", "element": "木", "number": 4},
    "巽": {"symbol": "☴", "element": "木", "number": 5},
    "坎": {"symbol": "☵", "element": "水", "number": 6},
    "艮": {"symbol": "☶", "element": "土", "number": 7},
    "坤": {"symbol": "☷", "element": "土", "number": 8},
}

# 六十四卦完整映射
HEXAGRAM_FULL_DATA: dict[str, dict] = {}

# 生成六十四卦数据
for upper, u_data in TRIGRAM_DATA.items():
    for lower, l_data in TRIGRAM_DATA.items():
        # 构建卦名和卦序
        # 简化：按标准卦序编号
        pass

# 标准卦序映射（文王六十四卦序）
GUA_SEQUENCE = [
    # 上经（乾至离，30卦）
    ("乾为天", 1), ("姤", 2), ("讼", 3), ("履", 4), ("同人", 5),
    ("大有", 6), ("无妄", 7), ("大畜", 8), ("颐", 9), ("大过", 10),
    ("坎", 11), ("习坎", 12), ("屯", 13), ("蒙", 14), ("需", 15),
    ("讼", 16), ("师", 17), ("比", 18), ("小畜", 19), ("履", 20),
    # 下经（咸至未济，34卦）
    ("恒", 32), ("遁", 33), ("大壮", 34), ("晋", 35), ("明夷", 36),
    ("家人", 37), ("睽", 38), ("蹇", 39), ("解", 40), ("损", 41),
    ("益", 42), ("夬", 43), ("萃", 44), ("升", 45), ("困", 46),
    ("井", 47), ("革", 48), ("鼎", 49), ("震", 51), ("艮", 52),
    ("渐", 53), ("归妹", 54), ("丰", 55), ("旅", 56), ("巽", 57),
    ("兑", 58), ("涣", 59), ("节", 60), ("中孚", 61), ("小过", 62),
    ("既济", 63), ("未济", 64),
]

# 完整六十四卦表（上卦, 下卦）→ 卦名
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
    ('震', '震'): '震为雷', ('震', '巽'): '雷风恒', ('震', '坎'): '雷水解',
    ('震', '艮'): '雷山小过', ('震', '坤'): '雷地豫',
    ('巽', '乾'): '风天小畜', ('巽', '兑'): '风泽中孚', ('巽', '离'): '风火家人',
    ('巽', '震'): '风雷益', ('巽', '巽'): '巽为风', ('巽', '坎'): '风水涣',
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
    """从六十四卦名获取卦的完整符号结构。纯数据查询，无 AI 介入。"""
    # 反向查找上下卦
    upper = lower = "?"
    for (u, l), n in SIXTY_FOUR_MAP.items():
        if n == name or n.endswith(name[-2:] if len(name) >= 2 else name):
            upper, lower = u, l
            break
    
    # 使用内置数据
    upper_data = TRIGRAM_DATA.get(upper, {"symbol": "?", "element": "?"})
    lower_data = TRIGRAM_DATA.get(lower, {"symbol": "?", "element": "?"})
    
    # 体用关系
    ti_yong = get_ti_yong_relation(upper, lower)
    
    # 互卦、错卦、综卦
    hu = _get_hu_gua(upper, lower)
    cuo = _get_cuo_gua(upper, lower)
    zong = _get_zong_gua(upper, lower)
    
    return HexagramSymbol(
        name=name,
        hexagram_number=0,  # 简化版暂不编号
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


def get_ti_yong_relation(upper: str, lower: str) -> str:
    """体用生克关系分析。体卦（下卦）= 自己，用卦（上卦）= 外部环境。"""
    from ..yi.core import TRIGRAM_ELEMENT
    ti_elem = TRIGRAM_ELEMENT.get(lower, "?")
    yong_elem = TRIGRAM_ELEMENT.get(upper, "?")
    
    sheng = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
    ke = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}
    
    if sheng.get(ti_elem) == yong_elem:
        return "用生体（吉）"
    elif ke.get(ti_elem) == yong_elem:
        return "用克体（凶）"
    elif sheng.get(yong_elem) == ti_elem:
        return "体生用（泄）"
    elif ke.get(yong_elem) == ti_elem:
        return "体克用（耗）"
    else:
        return "比和（平）"


def _get_cuo_gua(upper: str, lower: str) -> str:
    """错卦：阴阳全反"""
    swap = {"乾": "坤", "坤": "乾", "坎": "离", "离": "坎",
            "震": "巽", "巽": "震", "艮": "兑", "兑": "艮"}
    cuo_upper = swap.get(upper, upper)
    cuo_lower = swap.get(lower, lower)
    return SIXTY_FOUR_MAP.get((cuo_upper, cuo_lower), f"{cuo_upper}{cuo_lower}")


def _get_zong_gua(upper: str, lower: str) -> str:
    """综卦：上下翻转"""
    return SIXTY_FOUR_MAP.get((lower, upper), f"{lower}{upper}")


def _get_hu_gua(upper: str, lower: str) -> str:
    """互卦：取二三四爻为上卦，三四五爻为下卦"""
    # 简化实现
    return ""
