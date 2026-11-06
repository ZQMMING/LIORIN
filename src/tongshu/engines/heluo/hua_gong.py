"""H6: 化工计算模块

职责：判断先天卦/后天卦是否得"天地生生化化之妙"。
原典依据：《河洛真数》起例卷下·论化工 + 逢化工诗

冻结规则：
  1. 四季对应化工卦：
     - 冬（亥子丑月）→ 坎 ☵
     - 春（寅卯辰月）→ 震 ☳
     - 夏（巳午未月）→ 离 ☲
     - 秋（申酉戌月）→ 兑 ☱
  2. 正对反对：
     - 坎 ↔ 离（冬夏相反）
     - 震 ↔ 兑（春秋相反）
  3. 状态枚举：NORMAL / REVERSE / RESCUED / RESTRAINED / UNRESOLVED
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class HuaGongState(str, Enum):
    """化工状态。"""
    NORMAL = "NORMAL"           # 得位：卦中有当令化工卦，无正对反对
    REVERSE = "REVERSE"         # 反位：正对反对，非当令
    RESCUED = "RESCUED"         # 救应：虽相反但有相生救应
    RESTRAINED = "RESTRAINED"   # 受制：虽相反且化工受反卦克制、无相生救应 → 尤凶
    UNRESOLVED = "UNRESOLVED"   # 无据：无法判定


# 四季 → 地支月 → 化工卦
# 原典："冬至后春分前，坎水用事，为化工；春木夏火，秋金冬水"
SEASON_BRANCH_TO_HUAGONG: dict[str, str] = {
    # 原典（化工论）："坎卦自冬至十一月中以后至惊蛰终止" → 子丑寅
    "子": "坎", "丑": "坎", "寅": "坎",
    # "震卦自春分二月中以后至芒种终止" → 卯辰巳
    "卯": "震", "辰": "震", "巳": "震",
    # "离卦自夏至五月中以后至白露终止" → 午未申
    "午": "离", "未": "离", "申": "离",
    # "兑卦自秋分八月中以后至大雪终止" → 酉戌亥
    "酉": "兑", "戌": "兑", "亥": "兑",
}

# 四季月（辰戌丑未）："坤艮卦主四季辰戌丑未月，除正节气十二日外，各旺十八日。
# 妇人得此，名儿女星，又为贞母节妇。" → 土旺月坤艮亦可为化工。
TU_WANG_BRANCHES: tuple[str, ...] = ("辰", "戌", "丑", "未")
TU_WANG_TRIGRAMS: tuple[str, ...] = ("坤", "艮")

# 纳音五行 → 纳甲卦（原典："若正互俱无，则取纳甲纳音，终是浅薄，福寿减半"）。
NAYIN_ELEMENT_TO_TRIGRAMS: dict[str, tuple[str, str]] = {
    "金": ("乾", "兑"), "水": ("坎", "坎"), "火": ("离", "离"),
    "土": ("坤", "艮"), "木": ("震", "巽"),
}

# 化工正反对：反卦判断（原典《化工相反图》，起例卷之上）
#   "坎卦…与离相反"（冬夏）
#   "兑卦…与震相反" / "震卦…与兑相反"（春秋）
# 故化工反对 = 坎↔离、兑↔震（季节相对）。
# 注意：此为化工语境下的反对（四季相反），不同于卦象"错卦/对宫"
# （乾↔坤、坎↔离、震↔巽、艮↔兑，见 guajie.py）——两者不混用。
OPPOSITE_TRIGRAM: dict[str, str] = {
    "坎": "离", "离": "坎",
    "兑": "震", "震": "兑",
}

# 五行相生 / 相克（《河洛真数》化工论"彼此相生…忌克制"，起例卷之上 L193/L203）
from .numbers import TRIGRAM_ELEMENT, TRIGRAM_LINES

_SHENG: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE: dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _is_sheng(a: str, b: str) -> bool:
    """a 五行生 b 五行（如 水→木）。"""
    return bool(a and b and _SHENG.get(a) == b)


def _is_ke(a: str, b: str) -> bool:
    """a 五行克 b 五行（如 金→木）。"""
    return bool(a and b and _KE.get(a) == b)


@dataclass(frozen=True)
class HuaGongResult:
    """化工计算结果。"""
    state: HuaGongState
    huagong_trigram: str          # 当令化工卦
    birth_month_branch: str       # 出生月支
    has_huagong: bool             # 先天/后天卦中是否有化工卦
    has_opposite: bool            # 先天/后天卦中是否有反卦
    evidence: list[str]           # 可审计证据链
    scope: str = ""               # 化工来源：正体 / 土旺 / 互体 / 纳音
    weak: bool = False            # 纳音代用 → 原典"终是浅薄，福寿减半"
    tu_wang: bool = False         # 是否四季月（辰戌丑未）


def _hexagram_lines(upper: str, lower: str) -> list[int]:
    """上下卦 → 六爻（自下而上，1=阳 0=阴）。"""
    out: list[int] = []
    for tri in (lower, upper):
        for v in TRIGRAM_LINES.get(tri, (0, 0, 0)):
            out.append(1 if v > 0 else 0)
    return out


_LINES_TO_TRIGRAM: dict[tuple[int, int, int], str] = {
    (1, 1, 1): "乾", (1, 1, 0): "兑", (1, 0, 1): "离", (1, 0, 0): "震",
    (0, 1, 1): "巽", (0, 1, 0): "坎", (0, 0, 1): "艮", (0, 0, 0): "坤",
}


def hu_trigrams(upper: str, lower: str) -> tuple[str, str]:
    """互体（上互, 下互）：三四五爻为上互、二三四爻为下互。"""
    lines = _hexagram_lines(upper, lower)
    up = _LINES_TO_TRIGRAM.get(tuple(lines[2:5]), "")
    lo = _LINES_TO_TRIGRAM.get(tuple(lines[1:4]), "")
    return up, lo


def compute_huagong(
    prenatal_upper: str,
    prenatal_lower: str,
    postnatal_upper: str,
    postnatal_lower: str,
    birth_month_branch: str,
    nayin_element: str | None = None,
    gender: str | None = None,
) -> HuaGongResult:
    """
    计算化工状态（原典《河洛真数·起例卷之上·化工论》）。

    判据层级（原典）：
      1. 当令化工卦按**节气区间**定（冬至→惊蛰=坎 / 春分→芒种=震 /
         夏至→白露=离 / 秋分→大雪=兑）；
      2. 四季月（辰戌丑未）土旺十八日，坤艮亦为化工（女命=儿女星/贞母节妇）；
      3. 正体若无，取互体；正互俱无，取纳甲纳音（浅薄，福寿减半）；
      4. 正对反对见"化工相反图"：坎反离 / 离反坎 / 兑反震 / 震反兑；
         相反而又有相生者吉，忌克制尤凶。
    """
    evidence: list[str] = []

    huagong_trigram = SEASON_BRANCH_TO_HUAGONG.get(birth_month_branch, "?")
    opposite_trigram = OPPOSITE_TRIGRAM.get(huagong_trigram, "")
    tu_wang = birth_month_branch in TU_WANG_BRANCHES
    evidence.append(f"出生月支{birth_month_branch} → 当令化工卦={huagong_trigram}")
    if tu_wang:
        evidence.append(
            "四季月（辰戌丑未）土旺十八日，坤艮亦为化工"
        )

    zheng_trigrams = (
        prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower,
    )

    def _hit(scope_label: str) -> tuple[str, str] | None:
        for tri in zheng_trigrams:
            if tri == huagong_trigram:
                return scope_label, tri
            if tu_wang and tri in TU_WANG_TRIGRAMS:
                return "土旺", tri
        return None

    hit = _hit("正体")
    scope = ""
    weak = False
    hit_trigram = huagong_trigram
    if hit:
        scope, hit_trigram = hit
        if scope == "土旺":
            evidence.append(
                f"正体见{hit_trigram}（四季土旺）→ 得化工"
                + ("；女命得坤艮=儿女星/贞母节妇" if gender in ("female", "女") else "")
            )
        else:
            evidence.append(f"正体见{hit_trigram}（当令化工卦）")
    else:
        for label, (u, l) in (
            ("先天", (prenatal_upper, prenatal_lower)),
            ("后天", (postnatal_upper, postnatal_lower)),
        ):
            for hu in hu_trigrams(u, l):
                if not hu:
                    continue
                if hu == huagong_trigram or (tu_wang and hu in TU_WANG_TRIGRAMS):
                    scope, hit_trigram = "互体", hu
                    evidence.append(
                        f"正体不逢，{label}互体得{hu} → 得化工"
                        "（原典：正体若无，须看互体）"
                    )
                    break
            if scope:
                break
        if not scope and nayin_element:
            h_el = TRIGRAM_ELEMENT.get(huagong_trigram, "")
            # 原典："若正互俱无，则取纳甲纳音，终是浅薄，福寿减半"
            if h_el and (nayin_element == h_el or _is_sheng(nayin_element, h_el)):
                scope, weak = "纳音", True
                hit_trigram = huagong_trigram
                rel = "同气" if nayin_element == h_el else f"生{huagong_trigram}({h_el})"
                evidence.append(
                    f"正互俱无，纳音{nayin_element}{rel}代用"
                    " → 终是浅薄，福寿减半"
                )

    has_huagong = bool(scope)
    has_opposite = bool(opposite_trigram) and any(
        tri == opposite_trigram for tri in zheng_trigrams
    )

    if has_huagong and not has_opposite:
        state = HuaGongState.NORMAL
        if weak:
            evidence.append("纳音代用得化工（原典：终是浅薄，福寿减半），无正反对")
        else:
            evidence.append("得位：得当令化工卦，无正反对")
    elif has_huagong and has_opposite:
        h_el = TRIGRAM_ELEMENT.get(hit_trigram, "")
        o_el = TRIGRAM_ELEMENT.get(opposite_trigram, "")
        others = [tri for tri in zheng_trigrams if tri not in (hit_trigram, opposite_trigram)]
        o_ke_h = _is_ke(o_el, h_el)
        rescue = any(
            _is_sheng(TRIGRAM_ELEMENT.get(r, ""), h_el)
            or _is_ke(TRIGRAM_ELEMENT.get(r, ""), o_el)
            for r in others
        )
        if o_ke_h and not rescue:
            state = HuaGongState.RESTRAINED
            evidence.append(
                f"受制：化工卦{hit_trigram}被反卦{opposite_trigram}克制"
                f"（{o_el}克{h_el}）且无相生救应 → 尤凶（原典：但忌克制，尤凶）"
            )
        else:
            state = HuaGongState.RESCUED
            evidence.append(
                f"救应：含化工卦{hit_trigram}与反卦{opposite_trigram}，"
                + ("有相生救应（他卦生化工或克反卦）" if rescue else "化工得势不为祸（化工克反卦）")
            )
    elif has_opposite:
        state = HuaGongState.REVERSE
        evidence.append(f"反位：卦中含反卦{opposite_trigram}，无当令化工卦")
    else:
        state = HuaGongState.UNRESOLVED
        evidence.append("无据：卦中既无化工卦也无反卦")

    return HuaGongResult(
        state=state,
        huagong_trigram=huagong_trigram,
        birth_month_branch=birth_month_branch,
        has_huagong=has_huagong,
        has_opposite=has_opposite,
        evidence=evidence,
        scope=scope,
        weak=weak,
        tu_wang=tu_wang,
    )


# 节令月：以十二"节"（立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/立冬/大雪/小寒）
# 为月界，确定出生日所属月支。索引与 jiehhou.SOLAR_TERMS 一致（0=冬至…23=大雪）。
# 月支对应"节"：立春→寅、惊蛰→卯、清明→辰、立夏→巳、芒种→午、小暑→未、
#               立秋→申、白露→酉、寒露→戌、立冬→亥、大雪→子、小寒→丑
JIE_INDEX_TO_BRANCH: dict[int, str] = {
    3: "寅", 5: "卯", 7: "辰", 9: "巳", 11: "午", 13: "未",
    15: "申", 17: "酉", 19: "戌", 21: "亥", 23: "子", 1: "丑",
}


def resolve_birth_month_branch(birth_date: str) -> str | None:
    """
    按节气节令月精确定出生日所属月支（取代公历月份近似）。

    以出生时刻之前最近的一个"节"（立春/惊蛰/…/小寒）为月界定月支，
    正确处理跨年冬至与节气边界（如 11-03 立冬前属戌月，而非亥月）。

    Args:
        birth_date: 公历日期 ISO 格式（YYYY-MM-DD）

    Returns:
        月支（寅/卯/…/丑），sxtwl 不可用或无法定位时返回 None
    """
    try:
        import sxtwl
        from datetime import datetime
        bd = datetime.fromisoformat(birth_date)
    except Exception:
        return None

    try:
        candidates: list[tuple[datetime, str]] = []
        for yr in (bd.year - 1, bd.year):
            for info in sxtwl.getJieQiByYear(yr):
                branch = JIE_INDEX_TO_BRANCH.get(info.jqIndex)
                if branch is None:
                    continue
                dt = sxtwl.JD2DD(info.jd)
                t = datetime(dt.Y, dt.M, dt.D, int(dt.h), int(dt.m), int(dt.s))
                candidates.append((t, branch))
        past = [c for c in candidates if c[0] <= bd]
        if not past:
            return None
        return max(past, key=lambda c: c[0])[1]
    except Exception:
        return None
