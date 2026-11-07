"""L0 Adapter + Contexts（Phase 6 §65）。

- l0_adapter: 标准 L0 Chart（§B-2 字段）→ 基础 rules view（单值字段 + 多值 branch）
- contexts: 从 rules view 生成求值上下文（每柱干支 / 十神目标干 / 支对 / 单支）
  Rule Engine 对每个上下文求值，汇总去重 facts。
- 禁重排盘：本模块只消费 L0 字段，不计算任何命盘（rechart 禁止）
"""

from __future__ import annotations

from typing import Any, Dict, List

from shared_types.fail_closed import FailClosedReason, FailClosedError

BRANCH_SEASON = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}

STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def build_base_view(l0_chart: Dict[str, Any]) -> Dict[str, Any]:
    """L0 Chart → 基础 rules view（只映射，不计算）。"""
    pillars = l0_chart.get("pillars")
    if not pillars or "day" not in pillars:
        raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, "L0 chart 缺少 pillars.day")
    day = pillars["day"]
    v: Dict[str, Any] = {
        "day_stem": day.get("stem"),
        "day_branch": day.get("branch"),
        "year_stem": pillars.get("year", {}).get("stem"),
        "year_branch": pillars.get("year", {}).get("branch"),
        "month_stem": pillars.get("month", {}).get("stem"),
        "month_branch": pillars.get("month", {}).get("branch"),
        "hour_stem": pillars.get("hour", {}).get("stem"),
        "hour_branch": pillars.get("hour", {}).get("branch"),
        "branch": [p.get("branch") for p in pillars.values() if p.get("branch")],
        "branch_a": None,
        "branch_b": None,
        "stem_branch_pair": (day.get("stem") or "") + (day.get("branch") or ""),
        "day_element": STEM_ELEMENT.get(day.get("stem", "")),
        "gender": l0_chart.get("gender"),
    }
    mb = v["month_branch"]
    v["season"] = BRANCH_SEASON.get(mb, "") if mb else ""
    xunkong = l0_chart.get("xunkong") or {}
    v["xun"] = xunkong.get("xun", "")
    # L0 已提供的派生事实直接透传（§B-2：shishen/changsheng/nayin/relations 是 L0 层）
    v["shishen"] = l0_chart.get("shishen") or {}
    v["changsheng"] = l0_chart.get("changsheng") or {}
    v["nayin"] = l0_chart.get("nayin") or {}
    v["relations"] = l0_chart.get("relations") or {}
    return v


def build_contexts(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    """生成求值上下文列表。

    1. 日柱上下文（day_stem/branch/stem_branch_pair/season/xun/gender 齐备）
    2. 十神目标干上下文（day_stem + target_stem = 年干/月干/时干/日支藏干首干）
    3. 支对上下文（六合/六冲/六害候选：地支两两组合）
    4. 单支上下文（三合/神煞/空亡：每支 + day_element）
    5. 年/月/时柱上下文（year_stem/stem_branch_pair 等纳音/宫位）
    """
    ctxs: List[Dict[str, Any]] = []

    # 1. 日柱
    day_ctx = dict(view)
    day_ctx["context"] = "day_pillar"
    ctxs.append(day_ctx)

    # 2. 十神：日干 vs 年干/月干/时干/日支藏干
    stems = [s for s in [_stem_of(view, "year"), _stem_of(view, "month"), _stem_of(view, "hour")] if s]
    hidden = view.get("shishen", {}).get("day_branch_hidden") or []
    for t in list(dict.fromkeys(stems + (hidden[:1] if hidden else []))):
        c = dict(view)
        c["target_stem"] = t
        c["context"] = "ten_god"
        ctxs.append(c)

    # 3. 支对（六合/六冲/六害）：四柱支两两
    branches = view.get("branch") or []
    seen_pairs = set()
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            a, b = branches[i], branches[j]
            if not a or not b:
                continue
            key = tuple(sorted((a, b)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            c = dict(view)
            c["branch_a"], c["branch_b"] = a, b
            c["context"] = "branch_pair"
            ctxs.append(c)

    # 4. 单支（三合/神煞/空亡）
    for b in branches:
        if not b:
            continue
        c = dict(view)
        c["branch"] = b
        c["context"] = "branch_single"
        ctxs.append(c)

    # 5. 年/月/时柱
    for key in ("year", "month", "hour"):
        p = _pillar_of(view, key)
        if p:
            c = dict(view)
            c["context"] = f"{key}_pillar"
            c["stem_branch_pair"] = p
            c["branch"] = p[1:]
            ctxs.append(c)
    return ctxs


def _stem_of(view: Dict[str, Any], pos: str) -> str:
    return view.get(f"{pos}_stem") or ""


def _pillar_of(view: Dict[str, Any], pos: str) -> str:
    """返回 '干支' 串（如 甲子）。"""
    stem = view.get(f"{pos}_stem") or ""
    branch = view.get(f"{pos}_branch") or ""
    return stem + branch if stem and branch else ""
