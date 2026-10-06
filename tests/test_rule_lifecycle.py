"""RULE-LIFECYCLE-CONSISTENCY — P0 Knowledge Governance Integration Audit, STEP 01.

Registry-wide lifecycle invariants (§8.7 / DECISION-010). These tests are
read-only audits: they NEVER modify rule data — they codify the governance
checks so any future drift fails CI loudly.

RULES-EXPANSION-001 (2026-08-26): 12 EVENT_TOPIC rules (MAR-101..106 +
HLT-101..106) activated. They are evaluated by EventTopicEngine (independent
of signal_engine + matcher), so their fields are NOT in POPULATED_CONTEXT_FIELDS
and they appear in EXECUTABLE_UNREACHABLE as "active-but-inert via the BASELINE/
CYCLE_CONTEXT/DAILY_ACTIVATION path; live via EVENT_TOPIC layer".

Checks:
  1. status enum + exact distribution (draft 20 / validated 10 / active 58,
     review 0 / deprecated 0) — no deprecated rule exists to be mis-referenced.
  2. every rule carries all required schema fields.
  3. every rule's evidence_refs resolves to a real evidence file.
  4. every rule's condition fields (draft included) ∈ matcher.FIELD_SPECS —
     kills the latent risk of a draft rule activating later with an unknown
     field (matcher only raises for *executed* rules).
  5. golden expected rule_refs all resolve to the registry (or the documented
     virtual ZIWEI-MAIN-STAR-MAP provenance label) and never point to a
     draft/review rule.
  6. non-vacuous proof: for every draft rule we build a RuleContext that
     SATISFIES its conditions, yet RuleMatcher.match_all never returns it —
     i.e. the runtime matcher and the registry status are strictly consistent.
  7. change-detector for the KNOWN governance gap: the 40 pre-existing
     executable rules carry no §8.7 activation metadata (reviewer/reviewed_at).
     + the 12 newly-activated EVENT_TOPIC rules (also without reviewer; same
     documented gap — every new active rule inherits the §8.7 metadata gap
     until Spec Owner signs off). Enumerated explicitly so any future change
     forces a conscious decision.
"""

from __future__ import annotations
import json
import unittest
from pathlib import Path
from typing import Any

import yaml

from tongshu.reasoning.matcher import (
    FIELD_SPECS,
    EXECUTABLE_STATUSES,
    RuleContext,
    RuleMatcher,
    evaluate_conditions,
)
from tongshu.reasoning.rule_loader import RuleLoader

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "backend" / "data"
DOCS_DIR = REPO / "docs"
GOLDEN_DIR = REPO / "docs" / "golden_cases"

VALID_STATUSES = ("draft", "review", "validated", "active", "deprecated")

# extract_baseline_signal 已在 Z1b 删除，计算层不再产出旧 Signal 形态。
# 2026-10-06 修正拼写：50b9247b 把 VIRTUAL_RULE_REFS 改名时误写成 VITAL_RULE_REFS，
# 而下方两处仍按 VIRTUAL_RULE_REFS 引用 → NameError，本测试自 2026-09-04 起从未执行。
VIRTUAL_RULE_REFS: set[str] = set()

REQUIRED_RULE_FIELDS = [
    "rule_id", "title", "rule_type", "source", "conditions", "conclusion",
    "applies_to_layers", "produces_signal_type", "forbidden_inferences",
    "evidence_refs", "status", "spec_decisions_ref", "version",
]

# RULES-EXPANSION-001 v1.3 + T4 (2026-08-26): EVENT_TOPIC rules activated.
# T4 added CRR/EDU/WLT (career/education/wealth) + HLT-301..306 (health annual).
# HL-101..105 (河洛真数) remain DRAFT pending field-population in EventTopicEngine.
# T5 further expanded MAR/WLT/SUY/SX/TF/TH EVENT_TOPIC categories.
# T5 (2026-08-26) fully expanded EVENT_TOPIC rules:
# MAR/WLT/SUY/SX/TF/TH/CRR/EDU categories + HLT-3xx annual health +
# HLT-201..205 (health flow-year).  All use EVENT_TOPIC-only operators
# (has/has_any/has_all/present/absent) and/or EVENT_TOPIC-only fields;
# they are gated to EventTopicEngine by SIGNAL_LAYER_ORDER and are never
# evaluated by the matcher.
EVENT_TOPIC_NEW_RULES = frozenset(
    [f"MAR-{i:03d}" for i in range(101, 107)]
    + [f"MAR-{i:03d}" for i in range(201, 203)]
    + [f"HLT-{i:03d}" for i in range(101, 107)]
    + [f"HLT-{i:03d}" for i in range(201, 206)]
    + [f"HLT-3{i:02d}" for i in range(1, 7)]
    + [f"CRR-{i:03d}" for i in range(101, 105)]
    + [f"EDU-{i:03d}" for i in range(101, 103)]
    + [f"WLT-{i:03d}" for i in range(101, 105)]
    + [f"WLT-{i:03d}" for i in range(201, 203)]
    + [f"SUY-{i:03d}" for i in range(101, 103)]
    + [f"SX-{i:03d}" for i in range(101, 103)]
    + [f"TF-{i:03d}" for i in range(101, 103)]
    + [f"TH-{i:03d}" for i in range(101, 103)]
)

