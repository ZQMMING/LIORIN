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
  3. 状态枚举：NORMAL / REVERSE / RESCUED / UNRESOLVED
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class HuaGongState(str, Enum):
    """化工状态。"""
    NORMAL = "NORMAL"       # 得位：卦中有机气
    REVERSE = "REVERSE"     # 反位：正对反对，非当令
    RESCUED = "RESCUED"     # 救应：虽相反但有相生
    UNRESOLVED = "UNRESOLVED"  # 无据：无法判定


# 四季 → 地支月 → 化工卦
# 原典："冬至后春分前，坎水用事，为化工；春木夏火，秋金冬水"
SEASON_BRANCH_TO_HUAGONG: dict[str, str] = {
    "亥": "坎", "子": "坎", "丑": "坎",   # 冬
    "寅": "震", "卯": "震", "辰": "震",   # 春
    "巳": "离", "午": "离", "未": "离",   # 夏
    "申": "兑", "酉": "兑", "戌": "兑",   # 秋
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


@dataclass(frozen=True)
class HuaGongResult:
    """化工计算结果。"""
    state: HuaGongState
    huagong_trigram: str          # 当令化工卦
    birth_month_branch: str       # 出生月支
    has_huagong: bool             # 先天/后天卦中是否有化工卦
    has_opposite: bool            # 先天/后天卦中是否有反卦
    evidence: list[str]           # 可审计证据链


def compute_huagong(
    prenatal_upper: str,
    prenatal_lower: str,
    postnatal_upper: str,
    postnatal_lower: str,
    birth_month_branch: str,
) -> HuaGongResult:
    """
    计算化工状态。

    算法：
    1. 确定当令化工卦（出生月支 → 四季 → 卦）
    2. 检查先天卦上下卦是否有机气
    3. 检查后天卦上下卦是否有机气
    4. 检查是否有正反对（反卦）
    5. 判定状态

    原典原则：
      "根基不得化工者，灾重也"
      "有化工之气者，艰难获福"
      "大象与小象化工虽相反，却又有相生者，则吉"
    """
    evidence: list[str] = []

    # Step 1: 确定当令化工卦
    huagong_trigram = SEASON_BRANCH_TO_HUAGONG.get(birth_month_branch, "?")
    opposite_trigram = OPPOSITE_TRIGRAM.get(huagong_trigram, "")

    # Step 2: 检查卦中是否有化工卦 / 反卦
    all_trigrams = {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower}
    has_huagong = huagong_trigram in all_trigrams
    has_opposite = opposite_trigram in all_trigrams

    evidence.append(f"出生月支{birth_month_branch} → 当令化工卦={huagong_trigram}")
    evidence.append(f"卦中含化工卦: {has_huagong}（{all_trigrams}）")
    if has_opposite:
        evidence.append(f"卦中含反卦{opposite_trigram}（{huagong_trigram}↔{opposite_trigram}）")

    # Step 3: 判定状态
    # 原典："根基得三元纯正，生气充畅者，名曰元气足"
    # 原典："根基杂乱，克贼交加者，名曰元气损"
    if has_huagong and not has_opposite:
        state = HuaGongState.NORMAL
        evidence.append("得位：卦中含当令化工卦，无正反对")
    elif has_huagong and has_opposite:
        # 虽有化工卦，但亦有反卦 → 需检查相生关系
        state = HuaGongState.RESCUED
        evidence.append(f"救应：含化工卦{huagong_trigram}但同时含反卦{opposite_trigram}，需五行相生救应")
    elif has_opposite and not has_huagong:
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
