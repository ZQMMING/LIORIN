"""H7: 元气计算模块

职责：计算天元气 / 地元气 / 人元气 / 元反（年柱配先天之气）。
原典依据：《河洛真数》起例卷之上·元气化工有无论 / 「正体若无，须看互体，互体又无，推及伏体」。

原典明文（data/heluo/guajie_raw/河洛真数_起例卷之上.txt）：
  1. 「凡人当生年天干为天元气，主贵，地支为地元气，主富，纳音为人元气，主寿。」
  2. 「假如壬甲戌亥生人得乾卦是也。」（干支纳卦：甲壬乾、乙癸坤、丙艮、丁兑、戊坎、己离、庚震、辛巽；
     支：戌亥乾、子坎、丑寅艮、卯震、辰巳巽、午离、未申坤、酉兑）
  3. 「卦无元气……正体若无，须看互体，互体又无，推及伏体，妙在通变，不可执一。
      如甲子生人得小过，虽卦中无乾兑金元气，然互体有兑，亦是纳音。」
  4. 「又如水命生人，天干地支俱无元气，而得乾兑之卦，是金能生水，亦可谓得元气也。」
  5. 「干支纳卦——木命生年干支所纳之卦，即纳音……」（六十甲子纳音 → 金乾兑 / 水坎 / 火离 / 土坤艮 / 木震巽）

原实现（2026-09-xx）只检查先天/后天的正体上下卦，漏「人元气（纳音）」以及「互体 / 伏体」兜底，
且漏「生我之卦亦得元气」的相生口径 —— 本版按原文补齐（D-017，2026-11-06）。

状态枚举：NORMAL（得元气）/ REVERSE（元反）/ UNRESOLVED
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class YuanQiState(str, Enum):
    """元气状态。"""
    NORMAL = "NORMAL"       # 得元气（卦中含天/地/人元气卦，含互体/伏体/相生）
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

# 六十甲子纳音（原典「干支纳卦」三十组，标准纳音序）
_NAYIN_60: tuple[str, ...] = (
    "金", "火", "木", "土", "金", "火", "水", "土", "金", "木",
    "水", "土", "火", "木", "水", "金", "火", "木", "土", "金",
    "火", "水", "土", "金", "木", "水", "土", "火", "木", "水",
)

# 纳音五行 → 所纳之卦（原典 干支纳卦 / 人元气）
_ELEMENT_TRIGRAMS: dict[str, set[str]] = {
    "金": {"乾", "兑"},
    "水": {"坎"},
    "火": {"离"},
    "土": {"坤", "艮"},
    "木": {"震", "巽"},
}

# 八卦五行
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 五行相生：我生者（键生值）
_WUXING_SHENG: dict[str, str] = {
    "金": "水", "水": "木", "木": "火", "火": "土", "土": "金",
}

# 八卦爻画（自下而上，1=阳 0=阴）
TRIGRAM_LINES: dict[str, tuple[int, int, int]] = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}
_LINES_TRIGRAM: dict[tuple[int, int, int], str] = {v: k for k, v in TRIGRAM_LINES.items()}

_GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"
_ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"


def nayin_element(year_stem: str, year_branch: str) -> str:
    """年柱干支 → 纳音五行（原典「纳音为人元气」）。

    非法干支组合（阳干配阴支等五鼠遁不可能出现的组合）返回空串。
    """
    if year_stem not in _GAN_ORDER or year_branch not in _ZHI_ORDER:
        return ""
    si = _GAN_ORDER.index(year_stem)
    bi = _ZHI_ORDER.index(year_branch)
    if si % 2 != bi % 2:  # 阳干配阳支、阴干配阴支
        return ""
    idx = next(i for i in range(60) if i % 10 == si and i % 12 == bi)
    return _NAYIN_60[idx // 2]


def _lines(upper: str, lower: str) -> list[int]:
    return list(TRIGRAM_LINES.get(lower, ())) + list(TRIGRAM_LINES.get(upper, ()))


def _hu_gua(upper: str, lower: str) -> tuple[str, str] | None:
    """互卦：下互取二三四爻，上互取三四五爻（原典「互体」）。"""
    lines = _lines(upper, lower)
    if len(lines) != 6:
        return None
    low = tuple(lines[1:4])
    up = tuple(lines[2:5])
    return _LINES_TRIGRAM.get(up), _LINES_TRIGRAM.get(low)


def _complement_pair(upper: str, lower: str) -> tuple[str, str] | None:
    """伏体（错卦）：上下卦各取对宫（六爻全变）。"""
    up, low = OPPOSITE_TRIGRAM.get(upper, ""), OPPOSITE_TRIGRAM.get(lower, "")
    if not up or not low:
        return None
    return up, low


def _scope_hits(
    qis: dict[str, set[str]],
    prenatal_upper: str, prenatal_lower: str,
    postnatal_upper: str, postnatal_lower: str,
) -> tuple[str, list[str]]:
    """按「正体 → 互体 → 伏体」顺序找元气卦，返回 (scope, 命中明细)。"""
    positive: dict[str, set[str]] = {
        "正体": {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower},
    }
    hu_xi = _hu_gua(prenatal_upper, prenatal_lower)
    hu_hou = _hu_gua(postnatal_upper, postnatal_lower)
    positive["互体"] = {t for pair in (hu_xi, hu_hou) if pair for t in pair}
    fu_xi = _complement_pair(prenatal_upper, prenatal_lower)
    fu_hou = _complement_pair(postnatal_upper, postnatal_lower)
    positive["伏体"] = {t for pair in (fu_xi, fu_hou) if pair for t in pair}

    for scope in ("正体", "互体", "伏体"):
        hits = [f"{kind}={t}（{scope}）"
                for kind, tri in qis.items() for t in sorted(tri) if t in positive[scope]]
        if hits:
            return scope, hits
    return "", []


@dataclass(frozen=True)
class YuanQiResult:
    """元气计算结果。"""
    tian_yuan_qi: str            # 天元气卦（年干纳甲）
    tian_yuan_fan: str           # 天元反卦（错卦）
    di_yuan_qi: str              # 地元气卦（年支后天宫）
    di_yuan_fan: str             # 地元反卦（错卦）
    ren_yuan_element: str = ""   # 人元气五行（年柱纳音）
    ren_yuan_qi: tuple[str, ...] = ()  # 人元气所纳之卦（原典 干支纳卦）
    state: YuanQiState = YuanQiState.UNRESOLVED  # 先天/后天卦中元气状态
    scope: str = ""              # 元气所在：正体 / 互体 / 伏体 / 相生 / 无
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
    计算元气状态（天元气 / 地元气 / 人元气 / 元反）。

    算法（原典）：
    1. 天元气 = 年干纳甲卦；地元气 = 年支后天宫卦；人元气 = 年柱纳音五行所纳之卦。
    2. 得元气：先天/后天卦的「正体」含三元气卦；正体无则看「互体」，互体无则看「伏体」。
    3. 天干地支俱无元气而卦得生我之卦者（如金生水），亦可谓得元气。
    4. 元反：卦中含天/地/人元气之错卦，且无元气。
    """
    tian = STEM_TO_TRIGRAM.get(year_stem, "?")
    tian_fan = OPPOSITE_TRIGRAM.get(tian, "")
    di = BRANCH_TO_TRIGRAM.get(year_branch, "?")
    di_fan = OPPOSITE_TRIGRAM.get(di, "")
    ren_el = nayin_element(year_stem, year_branch)
    ren = tuple(sorted(_ELEMENT_TRIGRAMS.get(ren_el, set())))

    evidence = [
        f"年干{year_stem} → 天元气={tian}（纳甲），天元反={tian_fan}",
        f"年支{year_branch} → 地元气={di}（后天宫位），地元反={di_fan}",
    ]
    if ren_el:
        evidence.append(f"年柱纳音={ren_el} → 人元气={'/'.join(ren)}（干支纳卦）")

    qis = {"天元气": {tian} if tian not in ("", "?") else set(),
           "地元气": {di} if di not in ("", "?") else set(),
           "人元气": set(ren)}

    scope, hits = _scope_hits(qis, prenatal_upper, prenatal_lower,
                              postnatal_upper, postnatal_lower)
    all_hit: list[str] = list(hits)

    positive = {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower}
    fan_hits = [t for t in (tian_fan, di_fan) if t and t in positive]
    if ren:
        fan_hits += [t for t in positive
                     if any(t == OPPOSITE_TRIGRAM.get(r, "") for r in ren)]
    fan_hits = sorted(set(fan_hits))

    # 优先级（原典）：正体/互体有元气 → 吉；正体见元气之错卦（二者俱反）→ 凶；
    # 其后才「推及伏体」，最后才是「生我之卦亦可谓得元气」。
    if scope in ("正体", "互体"):
        state = YuanQiState.NORMAL
        evidence.append(f"得元气（{scope}）：{'/'.join(all_hit)}")
        if fan_hits:
            evidence.append(f"卦中亦含元反之卦（{fan_hits}），元气为主")
    elif fan_hits:
        state = YuanQiState.REVERSE
        scope = ""
        evidence.append(f"元反：卦中含年柱元气错卦（{fan_hits}），且正体/互体无元气"
                        f"（原典「二者俱反，必贫穷困苦夭死」）")
    else:
        # 伏体 → 相生 兜底
        state = YuanQiState.UNRESOLVED
        if scope == "伏体":
            state = YuanQiState.NORMAL
            evidence.append(f"得元气（伏体）：{'/'.join(all_hit)}"
                            f"（原典「正体若无，须看互体，互体又无，推及伏体」）")
        elif ren_el:
            sheng = next((k for k, v in _WUXING_SHENG.items() if v == ren_el), "")
            if sheng:
                trigrams = set(positive)
                sheng_tri = sorted(t for t in trigrams if TRIGRAM_ELEMENT.get(t) == sheng)
                if sheng_tri:
                    scope = "相生"
                    all_hit = [f"{ren_el}命得{'/'.join(sheng_tri)}之卦（{sheng}生{ren_el}）"]
                    state = YuanQiState.NORMAL
                    evidence.append(f"得元气（相生）：{'/'.join(all_hit)}")
        if state != YuanQiState.NORMAL:
            state = YuanQiState.UNRESOLVED
            scope = ""
            evidence.append("无据：正体/互体/伏体既无元气卦，亦无元反卦，亦无生我之卦")

    return YuanQiResult(
        tian_yuan_qi=tian, tian_yuan_fan=tian_fan,
        di_yuan_qi=di, di_yuan_fan=di_fan,
        ren_yuan_element=ren_el, ren_yuan_qi=ren,
        state=state, scope=scope, evidence=evidence,
    )
