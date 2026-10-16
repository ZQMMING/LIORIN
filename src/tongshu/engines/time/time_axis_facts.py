"""time_axis_facts — 时间轴事实层 (流年/流月/流日 Fact)

ZIPING Fact API 边界 (ADR: ZIPING_FACT_API_BOUNDARY_20260911):
排盘/时间引擎只生产"时间干支事实" (可计算 Fact), 不生产吉凶断语 (Judgment)。
本模块输出纯 Fact 字典, 供择日/事件验证/岁运分析等下游引擎消费。

契约:
- 流年: {"type":"LIUNIAN","year":Y,"pillar":"丙午","pillar_pinyin":"BING-WU",
         "gan":"BING","zhi":"WU","start":"2026-02-04","end":"2027-02-03"}
         以立春(节气索引3)切换; start=立春当日, end=次年立春前一日。
- 流月: {"type":"LIUYUE","year":Y,"month_index":1(寅=1..12),
         "pillar":"庚寅","pillar_pinyin":"GENG-YIN","gan":"GENG","zhi":"YIN",
         "start":"2026-02-04","end":"2026-03-05"}
         以节气"节"切换 (寅月=立春, 卯月=惊蛰, ... 丑月=小寒)。
- 流日: {"type":"LIURI","date":"2026-05-20","pillar":"甲辰","pillar_pinyin":"JIA-CHEN",
         "gan":"JIA","zhi":"CHEN"}

全部计算基于 sxtwl (寿星天文历), 与四柱引擎同源, 确定性可复算。
"""

from __future__ import annotations

import sxtwl

from ...facts.bazi_facts import HEAVENLY_STEMS, EARTHLY_BRANCHES

# 拼音 → 中文 (展示映射; 与 bazi_engine.STEM_CN/BRANCH_CN 同源同值, 避免跨层依赖)
STEM_CN = {
    "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
    "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸",
}
BRANCH_CN = {
    "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
    "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥",
}

# 流月 month_index(寅=1..丑=12) → 月首"节"的节气索引 (sxtwl: 奇数=节)
# 寅=立春3, 卯=惊蛰5, 辰=清明7, 巳=立夏9, 午=芒种11, 未=小暑13,
# 申=立秋15, 酉=白露17, 戌=寒露19, 亥=立冬21, 子=大雪23, 丑=小寒1(次年)
_MONTH_TERM_INDEX = (3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 1)
# 各"节"所在公历月 (丑月小寒在次年 1 月)
_MONTH_CAL_MONTH = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1)


def _find_jieqi_date(year: int, cal_month: int, term_index: int):
    """在 (year, cal_month) 内查找节气索引 == term_index 的日期 (日级精度).

    节所在公历日期范围固定 (如立春 2/3-2/5), 遍历 1-31 可稳定命中。
    """
    for d in range(1, 32):
        try:
            day = sxtwl.fromSolar(year, cal_month, d)
        except Exception:
            break
        if day.getJieQi() == term_index:
            return (year, cal_month, d)
    raise ValueError(
        f"未找到节气 term_index={term_index} in {year}-{cal_month:02d}"
    )


def _gz_str(stem: str, branch: str) -> str:
    return f"{STEM_CN[stem]}{BRANCH_CN[branch]}"


def compute_liunian(year: int) -> dict:
    """流年干支事实 (立春切换).

    start = 当年立春当日, end = 次年立春前一日 (契约见模块 docstring).
    """
    from datetime import date, timedelta

    lc = _find_jieqi_date(year, 2, 3)
    lc_next = _find_jieqi_date(year + 1, 2, 3)
    day = sxtwl.fromSolar(*lc)
    gz = day.getYearGZ()
    stem = HEAVENLY_STEMS[gz.tg]
    branch = EARTHLY_BRANCHES[gz.dz]
    return {
        "type": "LIUNIAN",
        "year": year,
        "pillar": _gz_str(stem, branch),
        "pillar_pinyin": f"{stem}-{branch}",
        "gan": stem,
        "zhi": branch,
        "start": date(*lc).isoformat(),
        "end": (date(*lc_next) - timedelta(days=1)).isoformat(),
    }


def compute_liuyue(year: int, month_index: int) -> dict:
    """流月干支事实 (节气"节"切换).

    Args:
        year: 干支纪年 (以立春为年界, 如 2026 = 丙午年).
        month_index: 1=寅月 .. 12=丑月.

    月干由 sxtwl.getMonthGZ 按节气月直接给出 (与四柱月柱同源)。
    """
    if not 1 <= month_index <= 12:
        raise ValueError(f"month_index must be 1..12, got {month_index}")

    idx = month_index - 1
    start_year_off = 1 if idx == 11 else 0
    next_idx = (idx + 1) % 12
    end_year_off = 1 if next_idx in (0, 11) else 0

    start = _find_jieqi_date(year + start_year_off, _MONTH_CAL_MONTH[idx], _MONTH_TERM_INDEX[idx])
    end = _find_jieqi_date(
        year + end_year_off,
        _MONTH_CAL_MONTH[next_idx],
        _MONTH_TERM_INDEX[next_idx],
    )

    day = sxtwl.fromSolar(*start)
    gz = day.getMonthGZ()
    stem = HEAVENLY_STEMS[gz.tg]
    branch = EARTHLY_BRANCHES[gz.dz]
    return {
        "type": "LIUYUE",
        "year": year,
        "month_index": month_index,
        "pillar": _gz_str(stem, branch),
        "pillar_pinyin": f"{stem}-{branch}",
        "gan": stem,
        "zhi": branch,
        "start": f"{start[0]:04d}-{start[1]:02d}-{start[2]:02d}",
        "end": f"{end[0]:04d}-{end[1]:02d}-{end[2]:02d}",
    }


def compute_liuyue_all(year: int) -> list:
    """某干支年的 12 个流月 (寅=1 .. 丑=12)."""
    return [compute_liuyue(year, i) for i in range(1, 13)]


def compute_liuri(year: int, month: int, day: int) -> dict:
    """流日干支事实 (日级, sxtwl getDayGZ)."""
    d = sxtwl.fromSolar(year, month, day)
    gz = d.getDayGZ()
    stem = HEAVENLY_STEMS[gz.tg]
    branch = EARTHLY_BRANCHES[gz.dz]
    return {
        "type": "LIURI",
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "pillar": _gz_str(stem, branch),
        "pillar_pinyin": f"{stem}-{branch}",
        "gan": stem,
        "zhi": branch,
    }
