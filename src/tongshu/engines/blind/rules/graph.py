"""Rule Graph 解析器：加载规则文件并执行匹配。"""
from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .models import MatchContext, Rule
from .matcher import RuleMatcher

# 规则文件目录：backend/data/rules/（从 graph.py 向上6级到项目根）
_RULES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "backend" / "data" / "rules"


@dataclass
class RuleGraph:
    """规则图：加载、匹配、应用 invalidates，返回最终规则集。"""

    rules: List[Rule] = field(default_factory=list)
    matcher: Optional[RuleMatcher] = field(default=None, repr=False)
    rules_dir: Path = field(default_factory=lambda: _RULES_DIR)

    def load(self, pattern: str = "BL-*.json") -> int:
        """从 rules_dir 加载规则文件，返回加载数量。"""
        rules = []
        for fp in glob.glob(str(self.rules_dir / pattern)):
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                items = data
            else:
                items = [data]
            for item in items:
                # BL-sample.json is legacy format without 'school' or 'judgment' fields
                school = item.get("school", "BLIND_SCHOOL")
                # Legacy format uses:
                # - title instead of judgment
                # - conditions.all instead of requires
                judgment = item.get("judgment", item.get("title", ""))
                requires = item.get("requires", item.get("conditions", {}).get("all", []))
                # Convert conditions to requires format (extract stem/branch values)
                requires_formatted = []
                for cond in requires:
                    if isinstance(cond, dict):
                        field = cond.get("field", "")
                        value = cond.get("value", "")
                        if field and value:
                            requires_formatted.append(f"{field}:{value}")
                    else:
                        requires_formatted.append(str(cond))
                rules.append(Rule(
                    rule_id=item["rule_id"],
                    school=school,
                    requires=requires_formatted,
                    invalidates=item.get("invalidates", []),
                    relations=item.get("relations", []),
                    judgment=judgment,
                    classic=item.get("classic", ""),
                    source_verified=item.get("source_verified", False),
                    evidence_refs=item.get("evidence_refs", []),
                ))
        self.rules = rules
        self.matcher = RuleMatcher(rules)
        return len(rules)

    def match(self, ctx: MatchContext) -> List[Rule]:
        """匹配规则并应用 invalidates 过滤。"""
        if self.matcher is None:
            raise RuntimeError("RuleGraph not loaded. Call load() first.")
        matched = self.matcher.match(ctx)
        return self.matcher.invalidate(matched, self.rules)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return next((r for r in self.rules if r.rule_id == rule_id), None)
