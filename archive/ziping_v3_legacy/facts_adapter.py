# -*- coding: utf-8 -*-
"""ZIPING V3.1 事实适配层 (P0 段, §3 FACT / §51 REV-TYPE-001).

职责: BaziChart (Bazi 引擎产出, 排盘层事实) → FrozenBaziFact (子平只读快照).
约束:
  - 只做字段搬运与键归一, 禁止任何重算 (ARCH-003~006).
  - NOT_AUTHORIZED 字段一律不透传 (five_element_balance / spouse_star* /
    officer_mixed / peach_blossom / 各 calc_* AUXILIARY_SIGNAL).
  - 缺失事实 → available_facts 缺项 → 下游 UNDETERMINED(FACT_MISSING), 不补算.

BaziChart 实际键形态 (已核对 1980-06-22 案例):
  - 四柱属性: year_pillar / month_pillar / day_pillar / hour_pillar (Pillar)
  - hidden_stems / branch_ten_gods / twelve_growth / nayin: 键为小写
    year/month/day/hour; 值中 stem/branch 为英文大写 (JIA..GUI / YIN..CHOU)
  - 关系 map (clash/he/harm/sanhe/sanxing/po): dict, 键为 "A-B" 拼音对
  - stem_he_pairs / stem_clash_pairs / branch_po_pairs: list
  - day 柱 stem_ten_god 值为 "DAY_MASTER" (Bazi 口径), 原样保留
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .constants import BRANCH_HIDDEN
from .types import FrozenBaziFact

# Bazi 侧 (英文小写位置键) → 子平位置键 (大写)
_EN_POS = ("year", "month", "day", "hour")
_ZP_POS = ("YEAR", "MONTH", "DAY", "HOUR")
_EN_TO_ZP = dict(zip(_EN_POS, _ZP_POS))


def _pillar_tuple(chart: Any, i: int) -> Tuple[str, str]:
    pillar = getattr(chart, f"{_EN_POS[i]}_pillar", None)
    return (
        getattr(pillar, "heavenly_stem", "") or "",
        getattr(pillar, "earthly_branch", "") or "",
    )


def _ten_god_of(chart: Any, i: int) -> str:
    """透干十神: BAZI 已算 (Pillar.stem_ten_god, P0-1-C), 只读取."""
    pillar = getattr(chart, f"{_EN_POS[i]}_pillar", None)
    return getattr(pillar, "stem_ten_god", "") or ""


def _remap_pos_keyed(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Bazi 小写位置键 dict → 子平大写位置键 dict (值原样保留)."""
    if not raw:
        return {}
    out: Dict[str, Any] = {}
    for k, v in raw.items():
        zk = _EN_TO_ZP.get(str(k).upper(), str(k).upper())
        out[zk] = v
    return out


