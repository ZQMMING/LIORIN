"""H11: 节候卦（主）+ 卦气说辅助常量（次）

**2026-10-07 重大校订**——本模块原先把 H11「节候卦」实现成了卦气歌体系，
与《河洛真数》原典不符，现已改回原典：

原典节候卦只有一节，即起例卷之下 **L1489–1492「节候卦爻」**：
  「气之八节，总之其卦四」（四正卦坎震离兑），
  「候有七十二，细分之，其卦六十」，
  「节卦**坎初六起冬至**，九二小寒，六三大寒，六四立春，九五雨水，上六惊蛰。
    震初九起春分……**每卦总管九十日，自下而上，每一爻各直十五日**」
该表已逐条照抄在 ``jiegua.JIE_GUA_TABLE``，并由
``tests/heluo/test_jiegua_vs_original.py`` 逐条对拍原典。

**旧实现的三个错**（取证见本文件节候卦区块注释）：
  1. 出处误植——docstring 与 evidence 都标「起例卷下·定节候卦说」，
     而原著全库检索该节名**零命中**；引的「冬至一索得中男」亦零命中。
  2. 体系错位——挂的是卦气歌（卦X爻动→变卦链），而原著 L1893/L2034 的
     「卦气属四月」「卦气在十月」说的**十二月辟卦月卦**，也不是这套。
     网络考据：卦气说里**冬至属复卦**，非「山雷颐」。
  3. 两套体系混称——``SIZHENG_GUA`` 原取坎离震兑（那是**本卷节卦四卦**），
     而京房卦气说的四正卦是**乾坤坎离**（主二分二至）。

现 ``JIEHOU_GUA`` 改为**派生自 jiegua.JIE_GUA_TABLE**，H11 报告原典节卦；
``jiegua.get_jie_gua`` 的判词链与 H11 字段从此同源，不再两套卦名打架。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
# ⚠ 2026-10-08 批次 G：本表此前在此、jiegua.JIEQI_24、yue_ling_shu_ge.JIE_QI_ORDER
#   三处各抄一份（内容相同）。二十四节气序全库必须只有一处定义——
#   三份各改各的，索引错位要到出卦时才炸。现统一引用 jiegua.JIEQI_24。
from .jiegua import JIEQI_24 as SOLAR_TERMS  # noqa: E402

# ═══════════════════════════════════════════════════════════════
# 节候卦：jqIndex → (节卦卦名, 爻位0-5, 原典爻名)  —— 单一来源 jiegua
# ═══════════════════════════════════════════════════════════════

#: 单一来源：《河洛真数》起例卷之下 L1492「节候卦爻」节卦段，
#: 逐条照抄于 jiegua.JIE_GUA_TABLE（有 test_jiegua_vs_original.py 对拍）。
#: 本模块不再另抄一份——旧版两份表各抄各的，卦名分叉无人发现。
from .jiegua import JIE_GUA_TABLE as _JIE_GUA_SRC  # noqa: E402

#: jqIndex → (节卦卦名, 爻位0-5, 原典爻名)
#:
#: **语义已变**（2026-10-07）：旧版第三元是「动出来的变卦名」，
#: 现为**原典爻名**（初六/九二/六三…）——原典节候卦只有「卦+爻」，
#: 根本没有「变卦」这一说，强造变卦名才是错的。
JIEHOU_GUA: dict[int, tuple[str, int, str]] = {
    e.jq_index: (e.trigram, e.yao_index, e.yao_name) for e in _JIE_GUA_SRC
}

# 原典 L1492 节卦段逐字（供 evidence 与守卫引用，避免二次转述走样）
JIE_GUA_QUOTE = (
    "节卦坎初六起冬至，九二小寒，六三大寒，六四立春，九五雨水，上六惊蛰。"
    "震初九起春分，六二清明，六三谷雨，九四立夏，六五小满，上六芒种。"
    "离初九起夏至，六二小暑，九二大暑，九四立秋，六五处暑，上九白露。"
    "兑初九起秋分，九二寒露，九三霜降，九四立冬，九五小雪，上六大雪。"
    "每卦总管九十日，自下而上，每一爻各直十五日。"
)

# 节候卦简化版：jqIndex → 节卦卦名（坎/震/离/兑），便于快速查询
# 注：此处取的是**节卦卦名**，不再是旧版的六十四卦名
JIEHOU_GUA_NAME: dict[int, str] = {idx: data[0] for idx, data in JIEHOU_GUA.items()}


# ═══════════════════════════════════════════════════════════════
# 卦气：六十卦配周天（京房六日七分法）
# ═══════════════════════════════════════════════════════════════

# 本卷《河洛真数》节候卦所取的**四个卦**（L1492：坎起冬至、震起春分、
# 离起夏至、兑起秋分，各管六爻十五日）。
# ⚠ **切勿与京房卦气说的「四正卦」混称**：后者是**乾坤坎离**，主二分二至
# （维基「易数与历法配合」：乾夏至、坤冬至、坎秋分、离春分，四卦跳过不入
# 六十卦）。旧版把坎离震兑挂在这个名字下，两套体系被混为一谈——已加注澄清。
# 本常量当前无生产消费方（get_qi_phase 另有一份内联 sizheng_map）。
SIZHENG_GUA = {"坎", "离", "震", "兑"}

# 辟卦（十二消息卦）分领十二月
BI_GUA = ["复", "临", "泰", "大壮", "夬", "乾",
          "姤", "观", "否", "遁", "剥", "坤"]

# 卦气说：二十四节气配六十卦（**非《河洛真数》本卷**，供查考，勿当本卷规则）
# 来源：卦气图「立春…大雪」六十卦配节（乾坤坎离四正卦跳过，以复/姤代之）。
# 旧版此表名「六十卦」而实 48 项，含 4 组重复（贲/困/涣/节各 ×2）、
# 含非卦名「宜」、含繁体「損」，且把本卷节卦四卦（震巽兑）当成京房四正卦剔除——
# 名称、条数、字形、体系四重不实。现按卦气图逐节补全，恰好 60 项、无重复。
SIXTY_GUA_BY_JIEQI: dict[int, tuple[str, ...]] = {
    0:  ("复",),                                 # 冬至
    1:  ("颐", "屯", "益"),                      # 小寒
    2:  ("震", "噬嗑", "随"),                    # 大寒
    3:  ("无妄", "明夷"),                       # 立春
    4:  ("贲", "既济", "家人"),                  # 雨水
    5:  ("丰", "革"),                            # 惊蛰
    6:  ("同人", "临"),                          # 春分
    7:  ("损", "节", "中孚"),                    # 清明
    8:  ("归妹", "睽", "兑"),                    # 谷雨
    9:  ("履", "泰"),                            # 立夏
    10: ("大畜", "需", "小畜"),                  # 小满
    11: ("大壮", "大有", "夬"),                  # 芒种
    12: ("姤",),                                 # 夏至
    13: ("大过", "鼎", "恒"),                    # 小暑
    14: ("巽", "井", "蛊"),                      # 大暑
    15: ("升", "讼"),                            # 立秋
    16: ("困", "未济", "解"),                    # 处暑
    17: ("涣", "蒙"),                            # 白露
    18: ("师", "遯"),                            # 秋分
    19: ("咸", "旅", "小过"),                    # 寒露
    20: ("渐", "蹇", "艮"),                      # 霜降
    21: ("谦", "否"),                            # 立冬
    22: ("萃", "晋", "豫"),                      # 小雪
    23: ("观", "比", "剥"),                      # 大雪
}

#: 六十卦扁平表（按节气顺序展开），恰好 60 项、无重复
SIXTY_GUA: list[str] = [g for jqs in SIXTY_GUA_BY_JIEQI.values() for g in jqs]
assert len(SIXTY_GUA) == 60, len(SIXTY_GUA)
assert len(set(SIXTY_GUA)) == 60, "SIXTY_GUA 有重复卦名"


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SeasonalHexagram:
    """节候卦结果（《河洛真数》原典节卦口径）。

    ⚠ 字段名 ``moving_line`` / ``result_gua`` 沿用旧版卦气歌口径，未改名以免
    破坏既有消费方（canonical._compute_seasonal_hexagram、evidence_producer）。
    **语义已随 2026-10-07 校订改变**：原典节候卦是「某卦某爻直十五日」，
    既无「动爻」也无「变卦」，故 result_gua 现存原典爻名。
    """
    jq_index: int                  # 节气索引 0-23
    jq_name: str                   # 节气名称
    main_gua: str                  # 节卦卦名（原典四正卦：坎/震/离/兑）
    moving_line: int               # 节卦爻位 0-5（自下而上）
    result_gua: str                # 原典爻名（初六/九二/六三…）
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

    main_gua, moving_line, yao_name = JIEHOU_GUA[jq_index]
    jq_name = SOLAR_TERMS[jq_index]
    yao_pos = ("初" if moving_line == 0
               else "上" if moving_line == 5
               else "二三四五"[moving_line - 1])

    evidence = [
        f"节气: {jq_name}（索引{jq_index}）",
        f"节卦: {main_gua}·{yao_name}（第{moving_line}爻，{yao_pos}位）",
        f"值日: {yao_name}爻直十五日",
        "原典依据: 《河洛真数》起例卷之下·节候卦爻 L1492",
        f"原典节卦段: {JIE_GUA_QUOTE}",
        "体系说明: 本条为原典四正卦节卦表（坎震离兑×六爻×15日），"
        "非卦气歌/京房六日七分口径；后者属另一体系，见本模块 docstring 取证。",
    ]

    return SeasonalHexagram(
        jq_index=jq_index,
        jq_name=jq_name,
        main_gua=main_gua,
        moving_line=moving_line,
        result_gua=yao_name,
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


#: 带**时刻**的全年节气缓存（批次 L）。与 _JIEQI_TIMELINE 分开：
#: 后者只存 (Y,M,D,jq) 且有别的调用方，不能改它的形状。
_JIEQI_TIMELINE_FULL: dict[int, tuple] = {}


def jieqi_timeline(year: int):
    """某年的全部节气点（**带缓存**）→ tuple((Y, M, D, hh, mm, jq), …)，升序。

    ⚠ 必须带**时刻**。缓存表只存 (Y,M,D,jq) 时，拿它替掉 ``sxtwl.JD2DD(jd)``
      会把节气时刻抹成 00:00 —— 而农历月起点是带时刻的（如「1975-01-06 07:17」）。
      该回归由 tests/heluo/test_timeline_yun_perf.py::test_batch_matches_dayscan
      当场逮到：改快路径时最容易丢的就是没人看的那些字段。
    """
    try:
        import sxtwl
    except ImportError:
        return ()
    if year < 2:
        return ()
    cached = _JIEQI_TIMELINE_FULL.get(year)
    if cached is not None:
        return cached
    merged: dict[tuple[int, int, int, int, int, int], None] = {}
    for yy in (year - 1, year):
        for info in sxtwl.getJieQiByYear(yy):
            jd, idx = ((info.jd, info.jqIndex) if hasattr(info, "jd")
                       else (info[0], info[1]))
            t = sxtwl.JD2DD(jd)
            merged[(int(t.Y), int(t.M), int(t.D),
                    int(t.h), int(t.m), idx)] = None
    table = tuple(sorted(merged))
    _JIEQI_TIMELINE_FULL[year] = table
    if len(_JIEQI_TIMELINE_FULL) > _JIEQI_TIMELINE_MAX:
        for stale in list(_JIEQI_TIMELINE_FULL)[
                :len(_JIEQI_TIMELINE_FULL) - _JIEQI_TIMELINE_MAX]:
            _JIEQI_TIMELINE_FULL.pop(stale, None)
    return table


def solar_term_date(year: int, jq_index: int):
    """按年 + 节气索引取**该年该节气**的公历日；无则 ``None``。

    ⚠ 2026-10-08 批次 L 新增。原先河洛有两处**逐字相同**的 ``_find_jie``，
      靠逐日扫整月调 ``sxtwl.fromSolar`` 求节气日（canonical.py 与 guajie.py 各一份），
      一次调用 92 次 sxtwl，两处共 184 次做同一件事。
      而 ``sxtwl.getJieQiByYear`` 一次就能给出全年节气的精确日期。
      已实测 1900–2100 逐年 201 组**零不一致**（见 tools/…/verify_jq_equiv.py）。

    本函数复用 ``_jieqi_timeline`` 的按年缓存，重复调用不再打 sxtwl。
    """
    if not (0 <= jq_index < 24):
        return None
    try:
        import sxtwl
    except ImportError:
        return None
    if year < 2:
        return None
    for entry in _jieqi_timeline(sxtwl, year):
        y, mo, d, idx = entry
        if idx == jq_index and y == year:
            return date(y, mo, d)
    return None


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
    "SIXTY_GUA",
    "SIXTY_GUA_BY_JIEQI",
    "JIE_GUA_QUOTE",
    "SeasonalHexagram",
    "QiPhase",
    "get_seasonal_hexagram",
    "get_qi_phase",
    "get_current_jieqi_info",
]