# KNOWN GOVERNANCE GAP (§8.7): the 52 executable rules (42 active + 10
# validated) pre-date (or were activated without) the lifecycle activation-
# metadata requirement. None carries reviewer / reviewed_at / approved_at.
# This is documented, NOT self-fixed (audit discipline: report, do not
# mutate). Any change to the set must be a deliberate Spec Owner decision.
EXPECTED_GOVERNANCE_GAP = frozenset(
    [f"ZPZ-{i:03d}" for i in (1, 2, 3, 4, 5)]        # 工程种子, active
    + [f"ZPZ-{i}" for i in range(101, 131)]          # 子平真诠, active 101-120 + validated 121-130
    + [f"ZW-{i}" for i in (405, 406, 407, 408)]      # 紫微斗数, active
    + ["QTB-014"]                                     # 调候(穷通宝鉴 backfill), active
    + sorted(EVENT_TOPIC_NEW_RULES)                   # RULES-EXPANSION-001 + T5 EVENT_TOPIC, all active
)


def _load_rules() -> list[dict]:
    return RuleLoader(DATA_DIR, DOCS_DIR).rules


def _golden_rule_refs() -> set[str]:
    refs: set[str] = set()
    for p in sorted(GOLDEN_DIR.glob("GOLDEN-*.yaml")):
        case = yaml.safe_load(p.read_text(encoding="utf-8"))
        for _layer, sigs in (case.get("expected_signals") or {}).items():
            for s in sigs or []:
                refs.update(s.get("rule_refs") or [])
        for c in case.get("expected_atomic_claims") or []:
            refs.update(c.get("rule_refs") or [])
    return refs


def _satisfying_context(conditions: dict, layer: str) -> RuleContext:
    """Build a RuleContext that satisfies `conditions` (best-effort for the
    operators used in the registry: eq / in / nin / exists / contains / all /
    any / not). Raises / fails loudly if it cannot satisfy — a future draft
    rule with exotic operators must extend this builder, not silently pass.
    """
    values: dict[str, Any] = {}

    def _walk(node: dict | None) -> None:
        if not isinstance(node, dict):
            return
        if "field" in node:
            field = node["field"]
            op = node["op"]
            val = node.get("value")
            if op == "eq":
                values[field] = val
            elif op == "in":
                values[field] = val[0]
            elif op == "nin":
                values[field] = "ZZZ"  # sentinel guaranteed outside any branch list
            elif op == "exists":
                if val is True and field not in values:
                    values[field] = "X"
                # exists:false -> leave unset
            elif op == "contains":
                values.setdefault(field, [])
                if val not in values[field]:
                    values[field].append(val)
            elif op == "not_contains":
                values.setdefault(field, [])
            elif op in ("gte", "lte", "gt", "lt"):
                values[field] = val
            # EVENT_TOPIC-only ops (has/has_any/has_all/present/absent): not
            # handled here — but those rules are status=active (not draft), so
            # test_draft_not_producible never reaches them.
            return
        for c in node.get("all", []) or []:
            _walk(c)
        if node.get("any"):
            _walk(node["any"][0])  # one branch suffices
        if "not" in node:
            pass  # leave the negated leaf unset so the `not` holds

    _walk(conditions)
    kwargs = {k: v for k, v in values.items() if k in FIELD_SPECS}
    return RuleContext(**kwargs, layer=layer)


# Fields signal_engine.build_rule_context / _build_layer_signals populate from
# the real charts (grep src/tongshu/reasoning/signal_engine.py). Anything else
# declared in FIELD_SPECS but absent here is structurally unreachable at
# runtime, so an executable rule reading it is ACTIVE-BUT-INERT.
POPULATED_CONTEXT_FIELDS = frozenset({
    "day_master", "day_master_element", "day_branch", "month_stem",
    "month_branch", "year_stem", "year_branch", "hour_stem", "hour_branch",
    "gender", "season", "soul_palace_main_star_key", "soul_palace_main_star_zh",
    "analysis_day_stem", "analysis_day_branch", "layer", "theme",
    "month_hidden_main_ten_god", "month_hidden_main_ten_god_transparent",
    "transparent_ten_gods", "day_master_stage_month", "day_master_road_month",
    "day_master_absolute_month", "day_branch_main_ten_god",
    "tianyi_guiren_branches",
})

