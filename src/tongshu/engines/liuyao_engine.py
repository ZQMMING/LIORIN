# -*- coding: utf-8 -*-
"""六爻(Liu Yao)起卦引擎 — 轻量级实现.

源自 chinese-fortune 项目(MIT许可证), 核心功能:
- 铜钱起卦(三枚铜钱, 六次)
- 本卦/变卦/互卦
- 动爻识别
- 基础八宫归宫

完整功能(世应/六亲/六神/纳甲)待后续扩展.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# 八卦二进制(从上到下, 1=阳, 0=阴)
BAGUA_BINARY = {
    "乾": "111", "兑": "110", "离": "101", "震": "100",
    "巽": "011", "坎": "010", "艮": "001", "坤": "000",
}
BINARY_TO_BAGUA = {v: k for k, v in BAGUA_BINARY.items()}

# 六十四卦序(文王卦序) — 简化版, 完整映射待补充
HEXAGRAM_ORDER = {
    "乾为天": 1, "坤为地": 2, "水雷屯": 3, "山水蒙": 4,
    "水天需": 5, "天水讼": 6, "地水师": 7, "水地比": 8,
    "风天小畜": 9, "天泽履": 10, "地天泰": 11, "天地否": 12,
    "天火同人": 13, "火天大有": 14, "地山谦": 15, "雷地豫": 16,
    "泽雷随": 17, "山风蛊": 18, "地泽临": 19, "风地观": 20,
    "火雷噬嗑": 21, "山火贲": 22, "山地剥": 23, "地雷复": 24,
    "天雷无妄": 25, "山天大畜": 26, "山雷颐": 27, "泽风大过": 28,
    "坎为水": 29, "离为火": 30, "泽山咸": 31, "雷风恒": 32,
    "天山遁": 33, "雷天大壮": 34, "火地晋": 35, "地火明夷": 36,
    "风火家人": 37, "火泽睽": 38, "水山蹇": 39, "雷水解": 40,
    "山泽损": 41, "风雷益": 42, "泽天夬": 43, "天风姤": 44,
    "泽地萃": 45, "地风升": 46, "泽水困": 47, "水风井": 48,
    "泽火革": 49, "火风鼎": 50, "震为雷": 51, "艮为山": 52,
    "风山渐": 53, "雷泽归妹": 54, "雷火丰": 55, "火山旅": 56,
    "巽为风": 57, "兑为泽": 58, "风水涣": 59, "水泽节": 60,
    "风泽中孚": 61, "雷山小过": 62, "水火既济": 63, "火水未济": 64,
}


@dataclass
class LiuYaoResult:
    """六爻起卦结果."""
    lines: list[int] = field(default_factory=list)  # 6爻值(6/7/8/9), 从下到上
    ben_gua: str = ""           # 本卦名
    bian_gua: str = ""         # 变卦名
    hu_gua: str = ""           # 互卦名
    dong_yao: list[int] = field(default_factory=list)  # 动爻位置(1-6)
    upper_trigram: str = ""    # 上卦
    lower_trigram: str = ""    # 下卦
    question: str = ""          # 所问之事
    cast_time: str = ""         # 起卦时间


def cast_coins(seed: Optional[int] = None) -> list[int]:
    """三枚铜钱起卦, 六次.

    每枚铜钱: 正面=3(字), 反面=2(背).
    三枚总和: 6=老阴(动), 7=少阳, 8=少阴, 9=老阳(动).

    返回6爻值列表(从下到上).
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    lines = []
    for _ in range(6):
        total = sum(rng.choice([2, 3]) for _ in range(3))
        lines.append(total)
    return lines


def lines_to_trigrams(lines: list[int]) -> tuple[str, str]:
    """6爻→上下卦.

    下卦=1-3爻, 上卦=4-6爻.
    阳爻(7/9)=1, 阴爻(6/8)=0.
    """
    lower_bin = "".join("1" if lines[i] in (7, 9) else "0" for i in range(3))
    upper_bin = "".join("1" if lines[i] in (7, 9) else "0" for i in range(3, 6))
    lower = BINARY_TO_BAGUA.get(lower_bin, "?")
    upper = BINARY_TO_BAGUA.get(upper_bin, "?")
    return upper, lower


def trigrams_to_gua_name(upper: str, lower: str) -> str:
    """上下卦→六十四卦名（取京房纳甲表，非纯卦亦正确）。"""
    from .liuyao_najia import HEXAGRAM_NAME

    name = HEXAGRAM_NAME.get((upper, lower))
    if name is None:  # pragma: no cover - 上下卦必为八卦之一
        raise ValueError(f"未知上下卦组合：上{upper}下{lower}")
    return name


def get_dong_yao(lines: list[int]) -> list[int]:
    """获取动爻位置(1-6, 从下到上).

    6=老阴(动), 9=老阳(动).
    """
    return [i + 1 for i, v in enumerate(lines) if v in (6, 9)]


