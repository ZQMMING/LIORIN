"""RuleMatcher — deterministic rule condition DSL (T201) + conflict resolution (T205).

Replaces the ad-hoc `_rule_matches` in rule_db.py with a typed, recursive
condition DSL. Per DECISION-009: unknown fields / operators raise hard errors —
a rule that references a misspelled field must fail loudly, never match
silently.

DSL syntax (JSON, lives in rule.conditions):
    - empty / null / {}  -> unconditional match (True)
    - {"all": [<cond>, ...]}  -> every child must match
    - {"any": [<cond>, ...]}  -> at least one child matches
    - {"not": <cond>}         -> child must NOT match
    - leaf: {"field": <str>, "op": <op>, "value": <literal|list>}

Operators (T201):
    eq ne in nin contains not_contains exists gte lte gt lt regex
    + EVENT_TOPIC-only: has has_any has_all present absent

Conflict resolution (T205):
    Matched rules are grouped by (layer, produces_signal_type). Within a group:
      - unanimous conclusion (direction, polarity)  -> one merged signal
        (rule_refs / evidence_refs = union)
      - disagreement -> unique winner by (precedence desc, specificity desc)
      - tie on both + conflicting conclusions -> the Signal is NOT produced
        (per v3.1 manual T205: "无法消解 → 不产出该 Signal")

RULES-EXPANSION-001 v1.3: extended FIELD_SPECS to register the 9 P2 chart
fields (spouse_star / spouse_star_attack / ... / five_element_imbalance) so
they pass `test_condition_fields_in_field_specs`. The matcher's `_eval_leaf`
does NOT actually evaluate these fields against RuleContext (the EVENT_TOPIC
rules are gated by SignalEngine's SIGNAL_LAYER_ORDER = (BASELINE,
CYCLE_CONTEXT, DAILY_ACTIVATION) and never enter the matcher's eval path).
The dedicated evaluator lives in `tongshu.reasoning.event_topic`.
"""

from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any