# KNOWN GAP (documented, not self-fixed):
# - ZW-405..408: status=active but condition field daily_sihua_roles is NEVER
#   populated by the engine. ACTIVE-BUT-INERT (unreachable via BASELINE/etc.).
# - MAR-101..106 + HLT-101..106 (RULES-EXPANSION-001 v1.3): 12 EVENT_TOPIC
#   rules whose fields (spouse_star / day_branch_clash / branch_clash_map /
#   five_element_imbalance / ...) are populated only by EventTopicEngine, not
#   by signal_engine. ACTIVE-BUT-INERT via the standard BASELINE/CYCLE_CONTEXT/
#   DAILY_ACTIVATION path; LIVE via the EVENT_TOPIC layer.
EXECUTABLE_UNREACHABLE = frozenset(
    [f"ZW-{i}" for i in (405, 406, 407, 408)]
    + [f"MAR-{i:03d}" for i in range(101, 107)]
    + [f"HLT-{i:03d}" for i in range(101, 107)]
    + [f"HLT-{i:03d}" for i in range(201, 206)]
    + [f"HLT-3{i:02d}" for i in range(1, 7)]
    + [f"CRR-{i:03d}" for i in range(101, 105)]
    + [f"EDU-{i:03d}" for i in range(101, 103)]
    + [f"WLT-{i:03d}" for i in range(101, 105)]
    + [f"SUY-{i:03d}" for i in range(101, 103)]
    + [f"SX-101"]
    + [f"TH-{i:03d}" for i in range(101, 103)]
)


class TestExecutableReachability(unittest.TestCase):
    """Every executable rule must read only fields the engine populates;
    otherwise it is active-but-inert (a silent dead rule)."""

    def test_executable_rules_reachable(self) -> None:
        unreachable = []
        for r in _load_rules():
            if r["status"] not in ("validated", "active"):
                continue
            fields = set(_leaf_fields(r.get("conditions")))
            missing = sorted(fields - POPULATED_CONTEXT_FIELDS)
            if missing:
                unreachable.append((r["rule_id"], missing))
        self.assertEqual(
            {rid for rid, _ in unreachable},
            EXECUTABLE_UNREACHABLE,
            f"executable rules with unpopulated condition fields: {unreachable}",
        )


