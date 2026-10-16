"""H7: 元气计算模块

职责：计算天元气 / 地元气 / 元反（年柱配先天之气）。
原典依据：《河洛真数》起例卷下·论元气；案例互证（2013乾造/卢某/王嵩淮）。

冻结算法（已破解并三案例互证）：
  1. 天元气 = 年干纳甲卦：
     - 甲壬 → 乾，乙癸 → 坤，丙 → 艮，丁 → 兑，
       戊 → 坎，己 → 离，庚 → 震，辛 → 巽
     - 证：癸巳年→"天元气坤"（癸→坤 ✓）；戊申年→"元气坎"（戊→坎 ✓）
  2. 地元气 = 年支后天八卦宫位（二十四山宫）：
     - 子→坎，丑寅→艮，卯→震，辰巳→巽，
       午→离，未申→坤，酉→兑，戌亥→乾
     - 证：癸巳年→"地元气巽"（巳→巽 ✓）；甲辰年→"年支元气相反(震)"（辰→巽，反=震 ✓）
  3. 元反 = 错卦（对宫）：乾↔坤、坎↔离、震↔巽、艮↔兑
  4. 化工 = 月支四季卦（见 hua_gong.py，冬坎/春震/夏离/秋兑）
     化工反 = 错卦（证：壬戌月→"化工兑、化工反艮" ✓）

状态枚举：NORMAL（得元气）/ REVERSE（元反）/ UNRESOLVED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class YuanQiState(str, Enum):
    """元气状态。"""
    NORMAL = "NORMAL"       # 得元气（卦中含天元气/地元气卦）
    REVERSE = "REVERSE"     # 元反（卦中含错卦）
    UNRESOLVED = "UNRESOLVED"  # 无据


# 天干纳甲 → 卦（河洛元气用）
STEM_TO_TRIGRAM: dict[str, str] = {
    "甲": "乾", "壬": "乾",
    "乙": "坤", "癸": "坤",
    "丙": "艮", "丁": "兑",
    "戊": "坎", "己": "离",
    "庚": "震", "辛": "巽",
}

# 地支后天八卦宫位（二十四山）
BRANCH_TO_TRIGRAM: dict[str, str] = {
    "子": "坎", "丑": "艮", "寅": "艮",
    "卯": "震", "辰": "巽", "巳": "巽",
    "午": "离", "未": "坤", "申": "坤",
    "酉": "兑", "戌": "乾", "亥": "乾",
}

# 错卦（先天方位对宫，六爻全变）
OPPOSITE_TRIGRAM: dict[str, str] = {
    "乾": "坤", "坤": "乾",
    "坎": "离", "离": "坎",
    "震": "巽", "巽": "震",
    "艮": "兑", "兑": "艮",
}


@dataclass(frozen=True)
class YuanQiResult:
    """元气计算结果。"""
    tian_yuan_qi: str            # 天元气卦（年干纳甲）
    tian_yuan_fan: str           # 天元反卦（错卦）
    di_yuan_qi: str              # 地元气卦（年支后天宫）
    di_yuan_fan: str             # 地元反卦（错卦）
    state: YuanQiState           # 先天/后天卦中元气状态
    evidence: list[str] = field(default_factory=list)


def compute_yuan_qi(
    year_stem: str,
    year_branch: str,
    prenatal_upper: str,
    prenatal_lower: str,
    postnatal_upper: str,
    postnatal_lower: str,
) -> YuanQiResult:
    """
    计算元气状态。

    算法：
    1. 天元气 = 年干纳甲卦；天元反 = 错卦
    2. 地元气 = 年支后天宫卦；地元反 = 错卦
    3. 检查先天/后天卦中是否含元气卦（得元气）或错卦（元反）
    """
    tian = STEM_TO_TRIGRAM.get(year_stem, "?")
    tian_fan = OPPOSITE_TRIGRAM.get(tian, "")
    di = BRANCH_TO_TRIGRAM.get(year_branch, "?")
    di_fan = OPPOSITE_TRIGRAM.get(di, "")

    evidence = [
        f"年干{year_stem} → 天元气={tian}（纳甲），天元反={tian_fan}",
        f"年支{year_branch} → 地元气={di}（后天宫位），地元反={di_fan}",
    ]

    all_trigrams = {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower}
    has_qi = (tian in all_trigrams) or (di in all_trigrams)
    has_fan = (tian_fan in all_trigrams) or (di_fan in all_trigrams)

    evidence.append(f"先天/后天卦含元气卦: {has_qi}（{all_trigrams}）")
    if has_fan:
        evidence.append(f"卦中含元反卦: {has_fan}（{tian_fan}/{di_fan}）")

    if has_qi and not has_fan:
        state = YuanQiState.NORMAL
        evidence.append("得元气：卦中含年柱元气卦，无元反")
    elif has_fan and not has_qi:
        state = YuanQiState.REVERSE
        evidence.append("元反：卦中含年柱错卦，无元气卦（需参看原典断语）")
    elif has_qi and has_fan:
        state = YuanQiState.NORMAL
        evidence.append("既有元气卦亦有反卦，元气为主")
    else:
        state = YuanQiState.UNRESOLVED
        evidence.append("无据：卦中既无元气卦亦无元反卦")

    return YuanQiResult(
        tian_yuan_qi=tian, tian_yuan_fan=tian_fan,
        di_yuan_qi=di, di_yuan_fan=di_fan,
        state=state, evidence=evidence,
    )
