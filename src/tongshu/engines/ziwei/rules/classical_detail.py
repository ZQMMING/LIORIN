# -*- coding: utf-8 -*-
"""经典细则层 —— Z80-H 接线：把 Z77–Z86 期古籍原文资产接入生产。

背景（Z80-G 待裁决项「11 个零引用模块」）：
    ``pattern_rules`` / ``temporal_rules`` / ``temporal_facts`` /
    ``child_limit_rules`` / ``nvming_rules`` / ``limit_advanced_rules``
    六模块此前在 ``src/`` 内**零生产引用**，其原典细目（富/贵/贫/杂格局、
    十二宫得地失陷诀、太岁小限、童限、女命、限运叠加）从未进入任何输出。

本模块把这六类资产**按机器可判定的条件**接入生产，并以**独立通道**
（``classical_detail``）输出，不并入既有 12 宫位维 / 体用层：

  - **不融合**：每条保留 ``school=CLASSICAL_SOURCE`` 与原典出处（source/section）；
  - **不污染**：独立字段，不参与既有维度归位，不影响 12 维/领域断语；
  - **可回查**：每条带 ``rule_id`` + ``verbatim``，与 asset_index 登记项一一对应。

边界（算→辨→解分层铁律）：
  - 本层只做「条件命中 → 原典条文列举」，**不做吉凶评分、不做加权融合**；
  - 未命中一律不输出（fail-closed）；
  - ``classical_patterns`` 为**候选**匹配（仅校验 supporting_stars 齐备，
    成格细节如夹/拱/宫位需人工复核），显式标注 ``match_level=candidate``。

Public API:
    build_classical_detail(chart) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List

from . import pattern_rules
from . import temporal_facts
from . import temporal_rules
from . import child_limit_rules
from . import nvming_rules
from . import limit_advanced_rules

_DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_SHA_YAO = ("擎羊", "陀罗")

# 十二宫序（与引擎盘面一致；第 8 宫为「仆役」）
_ZW_PALACES_ORDER = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
]


# ── 基础取值助手 ────────────────────────────────────────────────────────

def _year_gan(year: int) -> str:
    """公历年 → 天干（1984=甲子 基准）。"""
    return _TIANGAN[(year - 4) % 10]


def _year_zhi(year: int) -> str:
    """公历年 → 地支（1984=甲子 基准）。"""
    return _DIZHI[(year - 4) % 12]


def _palace_of_branch(chart, branch: str) -> str:
    for name, p in (chart.palaces or {}).items():
        if p.get("branch", "") == branch:
            return name
    return ""


def _stars_in(chart, palace: str) -> set:
    p = (chart.palaces or {}).get(palace) or {}
    return set(p.get("major", []) or []) | set(p.get("minor", []) or []) | set(
        p.get("adjective", []) or [])


def _sanfang_sizheng(chart, palace: str) -> List[str]:
    """三方四正（本宫+对宫+两合宫）宫名。"""
    try:
        i = _ZW_PALACES_ORDER.index(palace)
    except ValueError:
        return [palace]
    return [
        _ZW_PALACES_ORDER[i],
        _ZW_PALACES_ORDER[(i + 4) % 12],
        _ZW_PALACES_ORDER[(i + 8) % 12],
        _ZW_PALACES_ORDER[(i + 6) % 12],
    ]


def _age(chart) -> int:
    """流年虚岁（flow_year - birth_year）；未知返回 0。"""
    fy = getattr(chart, "flow_year", 0) or 0
    by = getattr(chart, "birth_year", 0) or 0
    if fy and by and fy > by:
        return fy - by
    return 0


# ── 各资产接线 ──────────────────────────────────────────────────────────

def _match_palace_jue(chart, rules: List[dict], kind: str) -> List[dict]:
    """十二宫得地/失陷诀：按命宫地支匹配（palace_branch 可为多字合并宫位）。"""
    branch = getattr(chart, "soul_earthly_branch", "") or ""
    if not branch:
        return []
    out: List[dict] = []
    for r in rules:
        pb = r.get("palace_branch", "")
        if branch and branch in pb:
            out.append({
                "kind": kind,
                "rule_id": r.get("rule_id", ""),
                "palace_branch": pb,
                "verbatim": r.get("verbatim", ""),
                "source": r.get("source", ""),
                "source_section": r.get("source_section", ""),
            })
    return out


def _match_classical_patterns(chart) -> List[dict]:
    """经典格局候选：supporting_stars 齐备于「命宫+三方四正」（候选级）。

    作用域限定为命三方（命宫 + 三合两宫 + 对宫），与古籍「格局看命三方」
    一致；全盘扫描会因 14 主星+众辅星组合过多而产生大量伪命中（实测
    1983 盘全盘 28 条 vs 命三方 1 条）。
    仅校验必要星曜齐备，成格细节（夹/拱/宫位/庙陷）需人工复核。
    """
    scope: set = set()
    for pn in _sanfang_sizheng(chart, "命宫"):
        scope |= _stars_in(chart, pn)
    if not scope:
        return []
    out: List[dict] = []
    for p in pattern_rules.ALL_PATTERNS:
        sup = set(p.get("supporting_stars") or [])
        if len(sup) < 2:
            continue
        if sup <= scope:
            out.append({
                "rule_id": p.get("pattern_id", ""),
                "pattern_name": p.get("pattern_name", ""),
                "verbatim": p.get("verbatim", ""),
                "supporting_stars": sorted(sup),
                "breaking_conditions": list(p.get("breaking_conditions") or []),
                "source": p.get("source", ""),
                "source_section": p.get("source_section", ""),
                "match_level": "candidate",
                "match_note": "命三方（命宫+三合+对宫）星曜齐备；夹/拱/宫位等成格细节需人工复核",
            })
    return out


def _match_nvming(chart) -> List[dict]:
    """女命专条：gender=female 时按命宫星曜匹配 good_stars/bad_stars。"""
    if (getattr(chart, "gender", "") or "").lower() not in ("female", "女"):
        return []
    ming = _stars_in(chart, "命宫")
    if not ming:
        return []
    out: List[dict] = []
    for r in nvming_rules.ALL_NVMING:
        good = set(r.get("good_stars") or [])
        bad = set(r.get("bad_stars") or [])
        hit = sorted((good | bad) & ming)
        if not hit:
            continue
        out.append({
            "rule_id": r.get("rule_id", ""),
            "name": r.get("name", ""),
            "hit_stars": hit,
            "polarity": "吉" if (good & ming) else "凶",
            "condition": r.get("condition", ""),
            "verbatim": r.get("verbatim", ""),
            "source": r.get("source", ""),
            "source_section": r.get("source_section", ""),
        })
    return out


def _match_child_limit(chart) -> List[dict]:
    """童限：年龄 ≤15 时出安童限诀；另出十二宫强弱（性别相关，常适用）。"""
    out: List[dict] = []
    age = _age(chart)
    for r in child_limit_rules.CHILD_LIMIT_RULES:
        rid = r.get("rule_id", "")
        if rid == "CL-01" and 1 <= age <= 15:
            out.append({
                "rule_id": rid, "name": r.get("name", ""),
                "age": age,
                "verbatim": r.get("verbatim", ""),
                "condition": r.get("condition", ""),
                "source": r.get("source", ""),
                "source_section": r.get("source_section", ""),
            })
        elif rid == "CL-05":
            out.append({
                "rule_id": rid, "name": r.get("name", ""),
                "gender": getattr(chart, "gender", ""),
                "verbatim": r.get("verbatim", ""),
                "condition": r.get("condition", ""),
                "source": r.get("source", ""),
                "source_section": r.get("source_section", ""),
            })
    return out


def _match_limit_advanced(chart) -> List[dict]:
    """限运进阶：羊陀迭并 / 七杀重逢（本命羊陀 + 流年流羊流陀冲照）。"""
    fy = getattr(chart, "flow_year", 0) or 0
    if not fy:
        return []
    ming_branch = getattr(chart, "soul_earthly_branch", "") or ""
    if not ming_branch:
        return []
    mi = _DIZHI.index(ming_branch)
    opposite_branch = _DIZHI[(mi + 6) % 12]
    ming_stars = _stars_in(chart, "命宫")
    dui_palace = _palace_of_branch(chart, opposite_branch)
    dui_stars = _stars_in(chart, dui_palace) if dui_palace else set()
    # 本命羊陀：命宫或对宫
    ben_sha = {s for s in (ming_stars | dui_stars) if s in _SHA_YAO}
    # 流年流羊/流陀所在宫位
    flow = temporal_facts.flow_star_positions(_year_gan(fy))
    flow_sha_branches = {flow.get("yang", ""), flow.get("tuo", "")}
    # 七杀本命三合（命宫三方四正）
    sanfang = _sanfang_sizheng(chart, "命宫")
    sanfang_stars: set = set()
    for pn in sanfang:
        sanfang_stars |= _stars_in(chart, pn)

    out: List[dict] = []
    for r in limit_advanced_rules.LIMIT_ADVANCED_RULES:
        rid = r.get("rule_id", "")
        hit = False
        detail: Dict[str, Any] = {}
        if rid == "LA-01":
            # 本命羊陀在对宫冲合命 + 流年流羊流陀冲照命/对宫
            if ben_sha and (flow_sha_branches & {ming_branch, opposite_branch}):
                hit = True
                detail = {"ben_sha": sorted(ben_sha),
                          "flow_sha": sorted(b for b in flow_sha_branches if b)}
        elif rid == "LA-02":
            # 本命三合有七杀 + 流年流羊流陀冲照命/对宫
            if "七杀" in sanfang_stars and (
                    flow_sha_branches & {ming_branch, opposite_branch}):
                hit = True
                detail = {"flow_sha": sorted(b for b in flow_sha_branches if b)}
        if hit:
            out.append({
                "rule_id": rid, "name": r.get("name", ""),
                "verbatim": r.get("verbatim", ""),
                "condition": r.get("condition", ""),
                "breaking_condition": r.get("breaking_condition", ""),
                "source": r.get("source", ""),
                "source_section": r.get("source_section", ""),
                "detail": detail,
            })
    return out


def _match_temporal_rules(chart, xiaoxian_palace: str, taisui_branch: str,
                          xiaoxian_branch: str) -> List[dict]:
    """太岁小限：太岁宫与**小限宫同宫**时，取该宫星曜吉凶（原典第九十六）。

    原典条件为「太岁宫=X 且 小限宫=X」——二者同宫方成岁限叠加；
    故此处要求 ``taisui_branch == xiaoxian_branch`` 才匹配。
    """
    if not xiaoxian_palace or not taisui_branch:
        return []
    if taisui_branch != xiaoxian_branch:
        return []
    stars = _stars_in(chart, xiaoxian_palace)
    if not stars:
        return []
    out: List[dict] = []
    for r in temporal_rules.TAISUI_XIAOXIAN_RULES:
        rp = r.get("palace", "")
        # 逐宫条（TMPL-04+）带 palace 字段；TMPL-01/02/03 为「子」年示例条
        target = rp if rp else "子"
        if target != taisui_branch:
            continue
        good = set(r.get("good_stars") or [])
        bad = set(r.get("bad_stars") or [])
        hit = sorted((good | bad) & stars)
        if not hit:
            continue
        out.append({
            "rule_id": r.get("rule_id", ""),
            "name": r.get("name", ""),
            "hit_stars": hit,
            "polarity": "吉" if (good & stars) else "凶",
            "verbatim": r.get("verbatim", ""),
            "condition": r.get("condition", ""),
            "source": r.get("source", ""),
            "source_section": r.get("source_section", ""),
        })
    return out


def _match_aux_verdicts(chart, doujun_palace: str) -> List[dict]:
    """辅煞杂曜 × 宫位原典断语（《诸星问答论》等）——接入 ANSWER 层
    VERDICT_INTERPRETATION 中**此前不可达**的辅助星/斗君键。

    背景：``answer_layer.get_interpretation`` 仅以「命宫主星」调用
    （facts["stars"] 只含主星），故 VERDICT_INTERPRETATION 的 102 个
    辅助星/斗君键（禄存/昌曲/辅弼/羊陀火铃/斗君 等）**永不可达**。
    本函数在经典细则层以「本盘实际存在的辅煞星 + 斗君落宫」为条件重新
    接入，只输出真实命中的条目（fail-closed），不做任何加权。

    组合键（如「天魁天钺」「擎羊陀罗」）需其全部组成星同宫方命中。
    """
    from .answer_layer import VERDICT_INTERPRETATION

    # 组合键可拆分的组成星（按已知辅煞名贪心切分）
    _KNOWN = ("天魁", "天钺", "擎羊", "陀罗", "火星", "铃星", "左辅", "右弼",
              "文昌", "文曲", "禄存", "天马", "地空", "地劫")
    _DOUJUN = "斗君"

    def _split_combined(s: str) -> List[str]:
        parts, i = [], 0
        while i < len(s):
            for k in _KNOWN:
                if s.startswith(k, i):
                    parts.append(k)
                    i += len(k)
                    break
            else:
                return []  # 无法切分 → 视为非组合键
        return parts

    out: List[dict] = []
    for palace, pdata in (chart.palaces or {}).items():
        present = set(pdata.get("major", []) or []) | set(
            pdata.get("minor", []) or []) | set(pdata.get("adjective", []) or [])
        for star in sorted(present):
            key = (palace, star)
            if key in VERDICT_INTERPRETATION:
                v = VERDICT_INTERPRETATION[key]
                out.append({
                    "palace": palace, "star": star,
                    "hit": [star],
                    "classic": v.get("classic", ""),
                    "vernacular": v.get("vernacular", ""),
                })
        # 组合键（全部组成星同宫）
        for (p, s), v in VERDICT_INTERPRETATION.items():
            if p != palace or s in present:
                continue
            parts = _split_combined(s)
            if parts and len(parts) >= 2 and all(x in present for x in parts):
                out.append({
                    "palace": palace, "star": s,
                    "hit": sorted(parts),
                    "classic": v.get("classic", ""),
                    "vernacular": v.get("vernacular", ""),
                })
    # 斗君（宫位标志，非星曜）
    if doujun_palace:
        v = VERDICT_INTERPRETATION.get((doujun_palace, _DOUJUN))
        if v:
            out.append({
                "palace": doujun_palace, "star": _DOUJUN,
                "hit": [_DOUJUN],
                "classic": v.get("classic", ""),
                "vernacular": v.get("vernacular", ""),
            })
    return out


def _temporal_facts_block(chart) -> Dict[str, Any]:
    """时间层 Fact：小限宫 / 斗君宫 / 太岁宫 / 流禄流羊流陀 落宫。"""
    facts: Dict[str, Any] = {}
    by = getattr(chart, "birth_year", 0) or 0
    fy = getattr(chart, "flow_year", 0) or 0
    if by:
        facts["birth_year_ganzhi"] = f"{_year_gan(by)}{_year_zhi(by)}"
    if fy:
        taisui_branch = _year_zhi(fy)
        facts["flow_year_ganzhi"] = f"{_year_gan(fy)}{taisui_branch}"
        facts["taisui_palace"] = _palace_of_branch(chart, taisui_branch)
        # 小限宫
        age = _age(chart)
        gender = getattr(chart, "gender", "") or ""
        g = "男" if str(gender).lower() in ("male", "男") else "女"
        if by and age:
            try:
                xb = temporal_facts.small_limit_branch(_year_zhi(by), g, age)
                facts["xiaoxian_branch"] = xb
                facts["xiaoxian_palace"] = _palace_of_branch(chart, xb)
            except ValueError:
                pass
        # 流曜
        flow = temporal_facts.flow_star_positions(_year_gan(fy))
        facts["flow_stars"] = {
            "禄": _palace_of_branch(chart, flow["lu"]),
            "羊": _palace_of_branch(chart, flow["yang"]),
            "陀": _palace_of_branch(chart, flow["tuo"]),
        }
    # 斗君（生年）
    dj = getattr(chart, "doujun_palace", "") or ""
    if dj:
        facts["doujun_palace"] = dj
    return facts


# ── 主入口 ──────────────────────────────────────────────────────────────

def build_classical_detail(chart) -> Dict[str, Any]:
    """构建经典细则层（独立通道，不并入 12 宫位维/体用层）。

    Returns:
        {
          "palace_jue":        [...],   # 十二宫得地/失陷诀（按命宫地支）
          "classical_patterns":[...],   # 富/贵/贫/杂格局候选
          "nvming":            [...],   # 女命专条（仅 female）
          "child_limit":       [...],   # 童限 / 十二宫强弱
          "limit_advanced":    [...],   # 限运进阶（羊陀迭并/七杀重逢）
          "temporal_rules":    [...],   # 太岁小限吉凶条
          "aux_verdicts":      [...],   # 辅煞杂曜×宫位原典断语（含斗君）
          "temporal_facts":    {...},   # 小限/斗君/太岁/流曜 落宫
          "summary":           {...},
        }
    """
    tfacts = _temporal_facts_block(chart)
    taisui_branch = ""
    if tfacts.get("flow_year_ganzhi"):
        taisui_branch = tfacts["flow_year_ganzhi"][-1]
    xiaoxian_palace = tfacts.get("xiaoxian_palace", "")
    xiaoxian_branch = tfacts.get("xiaoxian_branch", "")

    palace_jue = (
        _match_palace_jue(chart, pattern_rules.PALACE_FORTUNE_RULE, "得地合格诀")
        + _match_palace_jue(chart, pattern_rules.PALACE_DEPRIVATION_RULE, "失陷破格诀")
    )
    detail = {
        "palace_jue": palace_jue,
        "classical_patterns": _match_classical_patterns(chart),
        "nvming": _match_nvming(chart),
        "child_limit": _match_child_limit(chart),
        "limit_advanced": _match_limit_advanced(chart),
        "temporal_rules": _match_temporal_rules(
            chart, xiaoxian_palace, taisui_branch, xiaoxian_branch),
        "aux_verdicts": _match_aux_verdicts(
            chart, getattr(chart, "doujun_palace", "") or ""),
        "temporal_facts": tfacts,
    }
    detail["summary"] = {
        "palace_jue": len(detail["palace_jue"]),
        "classical_patterns": len(detail["classical_patterns"]),
        "nvming": len(detail["nvming"]),
        "child_limit": len(detail["child_limit"]),
        "limit_advanced": len(detail["limit_advanced"]),
        "temporal_rules": len(detail["temporal_rules"]),
        "aux_verdicts": len(detail["aux_verdicts"]),
    }
    return detail


__all__ = ["build_classical_detail"]
