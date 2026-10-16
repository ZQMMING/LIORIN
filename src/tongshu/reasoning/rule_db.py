"""Rule DB - in-memory rule lookup for v1.0 demo.

P1-A FIX: Rules are now matched by structured conditions on
(USO type, day_master element, etc). day_master parameter is actually USED.
"""

from __future__ import annotations


DAY_MASTER_ELEMENT = {
    "JIA": "WOOD", "YI": "WOOD",
    "BING": "FIRE", "DING": "FIRE",
    "WU": "EARTH", "JI": "EARTH",
    "GENG": "METAL", "XIN": "METAL",
    "REN": "WATER", "GUI": "WATER",
}


class RuleDB:
    """In-memory Rule DB stub."""

    def __init__(self):
        self._rules = []

    def load(self, rules):
        self._rules = list(rules)

    def get_baseline_rules(self, day_master: str) -> list:
        """Return baseline-layer rules matching the day_master."""
        matched = []
        dm_element = DAY_MASTER_ELEMENT.get(day_master, "")
        for r in self._rules:
            if "BASELINE" not in r.get("applies_to_layers", []):
                continue
            if self._rule_matches(r, day_master, dm_element):
                matched.append(r)
        return matched

    def get_cycle_rules(self, bazi_chart) -> list:
        matched = []
        for r in self._rules:
            if "CYCLE_CONTEXT" not in r.get("applies_to_layers", []):
                continue
            if self._rule_matches(r, bazi_chart.day_master, DAY_MASTER_ELEMENT.get(bazi_chart.day_master, "")):
                matched.append(r)
        return matched

    def get_daily_rules(self, huangli) -> list:
        """Return daily-activation rules matching today's day pillar."""
        matched = []
        day_stem = huangli.day_stem
        day_branch = huangli.day_branch
        for r in self._rules:
            if "DAILY_ACTIVATION" not in r.get("applies_to_layers", []):
                continue
            matches = r.get("matches", {})
            trigger_stems = matches.get("trigger_day_stems", [])
            trigger_branches = matches.get("trigger_day_branches", [])
            if trigger_stems and day_stem not in trigger_stems:
                continue
            if trigger_branches and day_branch not in trigger_branches:
                continue
            matched.append(r)
        return matched

    def _rule_matches(self, rule: dict, day_master: str, dm_element: str) -> bool:
        matches = rule.get("matches", {})
        stems = matches.get("applies_to_day_masters", [])
        if stems and day_master not in stems:
            return False
        elements = matches.get("applies_to_elements", [])
        if elements and dm_element not in elements:
            return False
        onto_types = matches.get("applies_to_ontology_types", [])
        if onto_types and not stems and not elements:
            if rule.get("produces_signal_type") not in onto_types:
                return False
        return True
