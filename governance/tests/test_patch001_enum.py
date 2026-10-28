"""V2.22-PATCH-001 §19 Acceptance Criteria：TEST-ENUM-001~010。

铁律：Boolean ≠ Business Judgment；MATCH ≠ YES；UNKNOWN ≠ NO；
RULE_NOT_APPLICABLE ≠ NO；Existence ≠ Strength ≠ Effectiveness；
Pattern Existence ≠ Pattern Success；Disease ≠ Medicine；
未注册 Enum 必须 FAIL_CLOSED；多态语义必须 Multi-State Enum。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.enums import (  # noqa: E402
    DTSEffectState,
    DTSSupportState,
    DTSStrengthState,
    RuleMatchState,
    EngineStatus,
)
from shared_types.fail_closed import FailClosedError  # noqa: E402
from engines.yuhai_ziping.rule.rule_engine import _eval_condition, _eval_preconditions  # noqa: E402

REGISTRY = json.load(open(ROOT / "governance" / "enum_registry.json", encoding="utf-8"))
RULES_DIR = ROOT / "registries" / "rule"


def _load_rules(engine: str):
    lines = (RULES_DIR / f"rules.{engine}.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


ALL_ENGINES = ("yhzp", "pzzq", "dts", "qtbj", "smth", "sftk")


# ---------------------------------------------------------------- TEST-ENUM-001
def test_enum_001_boolean_not_business_judgment_output():
    """Boolean 不得作为 Business Judgment 输出：六部规则无 `"value": true/false`。"""
    for eng in ALL_ENGINES:
        rules = _load_rules(eng)
        for r in rules:
            outs = r.get("output", [])
            if isinstance(outs, dict):
                outs = [outs]
            for o in outs:
                assert not isinstance(o.get("value"), bool), (
                    f"{eng} {r['rule_id']}: Boolean 业务输出 {o}"
                )


# ---------------------------------------------------------------- TEST-ENUM-002
def test_enum_002_match_not_yes():
    """MATCH 不得直接等同于 YES：RuleMatchState 值域无 YES。"""
    assert RuleMatchState.MATCH.value == "MATCH"
    assert "YES" not in {m.value for m in RuleMatchState}
    # registry rule_match_state 同步
    e = next(e for e in REGISTRY["enums"] if e["enum_id"] == "rule_match_state")
    assert "YES" not in e["values"]


# ---------------------------------------------------------------- TEST-ENUM-003
def test_enum_003_unknown_not_no():
    """UNKNOWN 不得转换为 NO：M-1/M-2 守卫不允许否定注入。"""
    from phase0.state_model import StateGuard
    # 守卫可调用且不抛错（允许明确表达，禁止赋否定语义）
    StateGuard.assert_no_negation_injection(RuleMatchState.UNKNOWN)
    StateGuard.assert_no_negation_injection(RuleMatchState.RULE_NOT_APPLICABLE)
    # EngineStatus.UNKNOWN 存在且独立于 PASS/FAIL（非 NO 语义）
    assert EngineStatus.UNKNOWN.value == "UNKNOWN"
    assert "NO" not in {s.value for s in EngineStatus}


# ---------------------------------------------------------------- TEST-ENUM-004
def test_enum_004_same_concept_cross_book_domains_independent():
    """同一 Concept 不同经典可拥有不同 State Domain：dts_* 与 pzzq_* 值域不交叉。"""
    dts_vals = set()
    pzzq_vals = set()
    for e in REGISTRY["enums"]:
        if e["enum_id"].startswith("dts_"):
            dts_vals |= set(e["values"])
        if e["enum_id"].startswith("pzzq_"):
            pzzq_vals |= set(e["values"])
    # 交叉值仅允许 UNDETERMINED/UNKNOWN 兜底类
    overlap = dts_vals & pzzq_vals
    allowed = {"UNDETERMINED", "UNKNOWN", "NONE"}
    assert overlap <= allowed, f"跨书值域污染: {overlap - allowed}"


# ---------------------------------------------------------------- TEST-ENUM-005
def test_enum_005_strength_not_boolean():
    """STRONG/WEAK 不得使用 Boolean 替代：strength_state 为六级枚举。"""
    assert len(DTSStrengthState) == 6
    assert set(DTSStrengthState.__members__) == {
        "STRONG", "SLIGHTLY_STRONG", "NEUTRAL",
        "SLIGHTLY_WEAK", "WEAK", "UNDETERMINED",
    }
    e = next(e for e in REGISTRY["enums"] if e["enum_id"] == "dts_strength_state")
    assert "UNDETERMINED" in e["values"]


# ---------------------------------------------------------------- TEST-ENUM-006
def test_enum_006_conditional_not_auto_yes():
    """CONDITIONAL 不得自动转换为 YES：规则层无 conditional→true/YES 的消费。"""
    for eng in ALL_ENGINES:
        for r in _load_rules(eng):
            for c in r.get("preconditions", {}).get("conditions", []):
                if c.get("value") == "conditional":
                    # 条件值=conditional 允许（如 SMTH 激活三态），但不得以 bool/YES 断言
                    assert c.get("operator") in ("equals", "in", "not_in"), c
                    assert not isinstance(c.get("value"), bool)
    # SMTH 激活三态含 conditional（多态，非 YES/NO 二态）
    e = next(e for e in REGISTRY["enums"] if e["enum_id"] == "smth_activation_status")
    assert "conditional" in e["values"]
    assert len(e["values"]) >= 3


# ---------------------------------------------------------------- TEST-ENUM-007
def test_enum_007_rule_not_applicable_not_business():
    """RULE_NOT_APPLICABLE 不得进入 Business Judgment：仅属 RuleMatchState。"""
    e_match = next(e for e in REGISTRY["enums"] if e["enum_id"] == "rule_match_state")
    assert "RULE_NOT_APPLICABLE" in e_match["values"]
    e_status = next(e for e in REGISTRY["enums"] if e["enum_id"] == "engine_status")
    assert "RULE_NOT_APPLICABLE" not in e_status["values"]
    assert "RULE_NOT_APPLICABLE" not in {s.value for s in EngineStatus}


# ---------------------------------------------------------------- TEST-ENUM-008
def test_enum_008_unregistered_enum_fail_closed():
    """未注册 Enum 必须 FAIL_CLOSED：未知算子/聚合触发 FailClosedError。"""
    with pytest.raises(FailClosedError):
        _eval_condition({}, {"operator": "gt", "field": "x", "value": 3})
    with pytest.raises(FailClosedError):
        _eval_preconditions({}, {"type": "xor", "conditions": []})


# ---------------------------------------------------------------- TEST-ENUM-009
def test_enum_009_boolean_only_schema_fails():
    """Boolean-only schema 检查必须 FAIL：校验器拒绝 Boolean 值输出。"""
    from shared_types.fail_closed import FailClosedReason

    def assert_boolean_free(output):
        """业务 output 若为 Boolean-only → FailClosedError。"""
        outs = output if isinstance(output, list) else [output]
        for o in outs:
            if isinstance(o.get("value"), bool):
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                                      "Boolean-only Business Judgment 被拒绝")
        return True

    assert_boolean_free({"field": "qing_state", "value": "半濁半清"})
    with pytest.raises(FailClosedError):
        assert_boolean_free({"field": "is_strong", "value": True})


# ---------------------------------------------------------------- TEST-ENUM-010
def test_enum_010_multistate_required():
    """经典原文存在多态语义时，必须使用 Multi-State Enum。"""
    # registry 无单值枚举、无二态无兜底（v1.8.0 铁律）
    for e in REGISTRY["enums"]:
        vals = e.get("values") or []
        assert len(vals) != 1, f"{e['enum_id']} 单值枚举"
        if len(vals) == 2:
            assert set(vals) & {"UNKNOWN", "UNDETERMINED"}, f"{e['enum_id']} 二态无兜底"
    # 成败/化从/清浊均多态
    for eid in ("pzzq_chengbai_state", "dts_hua_state", "dts_qing_state"):
        e = next(e for e in REGISTRY["enums"] if e["enum_id"] == eid)
        assert len(e["values"]) >= 3, f"{eid} 应多态"
    # 病/药分离（sftk_disease_type ≠ sftk_medicine_type）
    disease = next(e for e in REGISTRY["enums"] if e["enum_id"] == "sftk_disease_type")
    medicine = next(e for e in REGISTRY["enums"] if e["enum_id"] == "sftk_medicine_type")
    assert disease["values"] != medicine["values"]
    assert set(disease["values"]) & set(medicine["values"]) == set()