# --------------------------------------------------------------------------- #
# Field registry — the exact field set a rule may reference.
# Anything else raises at match time (DECISION-009: fail loud, never skip).
# --------------------------------------------------------------------------- #
FIELD_SPECS: dict[str, str] = {
    "day_master": "日主天干(大写,如 YI)",
    "day_master_element": "日主五行(WOOD/FIRE/EARTH/METAL/WATER)",
    "day_branch": "日支(如 XU)",
    "month_stem": "月干",
    "month_branch": "月支(如 CHOU)",
    "year_stem": "年干",
    "year_branch": "年支",
    "hour_stem": "时干",
    "hour_branch": "时支",
    "gender": "性别 M/F",
    "season": "季节 SPRING/SUMMER/AUTUMN/WINTER(由月支推导)",
    "soul_palace_main_star_key": "紫微命宫主星拼音键(如 TIANFU)",
    "soul_palace_main_star_zh": "紫微命宫主星中文名(如 天府)",
    "analysis_day_stem": "分析日天干(黄历日干)",
    "analysis_day_branch": "分析日地支",
    "daily_sihua_roles": "流日四化位列表(化禄/化权/化科/化忌)",
    "layer": "信号层(BASELINE/CYCLE_CONTEXT/DAILY_ACTIVATION/EVENT_TOPIC)",
    "theme": "人生主题(如 WORK)",
    "month_hidden_main_ten_god": "月支藏干主气对日主的十神(正印/偏印/比肩/劫财/食神/伤官/正财/偏财/正官/七杀)",
    "month_hidden_main_ten_god_transparent": "月支主气藏干是否透于四柱天干(bool;杂气格判据,《论杂气如何取用》)",
    "transparent_ten_gods": "年月时三干(日主除外)对日主的十神列表;透干显性(梯二「非当令十神透干」ZPZ-121~130,实时填充)",
    "day_master_stage_month": "日主于月支的十二长生位(长生/沐浴/冠带/临官/帝旺/衰/病/死/墓/绝/胎/养;三命通会·论天干生旺死绝)",
    "day_master_road_month": "月支是否为日主禄位(bool;建禄格判据,《三命通会·论建禄》)",
    "day_master_absolute_month": "月支是否为日主帝旺位(bool;阳刃/帝旺,《渊海子平·论阳刃》)",
    "day_branch_main_ten_god": "日支主气藏干对日主的十神(通根/得地判据,《滴天髓·论地支》)",
    "tianyi_guiren_branches": "命局四支(年月日时)中为日干天乙贵人的支列表(神煞判据,《三命通会·论天乙贵人》通行口诀)",
    # EVENT_TOPIC 层字段（婚姻/健康断事, EventTopicEngine 提供）
    # These are present so draft EVENT_TOPIC rules pass the static
    # `test_condition_fields_in_field_specs` audit. The matcher's _eval_leaf
    # never receives them in production (SignalEngine's SIGNAL_LAYER_ORDER
    # gates EVENT_TOPIC rules out of the matcher).
    "spouse_star": "配偶星强度(男=正财/女=正官, dict)",
    "spouse_star_attack": "配偶星受克状态(rob_wealth/guan_sha_mixed/none)",
    "officer_mixed": "女命官杀混杂(bool)",
    "day_branch_clash": "日支是否被冲(bool)",
    "day_branch_harm": "日支是否被刑/害(bool)",
    "spouse_star_strength": "配偶星强度档位 strong/weak/rootless",
    "peach_blossom": "日支是否桃花子午卯酉(bool)",
    "branch_clash_map": "四支冲关系图 dict (key=sorted pair, value=branch list)",
    "branch_harm_map": "四支害关系图 dict (key=sorted pair, value=branch list)",
    "five_element_imbalance": "五行失衡 bool (max > 0.40 or min < 0.05)",
    # T4 扩展(2026-08-26): 流年应期 + 河洛字段, 由 EventTopicEngine 提供
    "flow_year_stem": "流年天干",
    "flow_year_branch": "流年地支",
    "flow_year_branch_element": "流年地支五行",
    "flow_year_branch_clash_day_branch": "流年支冲日支 (bool)",
    "flow_year_branch_harm_day_branch": "流年支害日支 (bool)",
    "flow_year_branch_main_ten_god": "流年支主气藏干对日主的十神",
    "flow_year_branch_main_element_clash": "流年地支五行冲日主五行 (bool)",
    "heluo_benming_guawuxing": "河洛本命卦五行(金木水火土, 《河洛真数》)",
    "heluo_wuxing_imbalance": "河洛五行失衡 over/under/none",
    "heluo_dishu_youyu": "河洛地数有余 bool (凶数基础,《河洛真数·天地数》)",
    "heluo_birth_season_unfavorable": "生于河洛不利时节 bool (谷雨-芒种)",
    "heluo_benming_gong": "河洛本命卦宫位(坎离震坤巽艮兑乾, 领域定位)",
    "heluo_benming_guaming": "河洛本命卦名(六十四卦名,如乾为天/地天泰)",
    "heluo_yuantang": "河洛元堂爻名(初九/六二/.../上九/上六,等同八字日主)",
    "heluo_yuantang_index": "河洛元堂爻位(0-5,初爻=0,上爻=5)",
    "heluo_houtian_guaming": "河洛后天卦名(人生发展走势)",
}

OPS = (
    "eq", "ne", "in", "nin",
    "contains", "not_contains", "exists",
    "gte", "lte", "gt", "lt", "regex",
    # EVENT_TOPIC-only operators (handled by EventTopicEngine._eval_leaf, NOT
    # by the matcher's _eval_leaf). Listed here so static ops-enum checks
    # (e.g. in rule_loader validation passes) accept EVENT_TOPIC rules.
    "has", "has_any", "has_all", "present", "absent",
)

# 手册 §8.7 Rule 生命周期 draft→review→validated→active→deprecated:
# 「Rule Executor 只能执行已经批准的规则」——只有 validated(已批准待正式激活)
# 与 active 参与生产推理;draft/review 不执行(也防止 AI 自动 Active 的规则
# 静默生效,DECISION-010)。
EXECUTABLE_STATUSES = ("validated", "active")


class UnknownFieldError(KeyError):
    """Rule references a field outside FIELD_SPECS (DECISION-009)."""


class UnknownOperatorError(ValueError):
    """Rule uses an operator outside OPS (T201)."""


