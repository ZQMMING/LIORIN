# -*- coding: utf-8 -*-
"""
Decadal & Liunian Fortune — 大限/流年论断层 (Z21)

南派（倪海厦）断命重"本命 + 大限 + 流年"三盘联动：
  - 本命盘：格局定一生基调（已有）
  - 大限盘：每宫一个大限十年，主星/四化论该十年运势（本模块）
  - 流年盘：流年地支落宫，主星/四化论当年（本模块）

数据来源（全部实测，不推测）：
  - chart.palaces[宫].decadalRange/decadalStem/decadalBranch（大限基础）
  - GAN_SIHUA 天干四化表（大限四化 = decadalStem 四化）
  - 流年地支 = (year-4)%12；流年落宫 = 以命宫地支为起点顺数
  - 断言复用 NihaiAssertionResolver（倪师原话，fail-closed）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# 12 宫固定顺序（阳式：命→兄弟→夫妻→子女→财帛→疾厄→迁移→仆役→官禄→田宅→福德→父母）
# Z80-G：第 8 宫统一为「仆役」（= iztro/引擎盘面命名）。此前用书之「交友」，
# 与 chart.palaces 的「仆役」不一致 → chart.palaces.get("交友", {}) 恒空，
# 流年/流月应期该宫的主星被静默丢弃（与 Z80-F 修的 combinations.py 同类）。
PALACE_ORDER = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
]

BRANCH_IDX = {
    "子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4, "巳": 5,
    "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11,
}
IDX_BRANCH = list(BRANCH_IDX.keys())

# 月建地支（历法通识：北斗指寅为正月）
MONTH_BRANCH = {1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
                7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"}

# 五虎遁：年干 → 正月天干（甲己丙作首，乙庚戊为头，丙辛庚起，丁壬壬位，戊癸甲）
WUXING_HUDUN = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}
_MONTH_STEM_SEQ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]


def _year_stem(year: int) -> str:
    """阳历年份 → 天干（与引擎一致）"""
    return {0: "庚", 1: "辛", 2: "壬", 3: "癸", 4: "甲",
            5: "乙", 6: "丙", 7: "丁", 8: "戊", 9: "己"}[year % 10]


def _sihua_of_stem(stem: str) -> List[str]:
    """天干 → 四化四星 [禄,权,科,忌]"""
    from ...ziwei_engine import GAN_SIHUA
    return list(GAN_SIHUA.get(stem, ()))


def _assertions_for_palace(chart, palace_name: str) -> List[Dict[str, Any]]:
    """指定宫位的倪师断言（主星键 + 宫位总论键，不受 resolve 上限截断）"""
    from .nihai_assertions import get_assertions
    try:
        result = []
        # 1. 宫位总论断言 (宫名, 宫名) 键 + (宫名去宫, 宫名) 主题键
        pkey = palace_name if palace_name.endswith("宫") else palace_name + "宫"
        for a in get_assertions(pkey, pkey):
            result.append({"star": a.star, "text": a.text, "category": a.category})
        pkey2 = palace_name.rstrip("宫")
        for a in get_assertions(pkey2, pkey):
            result.append({"star": a.star, "text": a.text, "category": a.category})
        # 2. 主星×宫位断言（断言库 palace 键带"宫"后缀）
        for star in chart.palaces.get(palace_name, {}).get("major", []):
            for a in get_assertions(star, pkey):
                result.append({"star": a.star, "text": a.text, "category": a.category})
        return result
    except Exception:
        return []


def build_decadal_fortune(chart) -> List[Dict[str, Any]]:
    """12 宫大限论断.

    Returns:
        list[dict]: 每宫一个大限十年
            {age_range, palace, stem, branch, sihua(list4),
             major_stars, sihua_palaces(dict: 四化星→落宫), assertions}
    """
    from ...ziwei_engine import GAN_SIHUA

    # 星→落宫（用于大限四化落宫）
    star_to_palace: Dict[str, str] = {}
    for name, pd in chart.palaces.items():
        for s in pd.get("major", []):
            star_to_palace.setdefault(s, name)

    result: List[Dict[str, Any]] = []
    for name, pd in chart.palaces.items():
        dr = pd.get("decadalRange") or []
        sihua_stars = _sihua_of_stem(pd.get("decadalStem") or "")
        sihua_palaces = {}
        for star in sihua_stars:
            sihua_palaces[star] = star_to_palace.get(star, "")

        result.append({
            "age_range": list(dr) if dr else [],
            "palace": name,
            "stem": pd.get("decadalStem", ""),
            "branch": pd.get("decadalBranch", ""),
            "sihua": sihua_stars,                     # 大限四化四星
            "sihua_palaces": sihua_palaces,           # 大限四化落宫
            "major_stars": list(pd.get("major", [])), # 大限宫位主星
            "assertions": _assertions_for_palace(chart, name),
        })
    return result


def build_liunian_fortune(chart, year: int) -> Dict[str, Any]:
    """指定年份流年论断.

    Args:
        chart: FrozenZiweiChart
        year: 阳历年（如 2026）

    Returns:
        dict: {year, branch, stem, palace, sihua, sihua_palaces,
               major_stars, assertions}
    """
    from ...ziwei_engine import GAN_SIHUA

    # 流年地支 + 流年天干
    branch = IDX_BRANCH[(year - 4) % 12]
    stem = _year_stem(year)

    # 流年落宫：以命宫地支为起点顺数
    ming_branch = chart.palaces["命宫"]["branch"]
    offset = (BRANCH_IDX[branch] - BRANCH_IDX[ming_branch]) % 12
    palace_name = PALACE_ORDER[offset]

    # 流年四化（按流年天干）→ 落宫
    sihua_stars = _sihua_of_stem(stem)
    star_to_palace: Dict[str, str] = {}
    for name, pd in chart.palaces.items():
        for s in pd.get("major", []):
            star_to_palace.setdefault(s, name)
    sihua_palaces = {s: star_to_palace.get(s, "") for s in sihua_stars}

    palace_data = chart.palaces.get(palace_name, {})
    return {
        "year": year,
        "branch": branch,
        "stem": stem,
        "palace": palace_name,
        "sihua": sihua_stars,
        "sihua_palaces": sihua_palaces,
        "major_stars": list(palace_data.get("major", [])),
        "assertions": _assertions_for_palace(chart, palace_name),
    }


def build_liuyue_fortune(chart, year: int, month: int) -> Dict[str, Any]:
    """指定年月流月论断.

    流月口径（历法 + 五虎遁，与引擎 flow_month_mutagen 一致）：
      - 流月地支 = 月建（寅正月…丑腊月）
      - 流月天干 = 年上起月（五虎遁）：正月干 = WUXING_HUDUN[年干]，逐月顺行
      - 流月四化 = 月干 GAN_SIHUA
      - 流月落宫 = 以命宫地支为起点顺数到流月地支

    Args:
        chart: FrozenZiweiChart
        year: 阳历年
        month: 阳历月（1-12）

    Returns:
        dict: {year, month, branch, stem, palace, sihua, sihua_palaces,
               major_stars, assertions}
    """
    if month not in MONTH_BRANCH:
        return {}

    branch = MONTH_BRANCH[month]
    year_stem = _year_stem(year)
    first_month_stem = WUXING_HUDUN.get(year_stem, "丙")
    stem = _MONTH_STEM_SEQ[
        (_MONTH_STEM_SEQ.index(first_month_stem) + month - 1) % 10
    ]

    # 落宫：以命宫地支为起点顺数
    ming_branch = chart.palaces["命宫"]["branch"]
    offset = (BRANCH_IDX[branch] - BRANCH_IDX[ming_branch]) % 12
    palace_name = PALACE_ORDER[offset]

    sihua_stars = _sihua_of_stem(stem)
    star_to_palace: Dict[str, str] = {}
    for name, pd in chart.palaces.items():
        for s in pd.get("major", []):
            star_to_palace.setdefault(s, name)
    sihua_palaces = {s: star_to_palace.get(s, "") for s in sihua_stars}

    palace_data = chart.palaces.get(palace_name, {})
    return {
        "year": year,
        "month": month,
        "branch": branch,
        "stem": stem,
        "palace": palace_name,
        "sihua": sihua_stars,
        "sihua_palaces": sihua_palaces,
        "major_stars": list(palace_data.get("major", [])),
        "assertions": _assertions_for_palace(chart, palace_name),
    }

def build_liuri_fortune(
    chart, year: int, month: int, day: int, gender: str = "male",
) -> Dict[str, Any]:
    """指定日期流日论断.

    流日口径（消费八字排盘引擎日柱，只读调用不改引擎）：
      - 日干支 = BaziEngine.compute((year,month,day,12), gender) 日柱
      - 流日落宫 = 以命宫地支为起点顺数到日支
      - 流日四化 = 日干 GAN_SIHUA

    Args:
        chart: FrozenZiweiChart
        year/month/day: 阳历日期
        gender: 性别（影响八字引擎取数，默认 male）

    Returns:
        dict: {year, month, day, stem, branch, palace, sihua,
               sihua_palaces, major_stars, assertions}
    """
    # 消费八字排盘引擎（只读调用公开 API，不改八字引擎代码/提交）
    try:
        from ...bazi_engine import BaziEngine
        bz = BaziEngine().compute((year, month, day, 12), gender)
        day_ganzhi = bz.get_pillars_chinese()["day"]  # 如 "戊子"
        stem, branch = day_ganzhi[0], day_ganzhi[1]
    except Exception:
        return {}  # fail-closed: 八字引擎不可用时流日不输出

    # 落宫：以命宫地支为起点顺数
    ming_branch = chart.palaces["命宫"]["branch"]
    offset = (BRANCH_IDX.get(branch, 0) - BRANCH_IDX[ming_branch]) % 12
    palace_name = PALACE_ORDER[offset]

    sihua_stars = _sihua_of_stem(stem)
    star_to_palace: Dict[str, str] = {}
    for name, pd in chart.palaces.items():
        for s in pd.get("major", []):
            star_to_palace.setdefault(s, name)
    sihua_palaces = {s: star_to_palace.get(s, "") for s in sihua_stars}

    palace_data = chart.palaces.get(palace_name, {})
    return {
        "year": year,
        "month": month,
        "day": day,
        "stem": stem,
        "branch": branch,
        "palace": palace_name,
        "sihua": sihua_stars,
        "sihua_palaces": sihua_palaces,
        "major_stars": list(palace_data.get("major", [])),
        "assertions": _assertions_for_palace(chart, palace_name),
    }
