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

#: 节气全表缓存：公历年 → ((Y, M, D, jqIndex), ...) 升序。
#: 有界 FIFO —— 出生年跨度可达数百年，无界增长会让长期服务缓慢涨内存
#: （canonical._jie_cache 是同类问题，本轮一并处理）。
_JIEQI_TIMELINE: dict[int, tuple] = {}
_JIEQI_TIMELINE_MAX = 64

#: sxtwl ``Day.getJieQi()`` 在「当日无交节」时返回的哨兵值。
#: 实测 1970-01-01~2050-12-31 共 29,585 天，落在 0..23 之外的取值**只有 255**，
#: 而 0..23 的有效日恰好 1,944 天 = 81 年 × 24 节气，无一例外。
_JQ_NO_JIEQI_SENTINEL = 255

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


def _jieqi_timeline(sxtwl, year: int) -> tuple:
    """公历年 `year` 全年 24 节气的 (Y, M, D, jqIndex) 升序表，带进程内有界缓存。

    2026-10-06：旧实现用 ``sxtwl.fromSolar(y, m, d).getJieQi()`` 取"当日节气"，
    而该方法**只在节气当天返回索引**，其余日期返回 255（sxtwl 的无效哨兵），
    于是节候卦一年只有约 24 天可取、354 天直接判 None——而本函数的 docstring
    声称"查找最近一个已过节气"，实现与自述不符。生产上 H11 节候卦几乎恒为 None。

    改用批量接口 ``getJieQiByYear`` 取全表再二分。注意其窗口是
    **[该年立春, 次年立春]**（实测 getJieQiByYear(2026) 返回
    2026-02-04 ~ 2027-02-04 共 25 项），故须合并 (year-1, year) 两年，
    合并后跨度为 (year-1)立春 ~ (year+1)立春，完整覆盖 `year` 公历年。

    日界口径：取**日期不晚于目标日**的最近一个节气。即交节当日即归入新节气，
    与旧实现在 24 个节气当天的行为完全一致（实测 1984 年 24/24 相符、0 不一致）。
    """
    cached = _JIEQI_TIMELINE.get(year)
    if cached is not None:
        return cached

    merged: dict[tuple[int, int, int, int], None] = {}
    for yy in (year - 1, year):
        for info in sxtwl.getJieQiByYear(yy):
            # JieQiInfo 形态：属性 .jd/.jqIndex；老版本为 tuple，兜底下标取法
            jd, idx = (info.jd, info.jqIndex) if hasattr(info, "jd") else (info[0], info[1])
            t = sxtwl.JD2DD(jd)
            merged[(int(t.Y), int(t.M), int(t.D), int(idx))] = None
    table = tuple(sorted(merged))

    _JIEQI_TIMELINE[year] = table
    if len(_JIEQI_TIMELINE) > _JIEQI_TIMELINE_MAX:
        for stale in list(_JIEQI_TIMELINE)[:len(_JIEQI_TIMELINE) - _JIEQI_TIMELINE_MAX]:
            _JIEQI_TIMELINE.pop(stale, None)
    return table


def get_current_jieqi_info(year: int, month: int, day: int) -> Optional[SeasonalHexagram]:
    """
    根据公历日期获取当前所在节气的节候卦信息。

    使用 sxtwl 查找最近一个已过节气。

    Args:
        year: 公历年
        month: 公历月
        day: 公历日

    Returns:
        SeasonalHexagram；None 仅两种情形：sxtwl 未安装，或目标日早于可算窗口
        （公历年 < 2，或窗口内无任何节气早于该日）。

    Raises:
        Exception: sxtwl 已安装但计算过程出错时，异常原样上抛。
            「缺依赖」与「算错了」是两种不同故障，不应一并吞成 None ——
            否则真实计算错误会被静默伪装成「该日无节气」，无从发现。
            需要降级的调用方应自行捕获（见 canonical.HeluoCanonical
            ._compute_seasonal_hexagram，其 except 属该层自身的降级策略）。
    """
    try:
        import sxtwl
    except ImportError:
        return None
    # 以下为真实计算，异常一律上抛，不在此处降级。
    d = sxtwl.fromSolar(year, month, day)
    jq_idx = d.getJieQi()
    if 0 <= jq_idx <= 23:
        # 交节当日：与旧实现逐字一致（快路径，无需查表）。
        return get_seasonal_hexagram(jq_idx)
    if jq_idx != _JQ_NO_JIEQI_SENTINEL:
        # 其它非法值（如 -1）不是"当日无交节"，维持旧契约返回 None，不上抛。
        return None

    # 当日无交节（哨兵 255）：节候卦本就该取"最近一个已过节气"，
    # 旧实现到此直接判 None，导致一年只有约 24 天可取。改查全表取最近者。
    if year < 2:
        return None
    table = _jieqi_timeline(sxtwl, year)
    key = (year, month, day)
    found = None
    for entry in table:          # 表已升序，一旦越过目标日即止
        if entry[:3] <= key:
            found = entry[3]
        else:
            break
    if found is None:
        return None
    return get_seasonal_hexagram(found)


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