@dataclass(frozen=True)
class RuleContext:
    """Evaluation context handed to RuleMatcher.

    Only fields in FIELD_SPECS may be referenced by rules. Missing values are
    None (and match only against `exists: false`); a missing field NAME raises.
    """

    day_master: str | None = None
    day_master_element: str | None = None
    day_branch: str | None = None
    month_stem: str | None = None
    month_branch: str | None = None
    year_stem: str | None = None
    year_branch: str | None = None
    hour_stem: str | None = None
    hour_branch: str | None = None
    gender: str | None = None
    season: str | None = None
    soul_palace_main_star_key: str | None = None
    soul_palace_main_star_zh: str | None = None
    analysis_day_stem: str | None = None
    analysis_day_branch: str | None = None
    daily_sihua_roles: list[str] | None = None
    layer: str | None = None
    theme: str | None = None
    month_hidden_main_ten_god: str | None = None
    month_hidden_main_ten_god_transparent: bool | None = None
    transparent_ten_gods: list[str] | None = None
    day_master_stage_month: str | None = None
    day_master_road_month: bool | None = None
    day_master_absolute_month: bool | None = None
    day_branch_main_ten_god: str | None = None
    tianyi_guiren_branches: list[str] | None = None
    # EVENT_TOPIC-only fields (kept here so draft EVENT_TOPIC rules can be
    # statically validated; matcher never evaluates them in production).
    spouse_star: dict | None = None
    spouse_star_attack: str | None = None
    officer_mixed: bool | None = None
    day_branch_clash: bool | None = None
    day_branch_harm: bool | None = None
    spouse_star_strength: str | None = None
    peach_blossom: bool | None = None
    branch_clash_map: dict | None = None
    branch_harm_map: dict | None = None
    five_element_imbalance: bool | None = None
    # T4 扩展(2026-08-26): 流年应期 + 河洛字段(EventTopicEngine 提供)
    flow_year_stem: str | None = None
    flow_year_branch: str | None = None
    flow_year_branch_element: str | None = None
    flow_year_branch_clash_day_branch: bool | None = None
    flow_year_branch_harm_day_branch: bool | None = None
    flow_year_branch_main_ten_god: str | None = None
    flow_year_branch_main_element_clash: bool | None = None
    heluo_benming_guawuxing: str | None = None
    heluo_wuxing_imbalance: str | None = None
    heluo_dishu_youyu: bool | None = None
    heluo_birth_season_unfavorable: bool | None = None
    heluo_benming_gong: str | None = None
    heluo_benming_guaming: str | None = None
    heluo_yuantang: str | None = None
    heluo_yuantang_index: int | None = None
    heluo_houtian_guaming: str | None = None


def _eval_leaf(conditions: dict, ctx: RuleContext) -> bool:  # noqa: PLR0911 - intentional multi-return
    """Evaluate a single leaf condition.

    Per DECISION-009: unknown fields/operators raise. Empty leaves match False.
    """
    field = conditions.get("field")
    if field not in FIELD_SPECS:
        raise UnknownFieldError(
            f"unknown field '{field}' (not in FIELD_SPECS; DECISION-009)"
        )
    op = conditions.get("op")
    if op not in OPS:
        raise UnknownOperatorError(
            f"unknown operator '{op}' (not in OPS; DECISION-009)"
        )
    actual = getattr(ctx, field)
    value = conditions.get("value")
    if op == "exists":
        return bool(actual) == bool(value)
    if op == "eq":
        return actual == value
    if op == "ne":
        return actual != value
    if op == "in":
        if isinstance(value, (list, tuple, set)):
            return actual in value
        return actual == value
    if op == "nin":
        if isinstance(value, (list, tuple, set)):
            return actual not in value
        return actual != value
    if op in ("contains", "not_contains"):
        if isinstance(actual, (list, tuple, set)):
            contained = value in actual
        elif isinstance(actual, str):
            contained = str(value) in actual
        else:
            contained = False
        if op == "contains":
            return contained
        return not contained
    if op in ("gte", "lte", "gt", "lt"):
        try:
            a, v = float(actual), float(value)
        except (TypeError, ValueError):
            return False
        if op == "gte":
            return a >= v
        if op == "lte":
            return a <= v
        if op == "gt":
            return a > v
        return a < v
    if op == "regex":
        try:
            return re.search(str(value), str(actual)) is not None
        except re.error as exc:
            raise ValueError(f"invalid regex in rule: {value!r}: {exc}") from exc
    # EVENT_TOPIC-only ops (has/has_any/has_all/present/absent): never reach
    # here in production (SignalEngine gates EVENT_TOPIC rules out of matcher).
    # If they do (e.g. someone bypasses the layer gate), fall through to a
    # fail-loud default.
    raise UnknownOperatorError(
        f"operator '{op}' is EVENT_TOPIC-only and must not reach the matcher; "
        f"use EventTopicEngine instead (DECISION-009 fail-loud)"
    )


