# -*- coding: utf-8 -*-
"""ZIPING V3.1 确定性派生事实层 (P1 段, "算" 层 / Deterministic First).

从 FrozenBaziFact 派生结构性 (非数值) 派生事实。原则:
  - 只做结构判定 (存在/缺失/枚举/分级), 不做计数阈值与加减分 (§2 FORBIDDEN).
  - 根气/党众/透干 仅依赖 FrozenBaziFact (已验证), 零外部表 → 可独立测试.
  - 结果写入 ZiPingDerivedFact.states (按域分键), 供 裁决链/判断层 消费.
  - 依赖月令司令/调候 的域: 表数据可插拔, 缺格 → fail-closed, 绝不补造.

对齐真实 API:
  FrozenBaziFact.pillar_stem(pos)/pillar_branch(pos)  四柱取值
  constants: STEM_ELEMENT / GENERATES / CONTROLS / BRANCH_HIDDEN
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import STEM_ELEMENT, GENERATES, CONTROLS
from .types import FrozenBaziFact, ZiPingDerivedFact


def _stem_element(stem: str) -> str:
    return STEM_ELEMENT.get(stem, "")


def _classify_party(day_element: str, stem: str) -> Optional[str]:
    """干 → 帮身(ALIGNED)/克泄耗(OPPOSED) 结构分类 (确定性, 无计数).

      帮身 ALIGNED:  同我 (比劫) + 生我 (印)
      克泄耗 OPPOSED: 我生 (食伤泄) + 我克 (财耗) + 克我 (官杀)
    未知干/日主五行 → None (该干不参与党众).
    """
    e = _stem_element(stem)
    if not e or not day_element:
        return None
    born_by = [s for s, t in GENERATES.items() if t == day_element]      # 生我
    controlling = [s for s, t in CONTROLS.items() if t == day_element]   # 克我
    if e == day_element:
        return "ALIGNED"        # 同我 (比劫)
    if e in born_by:
        return "ALIGNED"        # 生我 (印)
    if e == GENERATES.get(day_element):
        return "OPPOSED"       # 我生 (食伤, 泄)
    if e == CONTROLS.get(day_element):
        return "OPPOSED"       # 我克 (财, 耗)
    if e in controlling:
        return "OPPOSED"       # 克我 (官杀)
    return None


# ---------------------------------------------------------------------------
# 根气 (D 段 ROOT, §6 + §52 REV-ROOT / §72 REV-GROWTH)
# ---------------------------------------------------------------------------

def _root_grade(slot: str) -> str:
    """藏干槽位 → 本/中/余气 分级 (§6.2 D2)."""
    return {"main": "本气", "middle": "中气", "residual": "余气"}.get(slot, "")


def derive_root_strength(fact: FrozenBaziFact) -> Dict[str, Any]:
    """根气: 日主在 四柱天干 / 四柱藏干 / 十二长生 中的根 (结构性).

    三类根 (均非数值, 仅供下游 身强弱 域 枚举消费):
      TONG_GAN  本柱天干 == 日主 (建禄/月劫 最强根)
      CANG_GAN  藏干含 日主同五行 (本/中/余气 分级)
      GROWTH    十二长生 落在 长生/临官/帝旺 (Bazi 冻结口径, 只消费 §72)
    """
    day = fact.day_master
    day_el = _stem_element(day)
    if not day or not day_el:
        return {"day_master": day, "has_root": False, "root_grade": "UNDETERMINED",
                "roots": [], "growth_roots": [],
                "state": "UNDETERMINED", "reason": "FACT_MISSING:day_master"}

    roots: List[Dict[str, str]] = []
    growth_roots: List[Dict[str, str]] = []

    # --- 本柱同干根 (天干 == 日主) ---
    for pos in ("YEAR", "MONTH", "DAY", "HOUR"):
        if fact.pillar_stem(pos) == day:
            roots.append({"position": pos, "type": "TONG_GAN", "stem": day})

    # --- 藏干根 (四支 藏干 含日主同五行, 本/中/余 分级) ---
    for pos, hinfo in (fact.hidden_stems or {}).items():
        if not isinstance(hinfo, dict):
            continue
        for slot in ("main", "middle", "residual"):
            s = hinfo.get(slot, "")
            if s and _stem_element(s) == day_el:
                roots.append({"position": pos, "type": "CANG_GAN",
                              "stem": s, "grade": _root_grade(slot)})

    # --- 长生根 (Bazi 冻结 twelve_growth, 只消费) ---
    growth = fact.twelve_growth or {}
    if growth:
        for pos, g in growth.items():
            if g in ("长生", "临官", "帝旺"):
                growth_roots.append({"position": pos, "growth": g})

    # 根等级 = 取最强可用根 (建禄 TONG_GAN > 本气藏干 > 中气 > 余气 > 长生)
    grade = "UNDETERMINED"
    if any(r["type"] == "TONG_GAN" for r in roots):
        grade = "TONG_GAN"
    elif any(r.get("grade") == "本气" for r in roots):
        grade = "本气"
    elif any(r.get("grade") == "中气" for r in roots):
        grade = "中气"
    elif any(r.get("grade") == "余气" for r in roots):
        grade = "余气"
    elif growth_roots:
        grade = "长生"

    return {
        "day_master": day,
        "has_root": bool(roots or growth_roots),
        "root_grade": grade,
        "roots": roots,
        "growth_roots": growth_roots,
        "growth_available": bool(growth),
        "state": "DETERMINED",
    }


# ---------------------------------------------------------------------------
# 党众 (N 段 PARTY, §13 + §53 REV-PARTY 结构状态)
# ---------------------------------------------------------------------------

def derive_party(fact: FrozenBaziFact) -> Dict[str, Any]:
    """党众: 帮身 vs 克泄耗 的结构分类 (枚举, 非加减分)."""
    day = fact.day_master
    day_el = _stem_element(day)
    if not day_el:
        return {"day_master": day, "aligned": [], "opposed": [],
                "aligned_roots": 0, "opposed_roots": 0,
                "state": "UNDETERMINED", "reason": "FACT_MISSING:day_master"}

    aligned: List[Dict[str, str]] = []
    opposed: List[Dict[str, str]] = []

    # 四柱天干 (透干, 结构层)
    for pos in ("YEAR", "MONTH", "DAY", "HOUR"):
        stem = fact.pillar_stem(pos)
        c = _classify_party(day_el, stem)
        if c == "ALIGNED":
            aligned.append({"position": pos, "stem": stem, "layer": "STEM"})
        elif c == "OPPOSED":
            opposed.append({"position": pos, "stem": stem, "layer": "STEM"})

    # 四柱藏干 (结构层)
    for pos, hinfo in (fact.hidden_stems or {}).items():
        if not isinstance(hinfo, dict):
            continue
        for s in hinfo.get("all", []) or []:
            c = _classify_party(day_el, s)
            if c == "ALIGNED":
                aligned.append({"position": pos, "stem": s, "layer": "HIDDEN"})
            elif c == "OPPOSED":
                opposed.append({"position": pos, "stem": s, "layer": "HIDDEN"})

    # §53 REV-PARTY 结构状态 (枚举, 无"数量阈值"结论):
    #   独党 (仅帮身) / 独党 (仅克泄耗) / 两党皆见 / 党众不明 (缺干)
    if aligned and not opposed:
        party_state = "ALIGNED_ONLY"
    elif opposed and not aligned:
        party_state = "OPPOSED_ONLY"
    elif aligned and opposed:
        party_state = "BOTH"
    else:
        party_state = "UNDETERMINED"

    return {
        "day_master": day,
        "aligned": aligned,
        "opposed": opposed,
        "aligned_roots": len(aligned),
        "opposed_roots": len(opposed),
        "party_state": party_state,
        "state": "DETERMINED",
    }


# ---------------------------------------------------------------------------
# 透干 (E 段 STEM, §7) — 依赖月令司令 (可插拔)
# ---------------------------------------------------------------------------

def derive_tong_stems(fact: FrozenBaziFact,
                      commanded_stem: Optional[str] = None) -> Dict[str, Any]:
    """透干: 月令司令干 是否 透出 四柱天干.

    commanded_stem 缺 → fail-closed (UNDETERMINED / FACT_MISSING:month_command),
    绝不臆测司令干.
    """
    if not commanded_stem:
        return {"commanded_stem": commanded_stem, "is_tong": False,
                "state": "UNDETERMINED", "reason": "FACT_MISSING:month_command"}
    tong_set = {fact.pillar_stem(p) for p in ("YEAR", "MONTH", "DAY", "HOUR")} - {""}
    return {
        "commanded_stem": commanded_stem,
        "is_tong": commanded_stem in tong_set,
        "tong_stems": sorted(tong_set),
        "state": "DETERMINED",
    }


def build_derived_facts(
    fact: FrozenBaziFact,
    month_command: Optional[Dict[str, Any]] = None,
) -> ZiPingDerivedFact:
    """FrozenBaziFact → ZiPingDerivedFact (P1 派生层入口).

    结果按域写入 states 键: root_strength / party / tong_stems.
    month_command 缺 → 透干/调候 fail-closed, 根气/党众 不受影响.
    """
    root = derive_root_strength(fact)
    party = derive_party(fact)
    tong = derive_tong_stems(fact, (month_command or {}).get("commanded_stem"))

    derived = ZiPingDerivedFact(states={
        "day_master": fact.day_master,
        "month_branch": fact.month_branch,
        "root_strength": root,
        "party": party,
        "tong_stems": tong,
    })
    return derived