def build_frozen_fact(
    chart: Any,
    temporal_inputs: Optional[Dict[str, Any]] = None,
    solar_term_crossing: Optional[bool] = None,
) -> "Tuple[FrozenBaziFact, set, Dict[str, Any]]":
    """BaziChart → (FrozenBaziFact, available_facts, temporal_inputs).

    缺字段即缺项, fail-closed 由消费方处理 (下游 UNDETERMINED / FACT_MISSING).
    """
    pillars = tuple(_pillar_tuple(chart, i) for i in range(4))
    day_master = getattr(chart, "day_master", "") or ""
    month_branch = pillars[1][1]

    available: set = set()

    # --- 四柱 / 日主 / 月支 ---
    if all(p[0] and p[1] for p in pillars):
        available.update({"four_pillars", "day_master", "month_branch"})

    # --- 藏干 (Bazi 提供; 缺失时用通行表归一 — 确定性事实, 非重算 Bazi) ---
    raw_hidden = getattr(chart, "hidden_stems", None)
    if raw_hidden:
        hidden = _remap_pos_keyed(raw_hidden)
    else:
        hidden = {
            z: dict(BRANCH_HIDDEN.get(b, {"main": "", "middle": "", "residual": "", "all": []}))
            for z, (_, b) in zip(_ZP_POS, pillars)
        }
    if hidden:
        available.add("hidden_stems")

    # --- 透干十神 / 地支十神 (BAZI 已算, 只读取) ---
    stem_tg = {z: _ten_god_of(chart, i) for i, z in enumerate(_ZP_POS)}
    if any(stem_tg.values()):
        available.add("stem_ten_gods")
    branch_tg = _remap_pos_keyed(getattr(chart, "branch_ten_gods", None))
    if branch_tg:
        available.add("branch_ten_gods")

    # --- 干支关系 (raw facts, Bazi 已算; dict 原样保留, 键为拼音对) ---
    stem_he = list(getattr(chart, "stem_he_pairs", None) or [])
    relations: Dict[str, List[Any]] = {
        "he": list(getattr(chart, "branch_he_map", None) or []),
        "clash": list(getattr(chart, "branch_clash_map", None) or []),
        "harm": list(getattr(chart, "branch_harm_map", None) or []),
        "sanhe": list(getattr(chart, "branch_sanhe_map", None) or []),
        "sanxing": list(getattr(chart, "branch_sanxing_map", None) or []),
        "po": list(getattr(chart, "branch_po_pairs", None) or []),
        "stem_he": stem_he,
        "stem_clash": list(getattr(chart, "stem_clash_pairs", None) or []),
    }
    available.add("raw_relations")
    if stem_he:
        available.add("stem_he_pairs")

    # --- 十二长生 (Bazi 冻结口径, §72 REV-GROWTH: 子平只消费) ---
    growth = _remap_pos_keyed(getattr(chart, "twelve_growth", None))
    if growth:
        available.add("twelve_growth")

    # --- 时间层基础 (大运由 Bazi 提供; 流年/流月/流日 由调用方注入) ---
    luck_raw = list(getattr(chart, "luck_pillars", None) or [])
    luck: List[Tuple[str, str]] = []
    for p in luck_raw:
        if isinstance(p, tuple) and len(p) == 2:
            luck.append((p[0], p[1]))
        else:
            luck.append((getattr(p, "heavenly_stem", ""), getattr(p, "earthly_branch", "")))
    start_age = float(getattr(chart, "start_age", 0.0) or 0.0)
    if luck:
        available.add("luck_cycle")
        ti = dict(temporal_inputs or {})
        ti.setdefault("LUCK_PILLARS", list(luck))
        temporal_inputs = ti
    gender = getattr(chart, "gender", "male") or "male"

    # --- 确定性事实 (可选项, 缺失 → UNDETERMINED) ---
    nayin = _remap_pos_keyed(getattr(chart, "nayin", None))
    shensha = getattr(chart, "shensha", None)
    kong_wang = getattr(chart, "kong_wang", None)
    if nayin:
        available.add("nayin")
    if shensha:
        available.add("shensha")
    if kong_wang:
        available.add("kong_wang")
    if solar_term_crossing is not None:
        available.add("solar_term")
    if temporal_inputs:
        available.add("temporal_inputs")

    fact = FrozenBaziFact(
        four_pillars=pillars,
        day_master=day_master,
        month_branch=month_branch,
        hidden_stems=hidden,
        stem_ten_gods=stem_tg,
        branch_ten_gods=branch_tg,
        stem_he_pairs=[tuple(x) for x in stem_he] if stem_he else [],
        branch_relations=relations,
        twelve_growth=growth,
        luck_pillars=luck,
        start_age=start_age,
        gender=gender,
        nayin=nayin or None,
        shensha=shensha,
        kong_wang=tuple(kong_wang) if kong_wang else None,
        solar_term_crossing=solar_term_crossing,
    )
    return fact, available, temporal_inputs or {}


def chart_to_context(
    chart: Any,
    temporal_inputs: Optional[Dict[str, Any]] = None,
    solar_term_crossing: Optional[bool] = None,
) -> "Tuple[FrozenBaziFact, set, Dict[str, Any]]":
    """便捷入口: 返回 (fact, available_facts, temporal_inputs)."""
    return build_frozen_fact(chart, temporal_inputs, solar_term_crossing)
