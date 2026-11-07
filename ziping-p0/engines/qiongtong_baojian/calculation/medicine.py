"""QTBJ 穷通调候派生（《窮通寶鑑》· 引擎自有 Derived Facts，§65）。

《窮通寶鑑》核心是调候表：日干 × 月令 → 调候用神（先用/次用/忌）。
规则以 medicine/require 表达（registries/rule/rules.qtbj.jsonl）：
- operator=require：调候「要求」非事实，由引擎自有派生消费（§65），输出 local_requirement；
  Phase 7 再据命局判「得/不得」。
- 合论月（如己土巳午未「取癸為要，次用丙火」）以 month_branch 列表 + in 算子表达。

依据原著原文（精校稿 v1 / 国图民国本 v3）：
- 正月甲木：「先用丙癸（得丙癸透，無丙癸平常人）」（QTBJ-003-002）
- 三夏己土：「取癸為要，次用丙火……無癸曰旱田，無丙曰孤陰」（QTBJ-058-001）
- 三冬丁火：「三冬丁火微寒，端用庚甲……甲木為尊，庚金佐之」（QTBJ-046-001）

禁重排盘：只消费 L0 day_stem/month_branch + 正式 Rule Registry。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shared_types.fail_closed import FailClosedReason, FailClosedError

ROOT = Path(__file__).resolve().parent.parent.parent.parent
RULES_PATH = ROOT / "registries" / "rule" / "rules.qtbj.jsonl"

# (day_stem, frozenset(month_branches)) → (local_requirement, rule_id)
_INDEX: Optional[Dict[Tuple[str, frozenset], Tuple[str, str]]] = None


def _load_index() -> Dict[Tuple[str, frozenset], Tuple[str, str]]:
    """加载 QTBJ Rule Registry（require 调候规则）为查表索引。

    - 单月规则：month_branch equals 单值
    - 合论月规则：month_branch in 列表（如己土巳午未）
    编译期校验：日干/月支合法、output 为 local_requirement、source_ids 存在（§63）。
    """
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    if not RULES_PATH.exists():
        raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                              f"缺少 QTBJ Rule Registry: {RULES_PATH}")
    idx: Dict[Tuple[str, frozenset], Tuple[str, str]] = {}
    stems = set("甲乙丙丁戊己庚辛壬癸")
    branches = set("子丑寅卯辰巳午未申酉戌亥")
    for line in RULES_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("operator") != "require":
            continue  # 本派生只消费调候 require 规则
        conds = r.get("preconditions", {}).get("conditions", [])
        ds = mb = None
        for c in conds:
            if c.get("field") == "day_stem":
                ds = c.get("value")
            elif c.get("field") == "month_branch":
                v = c.get("value")
                mb = frozenset(v) if isinstance(v, list) else frozenset([v])
        if not ds or not mb:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                                  f"QTBJ 调候规则缺 day_stem/month_branch: {r.get('rule_id')}")
        if ds not in stems:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法日干: {ds} @ {r.get('rule_id')}")
        bad = mb - branches
        if bad:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法月支: {bad} @ {r.get('rule_id')}")
        out = r.get("output")
        if not isinstance(out, dict) or out.get("field") != "local_requirement":
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                                  f"QTBJ output 非 local_requirement: {r.get('rule_id')}")
        if not r.get("source_ids"):
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                                  f"QTBJ 调候规则无 Source 绑定: {r.get('rule_id')}")
        idx[(ds, mb)] = (str(out.get("value")), r.get("rule_id"))
    _INDEX = idx
    return idx


def derive_medicine(day_stem: Optional[str], month_branch: Optional[str],
                    hidden: Any = None, transparent_stems: Any = None,
                    branches: Any = None,
                    base: Any = None, l0_chart: Any = None) -> Dict[str, Any]:
    """日干 × 月支 → 调候用神（local_requirement）· 合论月 in 匹配。

    返回 {local_requirement, local_requirement_rule}；矩阵无此组合 → 返回空（不臆造）。
    """
    if not day_stem or not month_branch:
        raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN,
                              "调候派生需要 day_stem/month_branch")
    idx = _load_index()
    for (ds, months), (value, rid) in idx.items():
        if ds == day_stem and month_branch in months:
            return {"local_requirement": value, "local_requirement_rule": rid}
    return {}  # 原书无此组合调候（合论节无月级表述）→ 不产出
