# -*- coding: utf-8 -*-
"""ZIPING V3.1 判断层 (辨): 月令得令 + 十二长生 + 有效根 + 党众结构 + 身强弱.

判据链 (Deterministic, 全结构判定, 无数字阈值 §2/§50):
    LING (§4)   月令关系 seasonal_relation + 得令/失令
    GROWTH (§5/§72)  十二长生结构态 (帝旺/临官/长生/墓/余气/绝胎), 只结构不推导身强
    EFFECTIVE_ROOT (§52 REV-ROOT)  根有效条件树 (重/轻根 → 受损/合绊/冲 → 可用)
    PARTY (§53 REV-PARTY)          帮身/对立 结构清单 (集合, 不计数)
    STRENGTH (§14)                六态最终裁决 (强/得令不旺/失令不弱/弱/中和/无法判断)

原则: 每条判断产 ZiPingJudgment (强制 matched_rule_ids + evidence + method_scope +
      UNDETERMINED 分因 §77)。事实缺失 → fail-closed, 绝不臆测 (§0.3/§72)。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .constants import BRANCH_ELEMENT, STEM_ELEMENT, STORE_BRANCHES
from .engine import EngineContext, JudgmentBuilder, UndeterminedReason, ZiPingJudgment
from .types import FrozenBaziFact, MethodScope, ZiPingDerivedFact

# 结构态 → evidence id 映射 (V3.1 §4/§5)
_LING_EV = {
    "SAME": "E-ZQ-LING-001", "SUPPORTIVE": "E-ZQ-LING-002",
    "DRAINING": "E-ZQ-LING-003", "CONSUMING": "E-ZQ-LING-004",
    "OPPOSING": "E-ZQ-LING-005",
}
_DE_LING_REL = {"SAME", "SUPPORTIVE"}
_SHI_LING_REL = {"DRAINING", "CONSUMING", "OPPOSING"}
_ZHONGWANG = {"帝旺", "临官", "长生"}


# ---------------------------------------------------------------------------
# §4 月令 / 得令
# ---------------------------------------------------------------------------

def judge_ling(ctx: EngineContext, derived: ZiPingDerivedFact) -> ZiPingJudgment:
    """月令关系 + 得令/失令 (LING-010~013)."""
    month_el = ctx.element_of_branch(ctx.fact.month_branch)
    day_el = ctx.element_of_stem(ctx.fact.day_master)
    if not month_el or not day_el:
        return JudgmentBuilder.undetermined("LING", UndeterminedReason.FACT_MISSING,
                                             "月支或日主五行缺失")

    rel = ctx.relation(day_el, month_el)  # 日主视角: 日主对月支的生克
    # relation(a,b): a=day_el. 得令 = 月支 对 日主 的生克:
    #   月支生日主 (SUPPORTIVE=月支生日主): 得令
    #   月支同日主 (SAME): 得令
    #   日主生月支 (DRAINING=日主泄于月支): 失令
    #   日主克月支 (CONSUMING=日主耗于月支): 失令
    #   月支克日主 (OPPOSING=月支克日主): 失令
    transitional = bool(ctx.fact.solar_term_crossing)

    if transitional:
        # LING-012: 节气交界 → 不判得失令
        return JudgmentBuilder.from_hits(
            "LING", "TRANSITIONAL",
            _synth_rule("LING-012", "E-ZQ-LING-012"),
        )

    if month_el in STORE_BRANCHES and not ctx.stem_in_pillars(ctx.fact.day_master):
        # LING-013: 墓库月 藏干多变 → 转 ROOT 段, 此处仅标记
        pass

    if rel in _DE_LING_REL:
        return JudgmentBuilder.from_hits(
            "LING", "DE_LING",
            _synth_rule("LING-010", _LING_EV.get(rel, "E-ZQ-LING-010")),
            invalidated_by=["LING-012"] if not transitional else None,
        )
    if rel in _SHI_LING_REL:
        return JudgmentBuilder.from_hits(
            "LING", "SHI_LING",
            _synth_rule("LING-011", _LING_EV.get(rel, "E-ZQ-LING-011")),
        )
    # 不应到达 (relation 已穷尽 5 态)
    return JudgmentBuilder.undetermined("LING", UndeterminedReason.RULE_MISSING,
                                        f"seasonal_relation={rel} 未定义得失令")


def _synth_rule(rule_id: str, evidence: str):
    """轻量 Rule 占位 (判断层内联规则, 仍携带 rule_id + evidence, ARCH-009/013)."""
    from .engine import Rule
    r = Rule(rule_id=rule_id, domain="LING", result_state="")
    r.evidence_refs = [evidence]
    r.method_scope = [MethodScope.ZIPING_ZHENQUAN]
    return r


# ---------------------------------------------------------------------------
# §5/§72 十二长生 结构态
# ---------------------------------------------------------------------------

_GROWTH_STATE = {
    "帝旺": "IMPERIAL", "临官": "LU", "长生": "ROOTING",
    # 渊海 YHZP_0282: 帝旺/临官/长生/冠带/养/库 同列「吉」(有气)
    # 冠带/养 不归 余气, 归 ROOTING (有根)
    "冠带": "ROOTING", "养": "ROOTING",
    "墓": "STORE",
    # 衰/病 归 余气 (偏弱)
    "衰": "RESIDUAL", "病": "RESIDUAL",
    # 绝/胎/死 → EXTINCT (死/绝无渊海支撑, 胎 UNVERIFIED 但保留)
    "绝": "EXTINCT", "胎": "EXTINCT", "死": "EXTINCT",
}


def judge_growth(ctx: EngineContext, derived: ZiPingDerivedFact) -> ZiPingJudgment:
    """十二长生结构态 (GROWTH-001~006, §72 只结构事实, 禁止帝旺→身强)."""
    growth = ctx.fact.twelve_growth or {}
    day_growth = growth.get("DAY")
    if not day_growth:
        return JudgmentBuilder.undetermined("GROWTH", UndeterminedReason.FACT_MISSING,
                                             "day_master twelve_growth 缺失")
    state = _GROWTH_STATE.get(day_growth)
    if state is None:
        # 未知长生位 → 不臆测
        return JudgmentBuilder.undetermined("GROWTH", UndeterminedReason.RULE_MISSING,
                                             f"twelve_growth={day_growth} 未在 GROWTH 结构态表")
    # 日主长生位 结构态 (结构事实, 非身强推导)
    ev = {
        "IMPERIAL": "E-YH-GROWTH-001", "LU": "E-YH-GROWTH-002", "ROOTING": "E-YH-GROWTH-003",
        "STORE": "E-YH-GROWTH-004", "RESIDUAL": "E-YH-GROWTH-005", "EXTINCT": "E-YH-GROWTH-006",
    }[state]
    rid = {
        "IMPERIAL": "GROWTH-001", "LU": "GROWTH-002", "ROOTING": "GROWTH-003",
        "STORE": "GROWTH-004", "RESIDUAL": "GROWTH-005", "EXTINCT": "GROWTH-006",
    }[state]
    return JudgmentBuilder.from_hits("GROWTH", state, _synth_rule(rid, ev))


# ---------------------------------------------------------------------------
# §52 有效根 条件树
# ---------------------------------------------------------------------------

def derive_effective_root(ctx: EngineContext, derived: ZiPingDerivedFact) -> Dict[str, Any]:
    """EffectiveRootResolver 条件树 (§52 REV-ROOT). 无根分值.

    ROOT_PRESENT → ROOT_KIND(重/轻) → ROOT_IS_DAMAGED/COMBINED/CLASHED
             → ROOT_IS_AVAILABLE → EFFECTIVE_ROOT(TRUE/CONDITIONAL/FALSE)
    """
    day = ctx.fact.day_master
    day_el = ctx.element_of_stem(day)
    root_state = derived.states.get("root_strength", {})
    roots = root_state.get("roots", [])
    growth_roots = root_state.get("growth_roots", [])

    if not roots and not growth_roots:
        return {"ROOT_PRESENT": False, "EFFECTIVE_ROOT": "FALSE",
                "state": "DETERMINED"}

    # ROOT_KIND: 长生/禄/刃=重; 墓库/余气=轻
    has_heavy = any(r["type"] == "TONG_GAN" for r in roots) or \
                any(g["growth"] in _ZHONGWANG for g in growth_roots)
    has_light = any(r.get("grade") in ("中气", "余气") for r in roots) or \
                any(g["growth"] == "墓" for g in growth_roots)
    root_kind = "HEAVY" if has_heavy else ("LIGHT" if has_light else "MIXED")

    # 受损/合绊/冲破: 消费 Bazi 冻结关系 map (ARCH 合规, 不重算)
    damaged = _root_damaged(ctx, roots, growth_roots)
    combined = _root_combined(ctx, roots, growth_roots)

    # ROOT_IS_AVAILABLE: 重根未被损 → 可用; 轻根被冲刑无救应 → 不可用 (REV-ROOT-003)
    if not damaged and not combined:
        available = "TRUE"
    elif has_heavy and not damaged:
        available = "TRUE"
    elif damaged or combined:
        available = "FALSE" if root_kind in ("LIGHT",) else "CONDITIONAL"
    else:
        available = "CONDITIONAL"

    effective = {
        "TRUE": "TRUE", "CONDITIONAL": "CONDITIONAL", "FALSE": "FALSE"
    }[available]

    return {
        "ROOT_PRESENT": True,
        "ROOT_KIND": root_kind,
        "ROOT_IS_DAMAGED": damaged,
        "ROOT_IS_COMBINED": combined,
        "ROOT_IS_AVAILABLE": available,
        "EFFECTIVE_ROOT": effective,
        "state": "DETERMINED",
    }


def _root_positions(ctx: EngineContext, roots: List[Dict], growth: List[Dict]) -> Set[str]:
    pos = {r["position"] for r in roots} | {g["position"] for g in growth}
    return pos


def _root_damaged(ctx: EngineContext, roots: List[Dict], growth: List[Dict]) -> bool:
    """根所在支 是否 被冲/刑 (Bazi 冻结 relation map, 只读取)."""
    rel = ctx.fact.branch_relations or {}
    pos = _root_positions(ctx, roots, growth)
    branch_at = {ctx.fact.pillar_branch(p) for p in pos if ctx.fact.pillar_branch(p)}
    # 冲: 键为 "A-B" 拼音对
    for pair in rel.get("clash", []):
        a, b = _pair_sides(pair)
        if a in branch_at or b in branch_at:
            return True
    # 刑
    for pair in rel.get("sanxing", []):
        a, b = _pair_sides(pair)
        if a in branch_at or b in branch_at:
            return True
    return False


def _root_combined(ctx: EngineContext, roots: List[Dict], growth: List[Dict]) -> bool:
    """根所在支 是否 被合绊/合化 (Bazi 冻结 合 map)."""
    rel = ctx.fact.branch_relations or {}
    pos = _root_positions(ctx, roots, growth)
    branch_at = {ctx.fact.pillar_branch(p) for p in pos if ctx.fact.pillar_branch(p)}
    for rel_kind in ("he", "sanhe"):
        for pair in rel.get(rel_kind, []):
            a, b = _pair_sides(pair)
            if a in branch_at or b in branch_at:
                return True
    return False


def _pair_sides(pair: Any):
    """支关系键归一: 'A-B' 字符串 或 [a,b] 列表."""
    if isinstance(pair, str):
        a, _, b = pair.partition("-")
        return a, b
    if isinstance(pair, (list, tuple)) and len(pair) >= 2:
        return pair[0], pair[1]
    return str(pair), ""


# ---------------------------------------------------------------------------
# §53 党众结构 清单
# ---------------------------------------------------------------------------

def derive_party_structure(ctx: EngineContext, derived: ZiPingDerivedFact,
                          de_ling: bool) -> Dict[str, Any]:
    """帮身/对立 结构清单 (集合, 不计数, REV-PARTY-001~006)."""
    party = derived.states.get("party", {})
    support: Set[str] = set()
    opposition: Set[str] = set()

    for item in party.get("aligned", []):
        s = item.get("stem", "")
        el = ctx.element_of_stem(s)
        if not el:
            continue
        day_el = ctx.element_of_stem(ctx.fact.day_master)
        # 同类 → 比劫; 生我 → 印星
        if el == day_el:
            support.add("比劫")
        elif _generates(el, day_el):
            support.add("印星")
    for item in party.get("opposed", []):
        s = item.get("stem", "")
        el = ctx.element_of_stem(s)
        if not el:
            continue
        day_el = ctx.element_of_stem(ctx.fact.day_master)
        if _generates(day_el, el):
            opposition.add("食伤")          # 我生 → 泄
        elif _controls(day_el, el):
            opposition.add("财耗")          # 我克 → 耗
        elif _controls(el, day_el):
            opposition.add("官杀")          # 克我

    day_branch_root = _day_branch_root(ctx, derived)
    if day_branch_root:
        support.add("日支根")
    if de_ling:
        support.add("月令")

    return {
        "SUPPORT_STRUCTURE": sorted(support),
        "OPPOSITION_STRUCTURE": sorted(opposition),
        "day_branch_root": day_branch_root,
        "state": "DETERMINED",
    }


def _day_branch_root(ctx: EngineContext, derived: ZiPingDerivedFact) -> bool:
    day_el = ctx.element_of_stem(ctx.fact.day_master)
    h = (ctx.fact.hidden_stems or {}).get("DAY")
    if not h or not day_el:
        return False
    return any(ctx.element_of_stem(s) == day_el for s in h.get("all", []) if s)


def _generates(a: str, b: str) -> bool:
    """a 生 b (确定性查表)."""
    from .constants import GENERATES
    return GENERATES.get(a) == b


def _controls(a: str, b: str) -> bool:
    """a 克 b (确定性查表)."""
    from .constants import CONTROLS
    return CONTROLS.get(a) == b


# ---------------------------------------------------------------------------
# §14 身强弱 六态 最终裁决
# ---------------------------------------------------------------------------

def judge_strength(
    ctx: EngineContext,
    derived: ZiPingDerivedFact,
    ling: ZiPingJudgment,
    eff_root: Dict[str, Any],
    party: Dict[str, Any],
    special_valid: bool = False,
) -> ZiPingJudgment:
    """身强弱六态 (§14 STRENGTH-001~015, 无数字阈值, 特殊格优先)."""
    if special_valid:
        # STRENGTH-001: 特殊格成立 → 普通身强弱不适用
        return JudgmentBuilder.from_hits(
            "STRENGTH", "NOT_APPLICABLE",
            _synth_rule("STRENGTH-001", "E-YH-STRENGTH-001"),
        )

    shi_ling = ling.state == "SHI_LING"
    eff_root_exists = eff_root.get("EFFECTIVE_ROOT") == "TRUE"
    root_conditional = eff_root.get("EFFECTIVE_ROOT") == "CONDITIONAL"
    support = set(party.get("SUPPORT_STRUCTURE", []))
    opposition = set(party.get("OPPOSITION_STRUCTURE", []))
    # 结构谓词 (存在性/缺失性, 非数量阈值 — §53/§50 禁止 support_count):
    #   月令支持    = 月令 ∈ SUPPORT_STRUCTURE (与 de_ling 同义, 作交叉校验)
    #   有效支持存在 = 印星 或 比劫 或 日支根 ∈ SUPPORT (任一结构成立即可)
    #   对立结构存在 = 食伤/财耗/官杀 任一 ∈ OPPOSITION
    _HELP = {"印星", "比劫", "日支根"}
    _OPPOSE = {"食伤", "财耗", "官杀"}
    month_support = "月令" in support
    help_exists = bool(support & _HELP)
    opposing_exists = bool(opposition & _OPPOSE)
    opposing_absent = not opposing_exists
    support_absent = not help_exists

    # STRENGTH-010 身强: 得令 + 有效根 + 有效支持 + 对立缺失
    if month_support and eff_root_exists and help_exists and opposing_absent:
        return JudgmentBuilder.from_hits(
            "STRENGTH", "STRONG",
            _synth_rule("STRENGTH-010", "E-DT-STRENGTH-010"),
        )
    # STRENGTH-011 得令不旺: 得令 + 对立存在 (不论根是否有效)
    # 滴天髓: 「犹如春木虽强, 金太重而木亦危」— 得令但对抗强即不旺
    if month_support and opposing_exists:
        return JudgmentBuilder.from_hits(
            "STRENGTH", "WANG_BUT_NOT_STRONG",
            _synth_rule("STRENGTH-011", "E-DT-STRENGTH-011"),
        )
    # STRENGTH-012 失令不弱: 失令 + 根存在(含条件) + 支持存在 + 对立缺失
    if shi_ling and (eff_root_exists or root_conditional) and help_exists and opposing_absent:
        return JudgmentBuilder.from_hits(
            "STRENGTH", "SHUAI_BUT_NOT_WEAK",
            _synth_rule("STRENGTH-012", "E-DT-STRENGTH-012"),
        )
    # STRENGTH-014 中和: 帮身与对立并存 + 根可用 (不限月令方向)
    # 子平真诠: 「然其理之大纲, 亦在有情、有力无力之间而已」
    if help_exists and opposing_exists and (eff_root_exists or root_conditional):
        return JudgmentBuilder.from_hits(
            "STRENGTH", "BALANCED",
            _synth_rule("STRENGTH-014", "E-DT-STRENGTH-014"),
        )
    # STRENGTH-013 身弱: 失令 + 根缺失/失效 + 支持缺失 (不限对立是否存在)
    # 子平真诠: 「秋木虽弱, 木根深而木亦强」— 弱不依赖对立
    if shi_ling and not eff_root_exists and support_absent:
        return JudgmentBuilder.from_hits(
            "STRENGTH", "WEAK",
            _synth_rule("STRENGTH-013", "E-DT-STRENGTH-013"),
        )
    # STRENGTH-015 无法判断: 上述结构谓词均未消解
    return JudgmentBuilder.undetermined(
        "STRENGTH", UndeterminedReason.DEPENDENCY_UNRESOLVED,
        "STRENGTH 六态规则均未命中 (结构歧义未消解)")


def run_strength_chain(
    ctx: EngineContext,
    derived: ZiPingDerivedFact,
    special_valid: bool = False,
) -> Dict[str, ZiPingJudgment]:
    """月令→有效根→党众→身强弱 判据链 一次跑完, 返回各域判断."""
    ling = judge_ling(ctx, derived)
    eff_root = derive_effective_root(ctx, derived)
    party = derive_party_structure(ctx, derived, de_ling=(ling.state == "DE_LING"))
    strength = judge_strength(ctx, derived, ling, eff_root, party, special_valid)
    growth = judge_growth(ctx, derived)
    return {"LING": ling, "GROWTH": growth, "STRENGTH": strength}