def get_bian_gua(lines: list[int], dong_yao: list[int]) -> str:
    """获取变卦(动爻阴阳互变)."""
    if not dong_yao:
        return trigrams_to_gua_name(*lines_to_trigrams(lines))
    changed = lines.copy()
    for pos in dong_yao:
        idx = pos - 1
        changed[idx] = 7 if changed[idx] in (6, 8) else 8  # 阴↔阳
    return trigrams_to_gua_name(*lines_to_trigrams(changed))


def get_hu_gua(lines: list[int]) -> str:
    """获取互卦(2-4爻为下卦, 3-5爻为上卦)."""
    hu_lines = [lines[1], lines[2], lines[3], lines[2], lines[3], lines[4]]
    return trigrams_to_gua_name(*lines_to_trigrams(hu_lines))


def cast(question: str = "", seed: Optional[int] = None,
         cast_time: str = "") -> LiuYaoResult:
    """六爻起卦主入口.

    Args:
        question: 所问之事
        seed: 随机种子(可复现)
        cast_time: 起卦时间

    Returns:
        LiuYaoResult 起卦结果
    """
    lines = cast_coins(seed)
    upper, lower = lines_to_trigrams(lines)
    dong_yao = get_dong_yao(lines)
    ben_gua = trigrams_to_gua_name(upper, lower)
    bian_gua = get_bian_gua(lines, dong_yao)
    hu_gua = get_hu_gua(lines)

    return LiuYaoResult(
        lines=lines,
        ben_gua=ben_gua,
        bian_gua=bian_gua,
        hu_gua=hu_gua,
        dong_yao=dong_yao,
        upper_trigram=upper,
        lower_trigram=lower,
        question=question,
        cast_time=cast_time,
    )


def line_visual(lines: list[int]) -> str:
    """爻象可视化(从下到上).

    阳爻(7/9)=━━━, 阴爻(6/8)=━ ━, 动爻加*标记.
    """
    visual = []
    for i, v in enumerate(reversed(lines)):  # 从上到下显示
        pos = 6 - i
        if v in (7, 9):
            line = "━━━"
        else:
            line = "━ ━"
        if v in (6, 9):
            line += " *"  # 动爻
        visual.append(f"{pos}: {line}")
    return "\n".join(visual)


# ---------------------------------------------------------------------------
# 纳甲装卦（京房法）——起卦 + 装卦一体入口
# ---------------------------------------------------------------------------

@dataclass
class LiuYaoCast:
    """一次完整起卦：起卦结果 + 纳甲装卦盘。"""
    result: "LiuYaoResult"
    chart: "object"  # liuyao_najia.LiuYaoChart

    def to_dict(self) -> dict:
        return {"result": {
            "lines": list(self.result.lines),
            "ben_gua": self.result.ben_gua,
            "bian_gua": self.result.bian_gua,
            "hu_gua": self.result.hu_gua,
            "dong_yao": list(self.result.dong_yao),
            "upper_trigram": self.result.upper_trigram,
            "lower_trigram": self.result.lower_trigram,
            "question": self.result.question,
            "cast_time": self.result.cast_time,
        }, "chart": self.chart.to_dict()}


def cast_from_lines(
    lines: list[int],
    *,
    question: str = "",
    cast_time: str = "",
    day_stem: str = "甲",
    day_branch: str = "子",
    month_branch: str = "",
) -> LiuYaoCast:
    """由六爻值（6/7/8/9，自下而上）直接起卦并纳甲装卦。"""
    from .liuyao_najia import build_liuyao_chart

    upper, lower = lines_to_trigrams(lines)
    dong_yao = get_dong_yao(lines)
    ben_gua = trigrams_to_gua_name(upper, lower)
    result = LiuYaoResult(
        lines=list(lines),
        ben_gua=ben_gua,
        bian_gua=get_bian_gua(lines, dong_yao),
        hu_gua=get_hu_gua(lines),
        dong_yao=dong_yao,
        upper_trigram=upper,
        lower_trigram=lower,
        question=question,
        cast_time=cast_time,
    )
    chart = build_liuyao_chart(day_stem, day_branch, month_branch, dong_yao, ben_gua)
    return LiuYaoCast(result=result, chart=chart)


def cast_full(
    question: str = "",
    seed: Optional[int] = None,
    cast_time: str = "",
    *,
    day_stem: str = "甲",
    day_branch: str = "子",
    month_branch: str = "",
) -> LiuYaoCast:
    """铜钱起卦 + 京房纳甲装卦（六亲/世应/六神/伏神/旬空/变爻）。"""
    return cast_from_lines(
        cast_coins(seed),
        question=question,
        cast_time=cast_time,
        day_stem=day_stem,
        day_branch=day_branch,
        month_branch=month_branch,
    )
