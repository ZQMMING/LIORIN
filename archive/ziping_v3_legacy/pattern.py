# -*- coding: utf-8 -*-
"""ZIPING V3.1 建格判定 (PATTERN) — §15 格局八格十项.

基于月令藏干透干 → 格神 → 成格/破格判定.
铁律: 纯确定性布尔规则, LLM不得修改.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .constants import BRANCH_ELEMENT, STEM_ELEMENT, GENERATES, CONTROLS
from .engine import EngineContext, JudgmentBuilder, Rule
from .judgment_ext import (
    _stem_tengods, _hidden_tengods,
    _SHENG, _TONG, _XIE, _HAO, _KE,
)
from .types import (
    FrozenBaziFact, MethodScope, UndeterminedReason,
    ZiPingDerivedFact, ZiPingJudgment,
)

# 中文十神 → 英文标识 (用于模式匹配)
_TG_EN = {
    "正官": "OFFICER", "七杀": "KILL",
    "正财": "WEALTH", "偏财": "WEALTH",
    "正印": "RESOURCE", "偏印": "RESOURCE",
    "食神": "FOOD", "伤官": "INJURY",
    "比肩": "COMpanion", "劫财": "COMpanion",
}

# 建禄/阳刃表 (日主 → [建禄地支, 阳刃地支]) — 拼音格式
LUWU_TABLE = {
    "BING": ("SI", "WU"), "DING": ("WU", "SI"),
    "WU": ("SI", "WU"), "JI": ("WU", "SI"),
    "GENG": ("SHEN", "YOU"), "XIN": ("YOU", "SHEN"),
    "REN": ("HAI", "ZI"), "GUI": ("ZI", "HAI"),
    "JIA": ("YIN", "MAO"), "YI": ("MAO", "YIN"),
}

# 十神五行 (基于日主)
TG_5X = {
    "正官": "OFFICER", "七杀": "OFFICER",
    "正财": "WEALTH", "偏财": "WEALTH",
    "正印": "RESOURCE", "偏印": "RESOURCE",
    "食神": "OUTPUT", "伤官": "OUTPUT",
    "比肩": "COMpanion", "劫财": "COMpanion",
}


def judge_pattern(
    ctx: EngineContext,
    derived: ZiPingDerivedFact,
    strength: Optional[ZiPingJudgment] = None,
) -> ZiPingJudgment:
    """建格判定: 月令取格 → 格神 → 成格/破格.

    §15 规则集:
    - PATTERN-SELECT-001~006: 取格 (月令透干优先)
    - PATTERN-OFFICER-001~004: 官格
    - PATTERN-WEALTH-001~005: 财格
    - PATTERN-RESOURCE-001~006: 印格
    - PATTERN-FOOD-001~005: 食神格
    - PATTERN-KILL-001~003: 七杀格
    - PATTERN-INJURY-001~006: 伤官格
    - PATTERN-BLADE-001~003: 阳刃格
    - PATTERN-LU-001~006: 建禄/月劫格

    Returns:
        ZiPingJudgment with state ∈ {CANDIDATE, FORMED, FAILED, ...}
    """
    fact = ctx.fact
    month_branch = fact.month_branch  # 月令地支 (拼音)
    day_master = fact.day_master     # 日主天干 (拼音)

    # ── 1. 取格: 月令藏干透干判定 ──────────────────────────────
    month_hidden = fact.hidden_stems.get("MONTH", {})
    main_stem = month_hidden.get("main", "")        # 本气
    middle_stem = month_hidden.get("middle", "")    # 中气
    residual_stem = month_hidden.get("residual", "")  # 余气

    four_stems = [fact.pillar_stem(p) for p in ("YEAR", "MONTH", "DAY", "HOUR")]

    # 透干检查
    main_transparent = main_stem in four_stems if main_stem else False
    middle_transparent = middle_stem in four_stems if middle_stem else False
    residual_transparent = residual_stem in four_stems if residual_stem else False

    # 取格神
    ge_shen_tg = ""  # 格神十神 (中文)
    ge_shen_stem = ""  # 格神天干 (拼音)
    select_reason = ""

    if main_transparent:
        # PATTERN-SELECT-001: 本气透干
        ge_shen_stem = main_stem
        ge_shen_tg = _stem_to_ten_god(day_master, main_stem)
        select_reason = f"本气{main_stem}透干 → 格神={ge_shen_tg}"
    elif middle_transparent:
        # PATTERN-SELECT-002: 中气透干
        ge_shen_stem = middle_stem
        ge_shen_tg = _stem_to_ten_god(day_master, middle_stem)
        select_reason = f"中气{middle_stem}透干 → 格神={ge_shen_tg}"
    elif residual_transparent:
        # PATTERN-SELECT-002 (余气)
        ge_shen_stem = residual_stem
        ge_shen_tg = _stem_to_ten_god(day_master, residual_stem)
        select_reason = f"余气{residual_stem}透干 → 格神={ge_shen_tg}"
    else:
        # PATTERN-SELECT-003: 本气不透 → 以本气十神为格神
        ge_shen_tg = month_hidden.get("main_tg", "")
        ge_shen_stem = main_stem
        select_reason = f"本气{main_stem}不透 → 格神={ge_shen_tg}(月令本气)"

    # ── 2. 特殊格局检测: 建禄/阳刃/月劫 ────────────────────────
    luwu = LUWU_TABLE.get(day_master, ("", ""))
    lu_branch, blade_branch = luwu

    # PATTERN-SELECT-005: 月令本气 == 比肩 → 建禄格
    if month_branch == lu_branch:
        return _judge_lu_pattern(ctx, derived, day_master, month_branch, ge_shen_tg,
                                  ge_shen_stem, select_reason, is_blade=False)

    # PATTERN-SELECT-006: 月令本气 == 劫财 → 阳刃格
    if month_branch == blade_branch:
        return _judge_blade_pattern(ctx, derived, day_master, month_branch, ge_shen_tg,
                                     ge_shen_stem, select_reason)

    # ── 3. 普通格局判定 ────────────────────────────────────────
    # 3a. 候选判定
    candidate_states = {
        "正官": "OFFICER_PATTERN_CANDIDATE",
        "七杀": "KILL_PATTERN_CANDIDATE",
        "正财": "WEALTH_PATTERN_CANDIDATE",
        "偏财": "WEALTH_PATTERN_CANDIDATE",
        "正印": "RESOURCE_PATTERN_CANDIDATE",
        "偏印": "RESOURCE_PATTERN_CANDIDATE",
        "食神": "FOOD_PATTERN_CANDIDATE",
        "伤官": "INJURY_PATTERN_CANDIDATE",
    }

    if ge_shen_tg in candidate_states:
        cand_state = candidate_states[ge_shen_tg]
        # 3b. 成格/破格判定
        formed_state = _judge_formation(
            ctx, derived, day_master, ge_shen_tg, ge_shen_stem, strength
        )
        if formed_state and formed_state not in ("UNDETERMINED", "NOT_APPLICABLE"):
            return JudgmentBuilder.from_hits(
                "PATTERN", formed_state,
                [Rule("PATTERN", "PATTERN", select_reason)]
            )
        # 返回候选状态
        return JudgmentBuilder.from_hits(
            "PATTERN", cand_state,
            [Rule("PATTERN-SELECT", "PATTERN-SELECT-003", select_reason)]
        )

    # 3c. 无明确格神 → NOT_APPLICABLE
    return JudgmentBuilder.from_hits(
        "PATTERN", "NOT_APPLICABLE",
        [Rule("PATTERN", "PATTERN-NONE", f"无标准格局: {select_reason}")]
    )


def _judge_formation(
    ctx: EngineContext,
    derived: ZiPingDerivedFact,
    day_master: str,
    ge_shen_tg: str,
    ge_shen_stem: str,
    strength: Optional[ZiPingJudgment],
) -> Optional[str]:
    """格局成破判定."""
    tg = _stem_tengods(ctx)
    body_state = strength.state if strength else "UNKNOWN"

    if ge_shen_tg in ("正官", "七杀"):
        return _judge_officer_kill(ctx, derived, ge_shen_tg, tg, body_state)
    elif ge_shen_tg in ("正财", "偏财"):
        return _judge_wealth(ctx, derived, ge_shen_tg, tg, body_state)
    elif ge_shen_tg in ("正印", "偏印"):
        return _judge_resource(ctx, derived, ge_shen_tg, tg, body_state)
    elif ge_shen_tg in ("食神",):
        return _judge_food(ctx, derived, tg, body_state)
    elif ge_shen_tg in ("伤官",):
        return _judge_injury(ctx, derived, tg, body_state)
    return None


def _judge_officer_kill(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    ge_shen_tg: str, tg: Set[str], body_state: str,
) -> Optional[str]:
    """官杀格判定."""
    has_officer = bool(tg & {"正官", "七杀"})
    has_wealth = bool(tg & _HAO)
    has_resource = bool(tg & _SHENG)
    has_injury = bool(tg & {"伤官"})
    has_blade = bool(tg & _TONG)

    # 官杀混杂
    officer_mixed = "正官" in tg and "七杀" in tg

    if ge_shen_tg == "正官":
        # PATTERN-OFFICER-004: 官星被伤官破 OR 官杀混杂无制
        if has_injury and "伤官" in tg:
            return "OFFICER_FAILED"
        if officer_mixed and not has_resource:
            return "OFFICER_FAILED"
        # PATTERN-OFFICER-003: 官星有效 + 财印相随 + 无决定性破坏
        if has_wealth and has_resource and not officer_mixed:
            return "OFFICER_FORMED"
        if has_officer and not has_injury and not officer_mixed:
            return "OFFICER_FORMATION_CANDIDATE"
        return "OFFICER_FAILED"
    else:  # 七杀
        # PATTERN-KILL-002: 身强 + 七杀有效 + 制化有效
        if body_state in ("STRONG", "WANG_BUT_NOT_STRONG", "WANG_OVER") and has_officer:
            if has_wealth or has_injury or has_resource:
                return "KILL_FORMED"
        # PATTERN-KILL-003: 七杀存在 + 制化缺 + 无解救
        if has_officer and not (has_wealth or has_injury or has_resource):
            return "KILL_FAILED"
        return "KILL_PATTERN_CANDIDATE"


def _judge_wealth(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    ge_shen_tg: str, tg: Set[str], body_state: str,
) -> Optional[str]:
    """财格判定."""
    has_officer = bool(tg & _KE)
    has_food = bool(tg & {"食神"})
    has_blade = bool(tg & _TONG)
    has_resource = bool(tg & _SHENG)

    # PATTERN-WEALTH-005: 比劫夺财无制
    if has_blade and not has_officer and not has_food:
        return "WEALTH_FAILED"
    # PATTERN-WEALTH-003: 财逢食生 + 身强 + 比劫不坏财
    if has_food and body_state in ("STRONG", "WANG_BUT_NOT_STRONG", "BALANCED") and not has_blade:
        return "WEALTH_FORMED"
    # PATTERN-WEALTH-002: 财生官 + 官结构有效
    if has_officer and body_state in ("STRONG", "WANG_BUT_NOT_STRONG"):
        return "WEALTH_FORMATION_SUPPORTED"
    return "WEALTH_PATTERN_CANDIDATE"


def _judge_resource(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    ge_shen_tg: str, tg: Set[str], body_state: str,
) -> Optional[str]:
    """印格判定."""
    has_officer = bool(tg & _KE)
    has_wealth = bool(tg & _HAO)
    has_food = bool(tg & _XIE)
    has_blade = bool(tg & _TONG)

    # PATTERN-RESOURCE-006: 财旺坏印
    if has_wealth and has_resource and body_state in ("WEAK", "WEAK_OVER"):
        return "RESOURCE_FAILED"
    # PATTERN-RESOURCE-003: 官印双全
    if has_officer and has_resource:
        return "RESOURCE_FORMED"
    # PATTERN-RESOURCE-002: 印轻逢杀 + 关系有效
    if has_officer and body_state in ("WEAK", "WEAK_OVER"):
        return "RESOURCE_FORMED"
    # PATTERN-RESOURCE-004: 身印两旺 + 食伤可泄
    if body_state in ("STRONG", "WANG_BUT_NOT_STRONG") and has_food:
        return "RESOURCE_FORMED"
    return "RESOURCE_PATTERN_CANDIDATE"


def _judge_food(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    tg: Set[str], body_state: str,
) -> Optional[str]:
    """食神格判定."""
    has_wealth = bool(tg & _HAO)
    has_kill = bool(tg & {"七杀"})
    has枭 = bool(tg & {"偏印"})

    # PATTERN-FOOD-005: 枭神夺食
    if has枭 and "食神" in tg:
        return "FOOD_FAILED"
    # PATTERN-FOOD-002: 食神生财
    if has_wealth:
        return "FOOD_FORMED"
    # PATTERN-FOOD-003: 食神带杀 + 财缺 + 结构许可
    if has_kill and not has_wealth:
        return "FOOD_FORMED"
    return "FOOD_PATTERN_CANDIDATE"


def _judge_injury(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    tg: Set[str], body_state: str,
) -> Optional[str]:
    """伤官格判定."""
    has_wealth = bool(tg & _HAO)
    has_resource = bool(tg & _SHENG)
    has_kill = bool(tg & {"七杀"})
    has_blade = bool(tg & _TONG)

    # PATTERN-INJURY-006: 伤官无印无财可化
    if not has_resource and not has_wealth and not has_kill:
        return "INJURY_FAILED"
    # PATTERN-INJURY-003: 伤官佩印 + 伤官旺 + 印有根
    if has_resource and body_state in ("STRONG", "WANG_BUT_NOT_STRONG"):
        return "INJURY_FORMED"
    # PATTERN-INJURY-002: 伤官生财
    if has_wealth:
        return "INJURY_FORMED"
    # PATTERN-INJURY-004: 伤官旺 + 身弱 + 杀印俱透
    if body_state in ("WEAK", "WEAK_OVER") and has_kill and has_resource:
        return "INJURY_FORMED"
    # PATTERN-INJURY-005: 伤官带杀 + 财缺
    if has_kill and not has_wealth:
        return "INJURY_FORMED"
    return "INJURY_PATTERN_CANDIDATE"


def _judge_blade_pattern(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    day_master: str, month_branch: str,
    ge_shen_tg: str, ge_shen_stem: str, select_reason: str,
) -> ZiPingJudgment:
    """阳刃格判定 (§15.7)."""
    tg = _stem_tengods(ctx)
    has_officer = bool(tg & _KE)
    has_wealth = bool(tg & _HAO)
    has_resource = bool(tg & _SHENG)
    has_injury = bool(tg & {"伤官"})

    # PATTERN-BLADE-003: 阳刃无制 (官杀缺)
    if not has_officer:
        return JudgmentBuilder.from_hits(
            "PATTERN", "BLADE_FAILED",
            [Rule("PATTERN-BLADE-003", "PATTERN", "阳刃无制, 官杀缺")]
        )
    # PATTERN-BLADE-002: 阳刃 + 官杀透 + 财印可用 + 伤官缺
    if has_officer and not has_injury and (has_wealth or has_resource):
        return JudgmentBuilder.from_hits(
            "PATTERN", "BLADE_FORMED",
            [Rule("PATTERN-BLADE-002", "PATTERN", "阳刃驾杀/劫财配印")]
        )
    return JudgmentBuilder.from_hits(
        "PATTERN", "BLADE_CANDIDATE",
        [Rule("PATTERN-BLADE-001", "PATTERN", select_reason)]
    )


def _judge_lu_pattern(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    day_master: str, month_branch: str,
    ge_shen_tg: str, ge_shen_stem: str, select_reason: str,
    is_blade: bool = False,
) -> ZiPingJudgment:
    """建禄/月劫格判定 (§15.8)."""
    tg = _stem_tengods(ctx)
    has_officer = bool(tg & _KE)
    has_wealth = bool(tg & _HAO)
    has_kill = bool(tg & {"七杀"})
    has_food = bool(tg & {"食神"})

    # PATTERN-LU-006: 比劫无制无化
    if not has_officer and not has_wealth and not has_kill and not has_food:
        return JudgmentBuilder.from_hits(
            "PATTERN", "LU_FAILED",
            [Rule("PATTERN-LU-006", "PATTERN", "比劫无制无化")]
        )
    # PATTERN-LU-003: 透官 + 财印有效
    if has_officer:
        return JudgmentBuilder.from_hits(
            "PATTERN", "LU_FORMED",
            [Rule("PATTERN-LU-003", "PATTERN", "建禄透官, 财印相随")]
        )
    # PATTERN-LU-004: 透财 + 食伤有效
    if has_wealth and has_food:
        return JudgmentBuilder.from_hits(
            "PATTERN", "LU_FORMED",
            [Rule("PATTERN-LU-004", "PATTERN", "建禄透财, 食伤生财")]
        )
    # PATTERN-LU-005: 透杀 + 制伏有效
    if has_kill:
        return JudgmentBuilder.from_hits(
            "PATTERN", "LU_FORMED",
            [Rule("PATTERN-LU-005", "PATTERN", "建禄透杀, 制伏得宜")]
        )
    return JudgmentBuilder.from_hits(
        "PATTERN", "LU_PATTERN_CANDIDATE" if not is_blade else "ROBBERY_MONTH_CANDIDATE",
        [Rule("PATTERN-LU-001" if not is_blade else "PATTERN-LU-002", "PATTERN", select_reason)]
    )


def _stem_to_ten_god(day_master: str, stem: str) -> str:
    """天干 → 十神 (基于日主)."""
    # 日主五行
    dm_5x = STEM_ELEMENT.get(day_master, "")
    s_5x = STEM_ELEMENT.get(stem, "")

    if dm_5x == s_5x:
        return "比肩" if day_master == stem else "劫财"

    # 我生 (食伤)
    if s_5x in GENERATES.get(dm_5x, []):
        return "食神" if (STEM_ELEMENT.get(day_master, "") == "YANG" and
                          STEM_ELEMENT.get(stem, "") == "YANG") or \
                       (STEM_ELEMENT.get(day_master, "") == "YIN" and
                        STEM_ELEMENT.get(stem, "") == "YIN") else "伤官"

    # 我克 (财)
    if dm_5x in GENERATES.get(s_5x, []):
        return "正财" if (STEM_ELEMENT.get(day_master, "") == "YANG" and
                          STEM_ELEMENT.get(stem, "") == "YIN") or \
                       (STEM_ELEMENT.get(day_master, "") == "YIN" and
                        STEM_ELEMENT.get(stem, "") == "YANG") else "偏财"

    # 克我 (官杀)
    if s_5x in CONTROLS.get(dm_5x, []):
        return "正官" if (STEM_ELEMENT.get(day_master, "") == "YANG" and
                          STEM_ELEMENT.get(stem, "") == "YIN") or \
                       (STEM_ELEMENT.get(day_master, "") == "YIN" and
                        STEM_ELEMENT.get(stem, "") == "YANG") else "七杀"

    # 生我 (印)
    if dm_5x in GENERATES.get(s_5x, []):
        return "正印" if (STEM_ELEMENT.get(day_master, "") == "YANG" and
                          STEM_ELEMENT.get(stem, "") == "YIN") or \
                       (STEM_ELEMENT.get(day_master, "") == "YIN" and
                        STEM_ELEMENT.get(stem, "") == "YANG") else "偏印"

    return "UNKNOWN"