def evaluate_conditions(conditions: dict | None, ctx: RuleContext) -> bool:
    """Recursively evaluate the DSL condition tree (T201)."""
    if not conditions:
        return True
    if not isinstance(conditions, dict):
        raise ValueError(f"conditions must be an object, got {type(conditions).__name__}")
    if "all" in conditions:
        return all(evaluate_conditions(c, ctx) for c in conditions["all"])
    if "any" in conditions:
        return any(evaluate_conditions(c, ctx) for c in conditions["any"])
    if "not" in conditions:
        return not evaluate_conditions(conditions["not"], ctx)
    return _eval_leaf(conditions, ctx)


def count_conditions(conditions: dict | None) -> int:
    """Specificity = number of leaf nodes in the condition tree (T205).

    Combinators contribute their children's leaves; a leaf contributes 1.
    Empty / null conditions contribute 0.
    """
    if not conditions:
        return 0
    if not isinstance(conditions, dict):
        raise ValueError(f"conditions must be an object, got {type(conditions).__name__}")
    if "all" in conditions:
        return sum(count_conditions(c) for c in conditions["all"])
    if "any" in conditions:
        return sum(count_conditions(c) for c in conditions["any"])
    if "not" in conditions:
        return count_conditions(conditions["not"])
    return 1  # leaf


class RuleMatcher:
    """Holds rules and selects the ones matching a RuleContext (T201)."""

    def __init__(self, rules: list[dict]):
        self._rules = list(rules)

    @property
    def rules(self) -> list[dict]:
        return list(self._rules)

    def match_all(self, ctx: RuleContext, layer: str | None = None) -> list[dict]:
        """All *executable* rules matching ctx, optionally filtered by layer.

        Per §8.7 lifecycle (DECISION-010): only validated / active rules
        participate in production reasoning; draft / review rules are inert.
        """
        matched = []
        for r in self._rules:
            if r.get("status", "active") not in EXECUTABLE_STATUSES:
                continue
            if layer is not None and layer not in r.get("applies_to_layers", []):
                continue
            if evaluate_conditions(r.get("conditions"), ctx):
                matched.append(r)
        return matched


# --------------------------------------------------------------------------- #
# T205 conflict resolution
# --------------------------------------------------------------------------- #

def rule_precedence(rule: dict) -> int:
    return int(rule.get("precedence", 0) or 0)


def rule_specificity(rule: dict) -> int:
    hint = rule.get("specificity_hint")
    if hint is not None:
        return int(hint)
    return count_conditions(rule.get("conditions"))


def _conclusion_signature(rule: dict) -> tuple:
    tpl = rule.get("conclusion", {}).get("produces_layer_output_template", {})
    return (tpl.get("direction"), tpl.get("polarity"))


def rule_refs_of(rule: dict) -> list[str]:
    """Rule IDs backing a signal. For a merged group this is the union."""
    merged = rule.get("_rule_refs")
    if merged:
        return list(merged)
    rid = rule.get("rule_id")
    return [rid] if rid else []


def resolve_conflicts(matched: list[dict]) -> list[dict]:
    """T205: group matched rules by produces_signal_type; resolve per group.

    - single rule -> kept
    - unanimous conclusion -> merged (refs unioned; _rule_refs set)
    - conflicting conclusions -> winner by (precedence desc, specificity desc);
      a tie on both -> the Signal is dropped entirely
    """
    groups: dict[str, list[dict]] = {}
    for r in matched:
        groups.setdefault(r.get("produces_signal_type"), []).append(r)

    out: list[dict] = []
    for stype in sorted(groups):
        rules = groups[stype]
        if len(rules) == 1:
            out.append(rules[0])
            continue

        conclusions = {_conclusion_signature(r) for r in rules}
        if len(conclusions) == 1:
            base = rules[0]
            merged = dict(base)
            merged["_rule_refs"] = sorted({r.get("rule_id") for r in rules if r.get("rule_id")})
            merged["evidence_refs"] = sorted(
                {er for r in rules for er in r.get("evidence_refs", [])}
            )
            out.append(merged)
            continue

        # Conflicting conclusions: unique winner by precedence then specificity.
        ranked = sorted(
            rules,
            key=lambda r: (-rule_precedence(r), -rule_specificity(r)),
        )
        top_p, top_s = rule_precedence(ranked[0]), rule_specificity(ranked[0])
        winners = [
            r for r in rules
            if rule_precedence(r) == top_p and rule_specificity(r) == top_s
        ]
        if len(winners) == 1:
            out.append(winners[0])
        # else: tie among conflicting conclusions -> Signal not produced (T205)

    return out
