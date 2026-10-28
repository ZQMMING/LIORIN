"""Yi Core — 易经基础数据层（独立于 Heluo 引擎）

这是 Yi Engine 的底层数据契约，供所有上层引擎（heluo、huangli 等）导入。
核心原则：
  1. 零外部依赖：本文件不 import heluo/*
  2. 单一数据源：TRIGRAM_DATA / SIXTY_FOUR_MAP 只在此定义
  3. 向后兼容：原 yi.hexagram_symbol 的功能全部保留在此

架构：
  yi/core.py              ← 共享数据契约（本文件）
  yi/hexagram_symbol.py   ← 从 core 构建 Symbol 对象
  yi/models.py            ← 数据模型定义
  heluo/hexagram.py       ← 从 core 导入，不再 import yi
  huangli_engine.py       ← 从 core 导入
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════
# 八卦基础数据（独立定义，不依赖 heluo.numbers）
# ═══════════════════════════════════════════════════════════════

# 八卦三爻（自下而上：初、二、上）
# 格式：1=阳爻, -1=阴爻
TRIGRAM_LINES: dict[str, tuple[int, int, int]] = {
    "乾": (1, 1, 1), "兑": (1, 1, -1), "离": (1, -1, 1), "震": (1, -1, -1),
    "巽": (-1, 1, 1), "坎": (-1, 1, -1), "艮": (-1, -1, 1), "坤": (-1, -1, -1),
}

# 八卦名→五行元素（中文，与原典一致）
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦名→阴阳性质
TRIGRAM_NATURE: dict[str, str] = {
    "乾": "阳", "震": "阳", "坎": "阳", "艮": "阳",
    "坤": "阴", "巽": "阴", "离": "阴", "兑": "阴",
}

# 八卦名→先天数
TRIGRAM_XIANTIAN_NUM: dict[str, int] = {
    "乾": 1, "兑": 2, "离": 3, "震": 4,
    "巽": 5, "坎": 6, "艮": 7, "坤": 8,
}

# 八卦名→后天方位数（洛书数）
TRIGRAM_LOSHU_NUM: dict[str, int] = {
    "坎": 1, "坤": 2, "震": 3, "巽": 4,
    "乾": 6, "兑": 7, "艮": 8, "离": 9,
}

# 自然象→八卦名
NATURE_TO_TRIGRAM: dict[str, str] = {
    "天": "乾", "泽": "兑", "火": "离", "雷": "震",
    "风": "巽", "水": "坎", "山": "艮", "地": "坤",
}


# ═══════════════════════════════════════════════════════════════
# 六十四卦表（上卦, 下卦）→ 卦名
# ═══════════════════════════════════════════════════════════════

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

# 反向映射：卦名 → (上卦, 下卦)
NAME_TO_TRIGRAMS: dict[str, tuple[str, str]] = {v: k for k, v in SIXTY_FOUR_MAP.items()}


# ═══════════════════════════════════════════════════════════════
# 卦象关系计算函数
# ═══════════════════════════════════════════════════════════════

# 错卦映射（阴阳全反）
CUO_GUA_MAP: dict[str, str] = {
    "乾": "坤", "坤": "乾", "兑": "艮", "艮": "兑",
    "震": "巽", "巽": "震", "坎": "离", "离": "坎",
}

# 综卦映射（上下卦互换 = 综卦 = 倒过来看）
def _get_zong_gua(upper: str, lower: str) -> str:
    """综卦：上下卦互换。"""
    return SIXTY_FOUR_MAP.get((lower, upper), f"{lower}{upper}")


def _get_cuo_gua(upper: str, lower: str) -> str:
    """错卦：阴阳全反。"""
    cuo_upper = CUO_GUA_MAP.get(upper, upper)
    cuo_lower = CUO_GUA_MAP.get(lower, lower)
    return SIXTY_FOUR_MAP.get((cuo_upper, cuo_lower), f"{cuo_upper}{cuo_lower}")


def _get_hu_gua(upper: str, lower: str) -> str | None:
    """
    互卦：取二三四爻为上卦，三四五爻为下卦。
    简化版：返回 None（完整实现需六爻数据）。
    """
    return None


def compute_ti_yong_relation(upper: str, lower: str) -> str:
    """
    体用生克关系。

    下卦为体，上卦为用：
      用生体 → 吉
      用克体 → 凶
      体生用 → 泄
      体克用 → 耗
      比和   → 平
    """
    ti_elem = TRIGRAM_ELEMENT.get(lower, "?")
    yong_elem = TRIGRAM_ELEMENT.get(upper, "?")

    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    if ti_elem == yong_elem:
        return "比和（平）"
    elif SHENG.get(yong_elem) == ti_elem:
        return "用生体（吉）"
    elif KE.get(yong_elem) == ti_elem:
        return "用克体（凶）"
    elif SHENG.get(ti_elem) == yong_elem:
        return "体生用（泄）"
    elif KE.get(ti_elem) == yong_elem:
        return "体克用（耗）"
    return "未知"


def get_hexagram_lines(upper: str, lower: str) -> tuple[int, ...]:
    """从上下卦构建六爻（自下而上：初、二、三、四、五、上）。"""
    lower_lines = list(TRIGRAM_LINES.get(lower, (-1, -1, -1)))
    upper_lines = list(TRIGRAM_LINES.get(upper, (-1, -1, -1)))
    return tuple(lower_lines + upper_lines)


def parse_hexagram_name(name: str) -> tuple[str, str] | None:
    """从卦名解析 (上卦, 下卦)。"""
    if name in NAME_TO_TRIGRAMS:
        return NAME_TO_TRIGRAMS[name]

    # 四字卦名（乾为天 → 乾,乾）
    if len(name) == 4 and name[1:3] == "为":
        trigram = name[0]
        if trigram in TRIGRAM_LINES:
            return (trigram, trigram)

    # 三字卦名（水山蹇 → 上坎,下艮）
    if len(name) == 3:
        upper_nature = name[0]
        lower_nature = name[1]
        if upper_nature in NATURE_TO_TRIGRAM and lower_nature in NATURE_TO_TRIGRAM:
            return (NATURE_TO_TRIGRAM[upper_nature], NATURE_TO_TRIGRAM[lower_nature])

    return None


__all__ = [
    # 八卦数据
    "TRIGRAM_LINES", "TRIGRAM_ELEMENT", "TRIGRAM_NATURE",
    "TRIGRAM_XIANTIAN_NUM", "TRIGRAM_LOSHU_NUM",
    "NATURE_TO_TRIGRAM",
    # 六十四卦
    "SIXTY_FOUR_MAP", "NAME_TO_TRIGRAMS", "CUO_GUA_MAP",
    # 计算函数
    "compute_ti_yong_relation",
    "get_hexagram_lines",
    "parse_hexagram_name",
    "_get_cuo_gua", "_get_zong_gua", "_get_hu_gua",
]
