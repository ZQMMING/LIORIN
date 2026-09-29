"""Rule 匹配器：评估 requires，应用 invalidates。"""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from .models import MatchContext, Rule


class RuleMatcher:
    """规则匹配器：评估 requires 条件，返回命中的规则 ID 列表。"""

    def __init__(self, rules: List[Rule]):
        self.rules = {r.rule_id: r for r in rules}
        self._index_by_requires()

    def _index_by_requires(self) -> None:
        self._req_index: Dict[str, List[str]] = {}
        for r in self.rules.values():
            for req in r.requires:
                self._req_index.setdefault(req, []).append(r.rule_id)

    def match(self, ctx: MatchContext) -> List[Rule]:
        hit_ids = set()
        conditions = self._flatten_requires(ctx)
        for cond in conditions:
            for rid in self._req_index.get(cond, []):
                hit_ids.add(rid)
        matched = []
        for rid in hit_ids:
            rule = self.rules[rid]
            if all(c in conditions for c in rule.requires):
                matched.append(rule)
        return matched

    def invalidate(self, matched: List[Rule], all_rules: List[Rule]) -> List[Rule]:
        """应用 invalidates 逻辑：若某规则 X 的 invalidates 列表包含另一条已命中规则 Y，则 Y 被排除。

        语义：rule.invalidates = [其他规则ID] 表示「本规则命中时，排除这些规则」。
        例：A 的 invalidates=["B"]，A 命中 → B 被移除。
        """
        # 找出所有因其他规则命中而被排除的规则 ID
        excluded: Set[str] = set()
        for r in matched:
            for excl_id in r.invalidates:
                excluded.add(excl_id)
        return [r for r in matched if r.rule_id not in excluded]

    def _flatten_requires(self, ctx: MatchContext) -> Set[str]:
        conditions: Set[str] = set()
        for _, stem in ctx.stems.items():
            conditions.add(f"stem:{stem}")
        for _, br in ctx.branches.items():
            conditions.add(f"branch:{br}")
        for _, tg in ctx.ten_gods.items():
            conditions.add(f"tg:{tg}")
        for s in ctx.ti_stems:
            if s in ctx.ten_gods:
                conditions.add(f"tg:{ctx.ten_gods[s]}")
        for s in ctx.yong_stems:
            if s in ctx.ten_gods:
                conditions.add(f"tg:{ctx.ten_gods[s]}")
        for b in ctx.ti_branches:
            conditions.add(f"ti_in:{b}")
        for b in ctx.yong_branches:
            conditions.add(f"yong_in:{b}")
        for method in ctx.zuo_gong_methods:
            conditions.add(f"zuo_gong:{method}")
        for b1, b2 in self._branch_pairs(ctx.branches):
            rel = self._branch_relation(b1, b2)
            if rel:
                conditions.add(f"branch_relation:{rel}:{b1}:{b2}")
        return conditions

    @staticmethod
    def _branch_pairs(branches: Dict[str, str]):
        vals = list(branches.values())
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                yield vals[i], vals[j]

    @staticmethod
    def _branch_relation(b1: str, b2: str) -> Optional[str]:
        if b1 == b2:
            return None
        from ...blind_bazi_engine import BRANCH_LIUHE, BRANCH_CHONG, BRANCH_CHUAN
        if BRANCH_LIUHE.get(b1) == b2 or BRANCH_LIUHE.get(b2) == b1:
            return "liuhe"
        if BRANCH_CHONG.get(b1) == b2 or BRANCH_CHONG.get(b2) == b1:
            return "chong"
        if BRANCH_CHUAN.get(b1) == b2 or BRANCH_CHUAN.get(b2) == b1:
            return "chuan"
        return None
