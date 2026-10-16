"""河洛天数地数计算模块（Module 2）

负责：天干取数 → 地支取数 → 天数 → 地数 → 归一化

冻结规则依据：Architecture Freeze V1.0 §2.3 模块2
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ========== 基础映射表（冻结） ==========

# C-01/C-02 天干取数定局（河图/豹书同一映射）
STEM_VALUES: dict[str, int] = {
    "甲": 6, "乙": 2, "丙": 8, "丁": 7, "戊": 1,
    "己": 9, "庚": 3, "辛": 4, "壬": 6, "癸": 2,
}

# C-03 地支取数定局（每支一奇一偶两数）
BRANCH_VALUES: dict[str, tuple[int, int]] = {
    "子": (1, 6), "丑": (5, 10),
    "寅": (3, 8), "卯": (3, 8),
    "巳": (2, 7), "午": (2, 7),
    "未": (5, 10), "申": (4, 9), "酉": (4, 9),
    "辰": (5, 10), "戌": (5, 10),
    "亥": (1, 6),
}

# C-05 洛书数→八卦
LUSHU_TO_TRIGRAM_NAME: dict[int, str] = {
    1: "坎", 2: "坤", 3: "震", 4: "巽",
    5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离",
}

# 八卦名→三爻二进制（自下而上：初、二、三爻）
# 格式：'1'=阳爻, '0'=阴爻
TRIGRAM_BINARY: dict[str, str] = {
    "乾": "111", "兑": "110", "离": "101", "震": "100",
    "巽": "011", "坎": "010", "艮": "001", "坤": "000",
}

# 八卦名→三爻数值（自下而上：初、二、三爻）
# 格式：1=阳爻, -1=阴爻（与原典参考实现一致）
TRIGRAM_LINES: dict[str, tuple[int, int, int]] = {
    "乾": (1, 1, 1), "兑": (1, 1, -1), "离": (1, -1, 1), "震": (1, -1, -1),
    "巽": (-1, 1, 1), "坎": (-1, 1, -1), "艮": (-1, -1, 1), "坤": (-1, -1, -1),
}

# 八卦名→五行元素
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦名→阴阳性质（冻结依据：经典四正亲子定属——
# 阳卦四：乾(父)、震(长男)、坎(中男)、艮(少男)；
# 阴卦四：坤(母)、巽(长女)、离(中女)、兑(少女)。
# 修正记录 2026-08-27：原表误标巽=阳、坎=阴，与本据相悖。）
TRIGRAM_NATURE: dict[str, Literal["阳", "阴"]] = {
    "乾": "阳", "震": "阳", "坎": "阳", "艮": "阳",
    "坤": "阴", "巽": "阴", "离": "阴", "兑": "阴",
}

# 六十四卦表（上卦, 下卦）→ 卦名
SIXTY_FOUR_HEXAGRAMS: dict[tuple[str, str], str] = {
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


# ========== 归一化函数（冻结规则） ==========

def normalize_tian_shu(tian_shu: int) -> int:
    """
    天数归一化（冻结规则 HL-04）：
    - 天数>25: 天数-25=余数
    - 天数≤25: 天数÷10取余数
    - 遇十不用：余数0取商的个位
    - 特殊：天数25→5（中宫）
    """
    if tian_shu > 25:
        r = tian_shu - 25
    else:
        r = tian_shu
    shang = r // 10
    yu = r % 10
    if yu != 0:
        return yu
    if shang != 0:
        return shang
    return 5  # 天数=25的特殊情况：除还天地正数后余0，商亦为0，原典"天数正数25"归中宫（5）


def normalize_di_shu(di_shu: int) -> int:
    """
    地数归一化（冻结规则 HL-04）：
    - 地数>30: 地数-30=余数
    - 地数≤30: 地数÷10取余数
    - 遇十不用：余数0取商的个位
    - 特殊：地数30→3
    """
    if di_shu > 30:
        r = di_shu - 30
    else:
        r = di_shu
    shang = r // 10
    yu = r % 10
    if yu != 0:
        return yu
    if shang != 0:
        return shang
    return 3  # 地数=30的特殊情况


# ========== 核心计算类 ==========

@dataclass(frozen=True)
class TianDiShu:
    """天数地数计算结果"""
    tian_shu: int
    di_shu: int
    tian_reduced: int
    di_reduced: int
    details: list[str] = field(default_factory=list)


def compute_tian_di_shu(bazi: list[tuple[str, str]], gender: str) -> TianDiShu:
    """
    计算天数地数（C-01 ~ C-04，冻结于 Canonical V2.0）

    算法：
    1. 取天干数（C-01/C-02）
    2. 取地支奇偶数（C-03）
    3. 分天数（阳干 + 阳支奇数）和地数（阴干 + 阴支偶数）
    4. 归一化
    """
    if len(bazi) != 4:
        raise ValueError(f"八字必须为四柱，得到 {len(bazi)} 柱")

    details = []
    tian_sum = 0
    di_sum = 0

    for g, z in bazi:
        gan_val = STEM_VALUES.get(g)
        if gan_val is None:
            raise ValueError(f"未知天干: {g}")

        zhi_vals = BRANCH_VALUES.get(z)
        if zhi_vals is None:
            raise ValueError(f"未知地支: {z}")

        # 原典算法：所有奇数归天数，所有偶数归地数（无论天干阴阳）
        all_vals = [gan_val] + list(zhi_vals)
        odd_vals = [v for v in all_vals if v % 2 == 1]
        even_vals = [v for v in all_vals if v % 2 == 0]

        tian_sum += sum(odd_vals)
        di_sum += sum(even_vals)
        details.append(f"{g}{z}: 天干{gan_val}, 地支{zhi_vals} → 奇数{odd_vals}, 偶数{even_vals}")

    tian_reduced = normalize_tian_shu(tian_sum)
    di_reduced = normalize_di_shu(di_sum)

    return TianDiShu(
        tian_shu=tian_sum,
        di_shu=di_sum,
        tian_reduced=tian_reduced,
        di_reduced=di_reduced,
        details=details,
    )


def number_to_trigram(n: int) -> str:
    """数字 → 八卦名（洛书数映射）"""
    return LUSHU_TO_TRIGRAM_NAME.get(n, "?")


def get_hexagram_name(upper: str, lower: str) -> str:
    """获取六十四卦名"""
    return SIXTY_FOUR_HEXAGRAMS.get((upper, lower), f"{upper}{lower}")


def build_six_lines(upper_name: str, lower_name: str) -> list[int]:
    """
    构建六爻数组（自下而上：初、二、三、四、五、上）

    格式：1=阳爻, -1=阴爻（与原典参考实现一致）
    顺序：[下卦三爻, 上卦三爻] = [初, 二, 三, 四, 五, 上]
    """
    lower_lines = list(TRIGRAM_LINES[lower_name])
    upper_lines = list(TRIGRAM_LINES[upper_name])
    return lower_lines + upper_lines


# 向后兼容：旧 API 别名
resolve_yuantang = None