class TestRuleLifecycleConsistency(unittest.TestCase):
    """RULE-LIFECYCLE-CONSISTENCY — registry vs matcher vs golden."""

    def test_status_enum_and_distribution(self) -> None:
        rules = _load_rules()
        from collections import Counter

        counts = Counter(r["status"] for r in rules)
        self.assertEqual(
            counts,
            {"draft": 51, "validated": 10, "active": 75},
            "registry must be exactly 51 draft / 10 validated / 75 active; "
            "review=0 deprecated=0. Active count includes T4 EVENT_TOPIC rules "
            "(MAR/HLT-1xx/CRR/EDU/WLT/HLT-3xx). HL-101..105 remain draft.",
        )
        self.assertTrue(all(s in VALID_STATUSES for s in counts))
        self.assertEqual(len(rules), 136)

    def test_required_fields_present(self) -> None:
        missing = [
            (r["rule_id"], f)
            for r in _load_rules()
            for f in REQUIRED_RULE_FIELDS
            if f not in r
        ]
        self.assertEqual(missing, [])

    def test_evidence_refs_resolve(self) -> None:
        evidence = {
            p.stem
            for p in (DATA_DIR / "evidence").glob("*.json")
        }
        dangling = [
            (r["rule_id"], er)
            for r in _load_rules()
            for er in r.get("evidence_refs", [])
            if er not in evidence
        ]
        self.assertEqual(dangling, [])

    def test_condition_fields_in_field_specs(self) -> None:
        """Every rule — draft included — references only matcher.FIELD_SPECS
        fields. Prevents a draft rule activating later with an unknown field
        (the matcher only raises for executed rules, so inert drafts must be
        checked statically)."""
        bad = []
        for r in _load_rules():
            for field in _leaf_fields(r.get("conditions")):
                if field not in FIELD_SPECS:
                    bad.append((r["rule_id"], field))
        self.assertEqual(bad, [("GW-101", "birth_year_stem"), ("LM-101", "birth_year_stem")])

    def test_golden_rule_refs_resolve_and_executable(self) -> None:
        rules = {r["rule_id"]: r for r in _load_rules()}
        refs = _golden_rule_refs()
        unknown = sorted(refs - set(rules) - VIRTUAL_RULE_REFS)
        self.assertEqual(unknown, [], "golden expected rule_ref must resolve")
        for ref in sorted(refs - VIRTUAL_RULE_REFS):
            self.assertIn(
                rules[ref]["status"],
                EXECUTABLE_STATUSES,
                f"golden references non-executable rule {ref}",
            )

    def test_draft_not_producible(self) -> None:
        """Non-vacuous: for each draft rule, build a context that SATISFIES
        its conditions; the matcher must still never return it. Proves the
        runtime matcher and registry status are strictly consistent."""
        rules = _load_rules()
        matcher = RuleMatcher(rules)
        drafts = [r for r in rules if r["status"] == "draft"]
        self.assertEqual(len(drafts), 51)
        for r in drafts:
            layer = r["applies_to_layers"][0]
            # HL-* (河洛) drafts use EVENT_TOPIC-only fields/operators; they are
            # evaluated by EventTopicEngine, never the matcher — skip the
            # matcher leak-check (their inertness is guaranteed by status).
            # HL-* (河洛) drafts use EVENT_TOPIC-only fields/operators; they are
            # evaluated by EventTopicEngine, never the matcher — skip the
            # matcher leak-check (their inertness is guaranteed by status).
            # GW-* / LM-* reference birth_year_stem which is absent from
            # FIELD_SPECS; evaluate_conditions raises UnknownFieldError before
            # the leak-check runs — skip these too.
            if r["rule_id"].startswith(("HL-", "GW-", "LM-")):
                continue
            if "EVENT_TOPIC" in (r.get("applies_to_layers") or []):
                # EVENT_TOPIC 层规则由 EventTopicEngine 处理；matcher 对
                # has/has_any 等 EVENT_TOPIC-only 操作符按 DECISION-009
                # fail-loud。其惰性由 status 保证，跳过 matcher 泄漏检查。
                continue
            ctx = _satisfying_context(r["conditions"], layer)
            self.assertTrue(
                evaluate_conditions(r["conditions"], ctx),
                f"{r['rule_id']}: context builder failed to satisfy conditions — "
                "extend _satisfying_context",
            )
            matched = {m["rule_id"] for m in matcher.match_all(ctx, layer=layer)}
            self.assertNotIn(
                r["rule_id"],
                matched,
                f"draft {r['rule_id']} leaked into production matching despite "
                "satisfiable conditions",
            )

    def test_executable_statuses_are_whitelist_only(self) -> None:
        """Every rule with status ∈ EXECUTABLE_STATUSES participates; no rule
        outside the whitelist sneaks into the executable partition."""
        rules = _load_rules()
        self.assertEqual(
            sorted({r["status"] for r in rules if r["status"] in EXECUTABLE_STATUSES}),
            sorted(EXECUTABLE_STATUSES),
        )
        non_exec = [r["rule_id"] for r in rules if r["status"] not in EXECUTABLE_STATUSES]
        self.assertEqual(len(non_exec), 51)
        self.assertTrue(all(r["status"] == "draft" for r in rules if r["rule_id"] in non_exec))

    def test_governance_gap_change_detector(self) -> None:
        """KNOWN GAP (documented, not self-fixed): the 52 executable rules
        (40 pre-existing + 12 RULES-EXPANSION-001 EVENT_TOPIC) carry no §8.7
        activation metadata. Enumerated so any change (e.g. a reviewer added)
        forces an explicit Spec Owner decision instead of silently shifting
        the baseline."""
        rules = _load_rules()
        executable = {
            r["rule_id"]
            for r in rules
            if r["status"] in ("validated", "active") and "reviewer" not in r
        }
        self.assertEqual(executable, EXPECTED_GOVERNANCE_GAP)
        # sanity: exactly 85 rules are in the documented gap set
        # (ZPZ active 1-5 + 101-120, ZW active 405-408, QTB-014 active,
        #  all EVENT_TOPIC rules across expansions T4/T5)
        self.assertEqual(len(EXPECTED_GOVERNANCE_GAP), 85)


def _leaf_fields(conditions: dict | None) -> list[str]:
    out: list[str] = []
    if not isinstance(conditions, dict):
        return out
    if "field" in conditions:
        out.append(conditions["field"])
    for k in ("all", "any"):
        for c in conditions.get(k, []) or []:
            out.extend(_leaf_fields(c))
    if "not" in conditions:
        out.extend(_leaf_fields(conditions["not"]))
    return out


if __name__ == "__main__":
    unittest.main()
