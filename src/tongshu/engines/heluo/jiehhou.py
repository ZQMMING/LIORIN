"""H11: 节候卦 / 卦气计算模块

职责：
  1. 节候卦：将二十四节气映射到对应的六十四卦
  2. 卦气：六十卦配周天三百六十五度（京房卦气说）

原典依据：
  - 《河洛真数》起例卷下·定节候卦说
  - 《易冒》引河洛理数（总集:210-211）
  - 《易楔·卷四》杭辛斋
  - 《周易图》（识典古籍）

卦气歌（起例卷下）：
  关关初起立春前，小过蒙兮渐泰发。
  二刚阑蜚及春雷，需随托离大壮列。
  ...（完整24节气配卦见 evidence matrix 附录A）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# 节候卦：节气 → 起始卦（从卦气歌推导）
# ═══════════════════════════════════════════════════════════════

# 节气名称（24节气，按 sxtwl jqIndex 0-23 顺序）
SOLAR_TERMS = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]

# 节候卦：jqIndex → (起始卦名, 动爻索引0-5)
# 原典："冬至一索得中男，颐六四爻动，为地雷复卦"
# 卦气歌原文解读（中华典籍网）：
#   立春→颐六四→复，小寒→井三爻→渐，大寒→渐四爻→泰，
#   雨水→泰三爻→解，惊蛰→遁二爻→夬，春分→节初爻→大壮，
#   清明→夬二爻→损，谷雨→大壮三爻→革，立夏→鼎初爻→益，
#   小满→旅上爻→睽，芒种→明夷五爻→大畜，夏至→师五爻→否，
#   小暑→比四爻→剥，大暑→观上爻→萃，立秋→剥上爻→晋，
#   处暑→睽四爻→坎，白露→履三爻→离，秋分→家人五爻→乾，
#   寒露→丰四爻→遯(遁)，霜降→革三爻→咸，立冬→未济上爻→蒙，
#   小雪→蒙五爻→讼，大雪→蹇四爻→需
#
# 格式：(起始卦名, 动爻位置0-5, 结果卦名)
# 注意：原典节候卦描述的是"卦动"关系，此处记录节气的"主卦"

JIEHOU_GUA: dict[int, tuple[str, int, str]] = {
    # 冬季（亥子丑）
    0:  ("山雷颐",  4, "地雷复"),   # 冬至：颐六四动→复
    1:  ("水风井",  3, "风山渐"),   # 小寒
    2:  ("风山渐",  4, "地天泰"),   # 大寒
    3:  ("地天泰",  3, "雷水解"),   # 立春
    4:  ("天山遁",  2, "泽天夬"),   # 雨水
    5:  ("水泽节",  1, "雷天大壮"), # 惊蛰
    # 春季（寅卯辰）
    6:  ("泽天夬",  2, "山泽损"),   # 春分
    7:  ("雷天大壮", 3, "火泽睽"),   # 清明
    8:  ("火风鼎",  1, "风雷益"),    # 谷雨
    9:  ("火山旅",   5, "山天大畜"), # 立夏（上爻=5）
    10: ("地火明夷", 5, "水地比"),   # 小满
    11: ("地水师",   5, "天地否"),   # 芒种
    # 夏季（巳午未）
    12: ("水地比",   4, "山地剥"),   # 夏至
    13: ("风地观",   5, "泽地萃"),   # 小暑
    14: ("山地剥",   5, "火地晋"),   # 大暑
    15: ("火泽睽",   4, "坎为水"),   # 立秋
    16: ("天泽履",   3, "离为火"),   # 处暑
    17: ("风火家人", 5, "乾为天"),   # 白露
    # 秋季（申酉戌）
    18: ("雷火丰",   4, "天山遁"),   # 秋分
    19: ("泽火革",   3, "泽山咸"),   # 寒露
    20: ("火水未济", 5, "山水蒙"),   # 霜降
    21: ("山水蒙",   5, "天水讼"),   # 立冬
    22: ("水山蹇",   4, "水天需"),   # 小雪
    23: ("水天需",   4, "坎为水"),   # 大雪
}

# 节候卦简化版：jqIndex → 节候主卦名（便于快速查询）
JIEHOU_GUA_NAME: dict[int, str] = {idx: data[0] for idx, data in JIEHOU_GUA.items()}


# ═══════════════════════════════════════════════════════════════
# 卦气：六十卦配周天（京房六日七分法）
# ═══════════════════════════════════════════════════════════════

# 四正卦（坎离震兑）分管二十四节气，不入六十卦
SIZHENG_GUA = {"坎", "离", "震", "兑"}

# 辟卦（十二消息卦）分领十二月
BI_GUA = ["复", "临", "泰", "大壮", "夬", "乾",
          "姤", "观", "否", "遁", "剥", "坤"]

# 六十卦（排除四正卦）
SIXTY_GUA = [
    "中孚", "讼", "履", "节", "損", "兑", "困", "萃",
    "咸", "否", "谦", "豫", "升", "鼎", "大过", "姤",
    "大畜", "剥", "贲", "无妄", "宜", "旅", "家人", "睽",
    "涣", "小过", "明夷", "震", "归妹", "丰", "恒", "巽",
    "晋", "渐", "蛊", "蒙", "屯", "噬嗑", "贲", "损",
    "益", "困", "井", "未济", "既济", "革", "涣", "节",
]


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SeasonalHexagram:
    """节候卦结果。"""
    jq_index: int                  # 节气索引 0-23
    jq_name: str                   # 节气名称
    main_gua: str                  # 节候主卦
    moving_line: int               # 动爻索引 0-5
    result_gua: str                # 动卦结果
    evidence: list[str]            # 可审计证据链


@dataclass(frozen=True)
class QiPhase:
    """卦气阶段结果。"""
    year: int
    jq_index: int
    jq_name: str
    main_gua: str
    is_sizheng: bool               # 是否为四正卦分管
    is_bi_gua: bool                # 是否为辟卦
    six_day_seven_method: bool     # 是否适用六日七分法


# ═══════════════════════════════════════════════════════════════
# 核心计算函数
# ═══════════════════════════════════════════════════════════════

def get_seasonal_hexagram(jq_index: int) -> SeasonalHexagram:
    """
    根据节气索引获取节候卦。

    Args:
        jq_index: 节气索引（0=冬至, 1=小寒, ..., 23=大雪）

    Returns:
        SeasonalHexagram

    Raises:
        ValueError: jq_index 超出 0-23 范围
    """
    if not (0 <= jq_index <= 23):
        raise ValueError(f"jq_index must be 0-23, got {jq_index}")

    main_gua, moving_line, result_gua = JIEHOU_GUA[jq_index]
    jq_name = SOLAR_TERMS[jq_index]

    evidence = [
        f"节气: {jq_name}（索引{jq_index}）",
        f"节候主卦: {main_gua}",
        f"动爻: 第{moving_line}爻（自下而上，{'初' if moving_line==0 else '上' if moving_line==5 else ''}）",
        f"动卦: {result_gua}",
        f"原典依据: 《河洛真数》起例卷下·定节候卦说",
    ]

    return SeasonalHexagram(
        jq_index=jq_index,
        jq_name=jq_name,
        main_gua=main_gua,
        moving_line=moving_line,
        result_gua=result_gua,
        evidence=evidence,
    )


def get_qi_phase(year: int, jq_index: int) -> QiPhase:
    """
    计算卦气阶段。

    Args:
        year: 公历年份
        jq_index: 节气索引 0-23

    Returns:
        QiPhase
    """
    jq_name = SOLAR_TERMS[jq_index]
    main_gua = JIEHOU_GUA_NAME.get(jq_index, "?")

    # 判断是否为四正卦分管的节气
    # 四正卦分管：坎(冬至)、离(夏至)、震(春分)、兑(秋分)
    sizheng_map = {0: "坎", 6: "震", 12: "离", 18: "兑"}
    is_sizheng = jq_index in sizheng_map
    is_bi_gua = jq_name in ["立春", "清明", "立夏", "立秋", "立冬", "冬至",
                              "春分", "夏至", "秋分", "芒种", "小寒", "大暑"]

    return QiPhase(
        year=year,
        jq_index=jq_index,
        jq_name=jq_name,
        main_gua=main_gua,
        is_sizheng=is_sizheng,
        is_bi_gua=is_bi_gua,
        six_day_seven_method=not is_sizheng,
    )


def get_current_jieqi_info(year: int, month: int, day: int) -> Optional[SeasonalHexagram]:
    """
    根据公历日期获取当前所在节气的节候卦信息。

    返回「出生日（含当天）之前最近一个已过节气」对应的节候卦。
    若出生当天恰为节气日，则返回当天节气；否则向前回溯最近的上一个节气。

    修复说明（H11 bug）：原实现用 ``sxtwl.Day.getJieQi()`` 直接判断"所在节气"，
    但该 API 语义是「当天是否为节气日」——仅在节气日返回索引(0-23)，非节气日返回
    255，导致绝大多数出生日期（非节气当天）被误判为 None，节候卦基本失效。
    本实现改为回溯最近已过节气，保证任意出生日期均能取到正确的节候卦。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日

    Returns:
        SeasonalHexagram 或 None（sxtwl 不可用或回溯失败时）
    """
    try:
        import sxtwl
        from datetime import date, timedelta
    except ImportError:
        return None

    try:
        target = date(year, month, day)
        # 两节气间隔约 15 天，回溯 31 天必然覆盖最近的上一个节气（含跨年冬至）。
        for back in range(0, 32):
            cur = target - timedelta(days=back)
            d = sxtwl.fromSolar(cur.year, cur.month, cur.day)
            if d.hasJieQi():
                jq_idx = d.getJieQi()
                if not (0 <= jq_idx <= 23):
                    return None
                return get_seasonal_hexagram(jq_idx)
        return None
    except Exception:
        return None


__all__ = [
    "SOLAR_TERMS",
    "JIEHOU_GUA",
    "JIEHOU_GUA_NAME",
    "SIZHENG_GUA",
    "BI_GUA",
    "SeasonalHexagram",
    "QiPhase",
    "get_seasonal_hexagram",
    "get_qi_phase",
    "get_current_jieqi_info",
]
