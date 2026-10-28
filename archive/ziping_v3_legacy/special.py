# -*- coding: utf-8 -*-
"""ZIPING V3.1 特殊格检测 (SPECIAL) — §22/§63.

铁律: SPECIAL_GATE FIRST，特殊格成立时跳过普通强弱解释 (ARCH-016).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .engine import EngineContext, JudgmentBuilder, Rule
from .judgment_ext import _stem_tengods, _SHENG, _TONG, _XIE, _HAO, _KE
from .types import FrozenBaziFact, ZiPingDerivedFact, ZiPingJudgment

# 特殊格检测规则 (滴天髓 + 子平真诠)
# 从格: 日主无根、食伤官杀财旺极 → 从xxx
# 专旺格: 日主得令+党众极旺 → 从强 (炎上/曲直/稼穑/从革/润下)

# 建禄/阳刃地支
LUWU = {
    "BING": ("SI", "WU"), "DING": ("WU", "SI"),
    "WU": ("SI", "WU"), "JI": ("WU", "SI"),
    "GENG": ("SHEN", "YOU"), "XIN": ("YOU", "SHEN"),
    "REN": ("HAI", "ZI"), "GUI": ("ZI", "HAI"),
    "JIA": ("YIN", "MAO"), "YI": ("MAO", "YIN"),
}


def judge_special(
    ctx: EngineContext,
    derived: ZiPingDerivedFact,
    strength: Optional[ZiPingJudgment] = None,
    pattern: Optional[ZiPingJudgment] = None,
) -> ZiPingJudgment:
    """特殊格检测 (SPECIAL_GATE).

    检测顺序:
    1. 专旺格 (炎上/曲直/稼穑/从革/润下) — 日主极旺，无克泄耗
    2. 从格 (从旺/从弱/从财/从官/从儿) — 日主极弱，无帮扶

    如果特殊格成立:
    - 覆盖普通强弱判定 (strength → NOT_APPLICABLE)
    - 格局直接用特殊格名称

    Returns:
        SPECIAL judgment with state ∈ {"NONE", "YANSHANG", "QUZHI", ...}
    """
    fact = ctx.fact
    day_master = fact.day_master
    month_branch = fact.month_branch
    four_stems = [fact.pillar_stem(p) for p in ("YEAR", "MONTH", "DAY", "HOUR")]
    four_branches = [fact.pillar_branch(p) for p in ("YEAR", "MONTH", "DAY", "HOUR")]

    tg = _stem_tengods(ctx)

    # ── 1. 专旺格检测 ──────────────────────────────────────────
    # 条件: 日主得令 + 党众极旺 + 无克泄耗 (或克泄耗极弱)
    special_type = _detect_special_wang(ctx, derived, day_master, month_branch,
                                         four_stems, four_branches, tg)

    if special_type and special_type not in ("NONE", "NOT_SPECIAL"):
        return JudgmentBuilder.from_hits(
            "SPECIAL", special_type,
            [Rule("SPECIAL", f"SPECIAL-{special_type}", f"专旺格: {special_type}")]
        )

    # ── 2. 从格检测 ───────────────────────────────────────────
    # 条件: 日主无根 + 克泄耗极旺 + 无帮扶
    cong_type = _detect_cong(ctx, derived, day_master, month_branch,
                              four_stems, four_branches, tg)

    if cong_type and cong_type not in ("NONE", "NOT_CONG"):
        return JudgmentBuilder.from_hits(
            "SPECIAL", cong_type,
            [Rule("SPECIAL", f"SPECIAL-{cong_type}", f"从格: {cong_type}")]
        )

    # ── 3. 无特殊格 ────────────────────────────────────────────
    return JudgmentBuilder.from_hits(
        "SPECIAL", "NONE",
        [Rule("SPECIAL", "SPECIAL-NONE", "无特殊格局，按普通格处理")]
    )


def _detect_special_wang(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    day_master: str, month_branch: str,
    four_stems: List[str], four_branches: List[str],
    tg: Set[str],
) -> str:
    """专旺格检测: 炎上/曲直/稼穑/从革/润下."""
    dm_5x = _stem_element(day_master)
    mb_5x = _branch_element(month_branch)

    # 同五行地支数
    same_count = sum(1 for b in four_branches if _branch_element(b) == dm_5x)
    # 同五行天干数 (不含日主)
    same_stem_count = sum(1 for s in four_stems if _stem_element(s) == dm_5x and s != day_master)

    # 日主极旺条件: 月令同五行 + 地支3支以上同五行 + 天干比劫透
    if mb_5x == dm_5x and same_count >= 3 and same_stem_count >= 1:
        # 检查是否有克泄耗 (官杀/食伤/财)
        opposition = tg & (_KE | _XIE | _HAO)
        if not opposition:
            # 专旺格成立
            return _special_wang_name(dm_5x)

    # 特殊检查: 三会局/三合局
    sanhui = _check_sanhui(four_branches, dm_5x)
    sanhe = _check_sanhe(four_branches, dm_5x)
    if sanhui or sanhe:
        return _special_wang_name(dm_5x)

    return "NONE"


def _detect_cong(
    ctx: EngineContext, derived: ZiPingDerivedFact,
    day_master: str, month_branch: str,
    four_stems: List[str], four_branches: List[str],
    tg: Set[str],
) -> str:
    """从格检测: 从旺/从弱/从财/从官/从儿."""
    dm_5x = _stem_element(day_master)
    mb_5x = _branch_element(month_branch)

    # 日主无根检查 — hidden_stems的key是位置名'year'/'month'/'day'/'hour'
    # 注意: 日柱天干本身就是日主, 必须计入根
    has_root = day_master in four_stems  # 日主透干即为有根
    if not has_root:
        positions = ["year", "month", "day", "hour"]
        for pos in positions:
            b_hidden = ctx.fact.hidden_stems.get(pos, {})
            for hs in b_hidden.get("all", []):
                if _stem_element(hs) == dm_5x:
                    has_root = True
                    break
            if has_root:
                break

    # 从弱检测 (从财/从官/从儿)
    if not has_root:
        support = tg & (_SHENG | _TONG)
        opposition = tg & (_KE | _XIE | _HAO)

        if not support and opposition:
            # 从格成立
            if _KE & opposition:
                return "CONG_GUAN"  # 从官/杀格
            if _HAO & opposition:
                return "CONG_CAI"   # 从财格
            if _XIE & opposition:
                return "CONG_ER"    # 从儿格

    # 从旺检测 (日主极旺但仍有克泄耗，却无力制)
    if _stem_element(month_branch) == dm_5x:
        support = tg & (_SHENG | _TONG)
        opposition = tg & (_KE | _XIE | _HAO)
        if support and not opposition:
            return "CONG_WANG"  # 从旺格

    return "NONE"


def _special_wang_name(element: str) -> str:
    """专旺格名称映射."""
    names = {
        "FIRE": "YANSHANG",   # 炎上格
        "WOOD": "QUZHI",      # 曲直格
        "EARTH": "JIASE",     # 稼穑格
        "METAL": "CONGGE",    # 从革格
        "WATER": "RUNXIA",    # 润下格
    }
    return names.get(element, "NONE")


def _stem_element(stem: str) -> str:
    """天干 → 五行."""
    from .constants import STEM_ELEMENT
    return STEM_ELEMENT.get(stem, "")


def _branch_element(branch: str) -> str:
    """地支 → 五行."""
    from .constants import BRANCH_ELEMENT
    return BRANCH_ELEMENT.get(branch, "")


def _check_sanhui(branches: List[str], dm_5x: str) -> bool:
    """检查三会局."""
    sanhui_map = {
        "WOOD": ["YIN", "MAO", "CHEN"],   # 寅卯辰东方木
        "FIRE": ["SI", "WU", "WEI"],       # 巳午未南方火
        "EARTH": ["SHEN", "YOU", "XU"],    # 申酉戌西方金 (实际是金局，但稼穑用土)
        "METAL": ["SHEN", "YOU", "XU"],    # 申酉戌西方金
        "WATER": ["HAI", "ZI", "CHOU"],    # 亥子丑北方水
    }
    target = sanhui_map.get(dm_5x, [])
    return all(b in target for b in branches)


def _check_sanhe(branches: List[str], dm_5x: str) -> bool:
    """检查三合局."""
    sanhe_map = {
        "WOOD": [["HAI", "MAO", "WEI"]],           # 亥卯未木局
        "FIRE": [["IN", "WU", "XU"]],              # 寅午戌火局
        "EARTH": [["SHEN", "ZI", "CHEN"], ["SI", "YOU", "CHOU"]],  # 申子辰水 / 巳酉丑金
        "METAL": [["SHEN", "ZI", "CHEN"]],          # 申子辰水局 (实际是水，但稼穑用土)
        "WATER": [["HEN", "MAO", "WEI"]],           # 亥卯未木局
    }
    for combo in sanhe_map.get(dm_5x, []):
        if all(b in branches for b in combo):
            return True
    return False
