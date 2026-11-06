"""H11: 节候卦 / 卦气计算模块

职责：
  1. 节候卦：二十四节气 → 七十二候候卦（卦 + 爻位），并给出八节卦（四正卦）分领
  2. 卦气阶段：四正卦当值 / 辟卦 / 六日七分适用性

原典依据：`data/heluo/guajie_raw/河洛真数_起例卷之下.txt`「节候卦爻」段：

  "气之八节，总之其卦四，候有七十二，细分之，其卦六十。节卦坎初六起冬至，
   九二小寒，六三大寒，六四立春，九五雨水，上六惊蛰。震初九起春分，六二清明，
   六三谷雨，九四立夏，六五小满，上六芒种。离初九起夏至，六二小暑，九二大暑，
   九四立秋，六五处暑，上九白露。兑初九起秋分，九二寒露，九三霜降，九四立冬，
   九五小雪，上六大雪。每卦总管九十日，自下而上，每一爻各直十五日。
   候卦颐四爻起冬至蚯蚓结，中孚三爻麋角解，复二爻水泉动，屯初爻小寒雁北乡……"

  "生时值节卦者，谓之化工，生月值卦者，谓之得令。"

修正记录（D-018，2026-11-06）：
  旧实现 JIEHOU_GUA 的 24 条候卦与动爻/变卦来自二手网文，与本卷原文不符：
    立春应为小过初（旧作泰三）、春分应为晋四（旧作夬二）、夏至应为井四（旧作比四）、
    秋分应为大畜四（旧作丰四）、冬至颐四（唯一正确）……共 23/24 条不符。
  现按原卷「七十二候」逐条重建（HOU_GUA 为唯一真源，JIEHOU_GUA 由节气首候派生），
  并补八节卦 JIE_GUA（四正卦分领，原文首句）。
  变卦：原典未载「某爻动→某卦」，本模块的 result_gua 为机械爻变（候卦该爻阴阳翻转）
  派生值，证据串明确标注「派生，非原文断语」。

爻位索引：全模块统一 0-5（初爻=0，上爻=5），与 `heluo` 其他层（yuantang_index）一致。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .guajie import COMPOUND_GUA, hexagram_to_lines, _lines_to_gua


# ═══════════════════════════════════════════════════════════════
# 二十四节气（sxtwl jqIndex 0-23 顺序）
# ═══════════════════════════════════════════════════════════════

SOLAR_TERMS = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]

# 三画卦 → 卦象（用于拼全名：上象 + 下象 + 卦名）
_TRIGRAM_IMAGE = {
    "乾": "天", "兑": "泽", "离": "火", "震": "雷",
    "巽": "风", "坎": "水", "艮": "山", "坤": "地",
}

# 八纯卦全名
_PURE_FULL = {
    "乾": "乾为天", "坤": "坤为地", "坎": "坎为水", "离": "离为火",
    "震": "震为雷", "艮": "艮为山", "巽": "巽为风", "兑": "兑为泽",
}


def _gua_full(short: str) -> str:
    """短卦名 → 全名（如 颐 → 山雷颐；坎 → 坎为水）。"""
    if short in _PURE_FULL:
        return _PURE_FULL[short]
    up, low = COMPOUND_GUA.get(short, ("", ""))
    if not up or not low:
        return short
    return f"{_TRIGRAM_IMAGE[up]}{_TRIGRAM_IMAGE[low]}{short}"


def _result_gua(short: str, idx: int) -> str:
    """候卦该爻变后所得之卦（派生值，原典未载）。"""
    lines = hexagram_to_lines(short)
    if not 0 <= idx <= 5:
        raise ValueError(f"爻位索引必须 0-5，实得 {idx}")
    lines[idx] = 1 if lines[idx] == 0 else 0
    return _gua_full(_lines_to_gua(lines))


# ═══════════════════════════════════════════════════════════════
# 七十二候（起例卷之下·节候卦爻，逐条照录）
#   (节气索引, 候序 1-3, 候卦短名, 爻位索引 0-5, 候名)
# ═══════════════════════════════════════════════════════════════

HOU_GUA: tuple[tuple[int, int, str, int, str], ...] = (
    # 冬至
    (0, 1, "颐", 3, "蚯蚓结"),
    (0, 2, "中孚", 2, "麋角解"),
    (0, 3, "复", 1, "水泉动"),
    # 小寒
    (1, 1, "屯", 0, "雁北乡"),
    (1, 2, "屯", 5, "鹊始巢"),
    (1, 3, "谦", 4, "雉始雊"),
    # 大寒
    (2, 1, "睽", 3, "鸡乳"),
    (2, 2, "井", 2, "鹫鸟厉疾"),
    (2, 3, "临", 1, "水泽腹坚"),
    # 立春
    (3, 1, "小过", 0, "东风解冻"),
    (3, 2, "小过", 5, "蛰虫始振"),
    (3, 3, "蒙", 4, "鱼陟负冰"),
    # 雨水
    (4, 1, "益", 3, "獭祭鱼"),
    (4, 2, "渐", 2, "候雁北"),
    (4, 3, "泰", 2, "草木萌动"),
    # 惊蛰
    (5, 1, "需", 0, "桃始华"),
    (5, 2, "需", 5, "鸧鹒鸣"),
    (5, 3, "随", 4, "鹰化为鸠"),
    # 春分
    (6, 1, "晋", 3, "玄鸟至"),
    (6, 2, "解", 2, "雷乃发声"),
    (6, 3, "大壮", 1, "始电"),
    # 清明
    (7, 1, "豫", 0, "桐始华"),
    (7, 2, "豫", 5, "田鼠化为鴽"),
    (7, 3, "讼", 4, "虹始见"),
    # 谷雨
    (8, 1, "蛊", 3, "萍始生"),
    (8, 2, "革", 2, "鸣鸠拂其羽"),
    (8, 3, "夬", 1, "戴胜降于桑"),
    # 立夏
    (9, 1, "旅", 0, "蝼蝈鸣"),
    (9, 2, "旅", 5, "蚯蚓出"),
    (9, 3, "师", 4, "王瓜生"),
    # 小满
    (10, 1, "比", 3, "苦菜秀"),
    (10, 2, "小畜", 2, "靡草死"),
    (10, 3, "乾", 2, "麦秋至"),
    # 芒种
    (11, 1, "大有", 0, "螳螂生"),
    (11, 2, "大有", 5, "鸱始鸣"),
    (11, 3, "家人", 4, "反舌无声"),
    # 夏至
    (12, 1, "井", 3, "鹿角解"),
    (12, 2, "咸", 2, "蜩始鸣"),
    (12, 3, "姤", 1, "半夏生"),
    # 小暑
    (13, 1, "鼎", 0, "温风至"),
    (13, 2, "鼎", 5, "蟋蟀居壁"),
    (13, 3, "丰", 4, "鹰始挚"),
    # 大暑
    (14, 1, "涣", 3, "腐草为萤"),
    (14, 2, "履", 2, "土润溽暑"),
    (14, 3, "随", 2, "大雨时行"),
    # 立秋
    (15, 1, "恒", 0, "凉风至"),
    (15, 2, "恒", 5, "白露降"),
    (15, 3, "节", 4, "寒蝉鸣"),
    # 处暑
    (16, 1, "同人", 3, "鹰乃祭鸟"),
    (16, 2, "损", 2, "天地始肃"),
    (16, 3, "否", 1, "禾乃登"),
    # 白露
    (17, 1, "巽", 0, "鸿雁来"),
    (17, 2, "巽", 5, "玄鸟归"),
    (17, 3, "萃", 4, "群鸟养羞"),
    # 秋分
    (18, 1, "大畜", 3, "雷始收声"),
    (18, 2, "贲", 2, "蛰虫坯户"),
    (18, 3, "观", 1, "水始涸"),
    # 寒露
    (19, 1, "归妹", 0, "鸿雁来宾"),
    (19, 2, "归妹", 5, "雀入大水为蛤"),
    (19, 3, "无妄", 4, "菊有黄花"),
    # 霜降
    (20, 1, "明夷", 3, "豺乃祭兽"),
    (20, 2, "困", 2, "草木黄落"),
    (20, 3, "剥", 1, "蛰虫咸俯"),
    # 立冬
    (21, 1, "艮", 0, "水始冰"),
    (21, 2, "艮", 5, "地始冻"),
    (21, 3, "既济", 4, "雉入大水为蜃"),
    # 小雪
    (22, 1, "噬嗑", 3, "虹藏不见"),
    (22, 2, "大过", 2, "天气上升地气下降"),
    (22, 3, "坤", 1, "闭塞而成冬"),
    # 大雪
    (23, 1, "未济", 0, "鹖不鸣"),
    (23, 2, "未济", 5, "虎始交"),
    (23, 3, "蹇", 4, "荔挺出"),
)

# 节气首候（候序=1）——节候卦的「主卦」
HOU_GUA_BY_JQ: dict[int, tuple[str, int, str]] = {
    jq: (short, idx, hou) for jq, seq, short, idx, hou in HOU_GUA if seq == 1
}

# 八节卦（四正卦分领二十四节气，原文首句）：jqIndex → (四正卦短名, 爻位索引)
JIE_GUA: dict[int, tuple[str, int]] = {
    0: ("坎", 0), 1: ("坎", 1), 2: ("坎", 2),
    3: ("坎", 3), 4: ("坎", 4), 5: ("坎", 5),
    6: ("震", 0), 7: ("震", 1), 8: ("震", 2),
    9: ("震", 3), 10: ("震", 4), 11: ("震", 5),
    12: ("离", 0), 13: ("离", 1), 14: ("离", 2),
    15: ("离", 3), 16: ("离", 4), 17: ("离", 5),
    18: ("兑", 0), 19: ("兑", 1), 20: ("兑", 2),
    21: ("兑", 3), 22: ("兑", 4), 23: ("兑", 5),
}
# 注意：原文作「离初九起夏至，六二小暑，九二大暑，九四立秋」，离卦无「九二大暑」之爻
# （离九三为大暑位），疑刻本讹字，按离卦爻序 初九/六二/九三/九四/六五/上九 排列，
# 登记为 data issue（不影响候卦层）。

# 节气 → (候卦全名, 爻位索引 0-5, 派生变卦全名)
JIEHOU_GUA: dict[int, tuple[str, int, str]] = {
    jq: (_gua_full(short), idx, _result_gua(short, idx))
    for jq, (short, idx, _hou) in HOU_GUA_BY_JQ.items()
}

# 节气 → 候卦全名（快速查询）
JIEHOU_GUA_NAME: dict[int, str] = {idx: data[0] for idx, data in JIEHOU_GUA.items()}

# 节气 → 首候候名
JIEHOU_HOU: dict[int, str] = {jq: hou for jq, (_s, _i, hou) in HOU_GUA_BY_JQ.items()}


# ═══════════════════════════════════════════════════════════════
# 卦气：六十卦配周天（京房六日七分法）
# ═══════════════════════════════════════════════════════════════

# 四正卦（坎离震兑）分管二十四节气，不入六十卦
SIZHENG_GUA = {"坎", "离", "震", "兑"}

# 辟卦（十二消息卦）分领十二月
BI_GUA = ["复", "临", "泰", "大壮", "夬", "乾",
          "姤", "观", "否", "遁", "剥", "坤"]

# 节气 → 当值辟卦（按节气所属月建；节令月首者领全月，中气者同月）
#   子月复（冬至/大雪）、丑月临（小寒/大寒）、寅月泰（立春/雨水）、卯月大壮（惊蛰/春分）、
#   辰月夬（清明/谷雨）、巳月乾（立夏/小满）、午月姤（芒种/夏至）、未月遁（小暑/大暑）、
#   申月否（立秋/处暑）、酉月观（白露/秋分）、戌月剥（寒露/霜降）、亥月坤（立冬/小雪）
BI_GUA_BY_JQ: dict[int, str] = {
    0: "复", 1: "临", 2: "临", 3: "泰", 4: "泰", 5: "大壮",
    6: "大壮", 7: "夬", 8: "夬", 9: "乾", 10: "乾", 11: "姤",
    12: "姤", 13: "遁", 14: "遁", 15: "否", 16: "否", 17: "观",
    18: "观", 19: "剥", 20: "剥", 21: "坤", 22: "坤", 23: "复",
}

# 六十四卦（文王序）
_WENWANG_ORDER = (
    "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履",
    "泰", "否", "同人", "大有", "谦", "豫", "随", "蛊", "临", "观",
    "噬嗑", "贲", "剥", "复", "无妄", "大畜", "颐", "大过", "坎", "离",
    "咸", "恒", "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
    "损", "益", "夬", "姤", "萃", "升", "困", "井", "革", "鼎",
    "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节",
    "中孚", "小过", "既济", "未济",
)

# 六十卦（去四正卦）——六日七分法用
# 旧表（2026-11-06 前）含重复项（贲/困/涣/节/损各两次）与讹字「宜」，已按文王序去四正重建。
SIXTY_GUA = tuple(n for n in _WENWANG_ORDER if n not in SIZHENG_GUA)


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SeasonalHexagram:
    """节候卦结果。"""
    jq_index: int                  # 节气索引 0-23
    jq_name: str                   # 节气名称
    main_gua: str                  # 节候主卦（七十二候候卦全名）
    moving_line: int               # 候卦爻位索引 0-5（初=0）
    result_gua: str                # 该爻变后之卦（派生，原典未载）
    jie_gua: str                   # 八节卦（四正卦）全名
    jie_line: int                  # 八节卦爻位索引 0-5
    hou: str                       # 该节气首候候名
    evidence: list[str]            # 可审计证据


@dataclass(frozen=True)
class QiPhase:
    """卦气阶段结果。"""
    year: int
    jq_index: int
    jq_name: str
    main_gua: str
    is_sizheng: bool               # 是否为二至二分（四正卦当值之节）
    is_bi_gua: bool                # 该节气所属月建是否有辟卦当值（恒真，保留字段）
    six_day_seven_method: bool     # 是否适用六日七分法（二至二分让位于四正卦）
    bi_gua: str = ""               # 当值辟卦（消息卦短名）


_YAO_POS = ("初", "二", "三", "四", "五", "上")


def _yao_label(idx: int, lines: Optional[list[int]] = None) -> str:
    """爻位索引 → 原典爻名（初六/九二…）。不知道阴阳时用「第N爻」。"""
    if not 0 <= idx <= 5:
        return f"第{idx}爻"
    if lines is None:
        return f"第{idx}爻"
    yang = lines[idx] == 1
    if idx == 0:
        return "初九" if yang else "初六"
    if idx == 5:
        return "上九" if yang else "上六"
    return ("九" if yang else "六") + _YAO_POS[idx]


# ═══════════════════════════════════════════════════════════════
# 核心计算函数
# ═══════════════════════════════════════════════════════════════

def get_seasonal_hexagram(jq_index: int) -> SeasonalHexagram:
    """
    根据节气索引获取节候卦。

    原典（起例卷之下·节候卦爻）：二十四节气各领三候，候卦「颐四爻起冬至…」
    逐候轮值；本函数取该节气首候的候卦与爻位。

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
    hou = JIEHOU_HOU[jq_index]
    jie_short, jie_line = JIE_GUA[jq_index]
    jie_gua = _gua_full(jie_short)
    short = HOU_GUA_BY_JQ[jq_index][0]
    hou_lines = hexagram_to_lines(short)
    jie_lines = hexagram_to_lines(jie_short)

    evidence = [
        f"节气: {jq_name}（索引{jq_index}）",
        f"节候候卦: {main_gua}·{_yao_label(moving_line, hou_lines)}"
        f"（二十四节气各领三候，首候「{hou}」）",
        f"八节卦（四正分领）: {jie_gua}·{_yao_label(jie_line, jie_lines)}",
        f"派生变卦: {result_gua}（该爻阴阳翻转所得，原典未载变卦，仅作参考）",
        "原典依据: 《河洛真数》起例卷之下·节候卦爻"
        "「气之八节，总之其卦四，候有七十二，细分之，其卦六十……"
        "候卦颐四爻起冬至蚯蚓结……生时值节卦者谓之化工，生月值卦者谓之得令」",
    ]

    return SeasonalHexagram(
        jq_index=jq_index,
        jq_name=jq_name,
        main_gua=main_gua,
        moving_line=moving_line,
        result_gua=result_gua,
        jie_gua=jie_gua,
        jie_line=jie_line,
        hou=hou,
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
    short = HOU_GUA_BY_JQ.get(jq_index, ("", 0, ""))[0]

    # 二至二分 = 八节卦中的四正卦当值之节（坎冬至/震春分/离夏至/兑秋分）
    is_sizheng = jq_index in (0, 6, 12, 18)
    # 辟卦按「节气所属月建当值之消息卦」，旧实现误把节气名当辟卦判据
    is_bi_gua = jq_index in BI_GUA_BY_JQ
    # 六日七分（六十卦配周天）让位于四正卦主气之二至二分
    six_day_seven_method = not is_sizheng

    return QiPhase(
        year=year,
        jq_index=jq_index,
        jq_name=jq_name,
        main_gua=main_gua,
        is_sizheng=is_sizheng,
        is_bi_gua=is_bi_gua,
        six_day_seven_method=six_day_seven_method,
        bi_gua=BI_GUA_BY_JQ.get(jq_index, ""),
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
    "HOU_GUA",
    "HOU_GUA_BY_JQ",
    "JIE_GUA",
    "JIEHOU_GUA",
    "JIEHOU_GUA_NAME",
    "JIEHOU_HOU",
    "SIZHENG_GUA",
    "BI_GUA",
    "BI_GUA_BY_JQ",
    "SIXTY_GUA",
    "SeasonalHexagram",
    "QiPhase",
    "get_seasonal_hexagram",
    "get_qi_phase",
    "get_current_jieqi_info",
]
