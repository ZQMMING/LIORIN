"""V2.2.2 FINAL §58 Phase 0 测试覆盖标准（100% = 定义的治理规则全部有对应测试）。

覆盖：Schema validation / Type validation / Contract validation /
Static import boundary / Runtime input boundary / Forbidden symbols / Golden permission
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.enums import (  # noqa: E402
    EngineID, EngineStatus, RuleMatchState, TextLayer, EvidenceGrade,
    Operator, RuleOperator, PZZQFormationState, DTSStrengthState,
    QTBJRequirementType, SMTHCombinationType, SFTKDiseaseType,
)
from shared_types.errors import GoldenPermissionError, StateModelError  # noqa: E402
from phase0.canonical_gate import CanonicalGate  # noqa: E402
from phase0.validate_schemas import validate_all, REQUIRED_SCHEMAS, SCHEMA_DIR  # noqa: E402
from phase0.check_import_boundaries import scan_files as scan_imports  # noqa: E402
from phase0.check_input_contracts import scan_files as scan_runtime  # noqa: E402
from phase0.check_forbidden_symbols import scan_files as scan_forbidden  # noqa: E402
from phase0.check_golden_permissions import scan_files as scan_golden  # noqa: E402
from phase0.state_model import StateGuard  # noqa: E402
from governance.golden_permission_guard import (  # noqa: E402
    GoldenPermissionGuard, GoldenRecord, ActorRole, GoldenAction,
)


# ---------- Schema validation 100% ----------

def test_all_13_schemas_exist_and_valid():
    errors = validate_all()
    assert errors == {}, f"Schema 校验失败: {errors}"
    for name in REQUIRED_SCHEMAS:
        assert (SCHEMA_DIR / name).exists(), f"缺少 {name}"


def test_schema_are_draft_2020_12():
    for name in REQUIRED_SCHEMAS:
        schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", name
        assert schema.get("$id"), name
        assert schema.get("additionalProperties", None) is False, f"{name} 非严格对象"


# ---------- Type validation 100% ----------

def test_engine_status_excludes_rule_not_applicable():
    vals = {e.value for e in EngineStatus}
    assert "RULE_NOT_APPLICABLE" not in vals
    assert "PASS" in vals and "FAIL_CLOSED" in vals


def test_operator_whitelist_no_comparators():
    vals = {o.value for o in Operator}
    assert vals == {"equals", "in", "not_in", "exists", "not_exists"}
    assert not (vals & {">", "<", ">=", "<="})


def test_key_enums_values():
    assert PZZQFormationState.FORMED.value == "FORMED"
    assert DTSStrengthState.UNDETERMINED.value == "UNDETERMINED"
    assert QTBJRequirementType.PRIMARY.value == "PRIMARY"
    assert SMTHCombinationType.BAN_HE.value == "半合"
    assert SFTKDiseaseType.DIAO.value == "雕"
    assert TextLayer.ORIGINAL.value == "ORIGINAL"
    assert EvidenceGrade.A.value == "A"
    assert RuleOperator.EMIT.value == "emit"


def test_rule_match_state_four_values():
    assert {s.value for s in RuleMatchState} == {"MATCH", "NO_MATCH", "RULE_NOT_APPLICABLE", "UNKNOWN"}


# ---------- Contract validation 100% ----------

def test_contract_engine_read_matrix():
    from phase0.contract_validator import ALLOWED_ENGINE_READS
    assert ALLOWED_ENGINE_READS["YUHAI_ZIPING"] == []
    assert ALLOWED_ENGINE_READS["SHENFENG_TONGKAO"] == [
        "YUHAI_ZIPING", "ZIPIN_ZHENQUAN", "DI_TIAN_SUI",
        "QIONGTONG_BAOJIAN", "SANMING_TONGHUI",
    ]


def test_contract_validator_rejects_bad_reads():
    from phase0.contract_validator import ContractValidator, ContractError
    import pytest as pt
    v = ContractValidator(SCHEMA_DIR / "contract.schema.json", ROOT / "engines")
    bad = {
        "engine": "YUHAI_ZIPING", "contract_version": "1.0.0", "engine_version": "0.1.0",
        "input": {"allowed_fields": ["pillars"], "allowed_engines": ["ZIPIN_ZHENQUAN"]},
        "output": {"fact_groups": ["ten_god_facts"], "judgment_fields": [], "statuses": ["PASS"]},
        "forbidden_input": [], "forbidden_output": [],
        "dependency": {"reads": []}, "approved_by": "H", "approved_at": "2026-09-15T00:00:00Z",
    }
    with pt.raises(ContractError):
        v.validate_contract_file("YUHAI_ZIPING", bad)


# ---------- Static import boundary 100% ----------

def test_static_import_scan_clean():
    assert scan_imports() == []


def test_static_import_detects_violation(tmp_path):
    from phase0.check_import_boundaries import ENGINE_MODULES, ALLOWED_IMPORTS
    # 构造违规文件：ziping 引 yuhai
    d = tmp_path / "engines" / "ziping_zhenquan"
    d.mkdir(parents=True)
    (d / "bad.py").write_text("import yuhai_ziping\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    # 重新扫描 tmp 目录
    import phase0.check_import_boundaries as m
    orig = m.SCAN_DIRS
    m.SCAN_DIRS = [tmp_path / "engines"]
    try:
        v = m.scan_files()
        assert any("ziping_zhenquan" in x and "yuhai_ziping" in x for x in v)
    finally:
        m.SCAN_DIRS = orig
        sys.path.remove(str(tmp_path))


# ---------- Runtime input boundary 100% ----------

def test_runtime_input_scan_clean():
    assert scan_runtime() == []


def test_runtime_input_detects_violation(tmp_path):
    import phase0.check_input_contracts as m
    d = tmp_path / "src" / "tongshu" / "engines" / "yuhai_ziping"
    d.mkdir(parents=True)
    (d / "bad.py").write_text('x = context["l2b"]\n', encoding="utf-8")
    orig = m.SCAN_DIRS
    m.SCAN_DIRS = [tmp_path / "src"]
    try:
        v = m.scan_files()
        assert any("yuhai_ziping" in x and "l2b" in x for x in v)
    finally:
        m.SCAN_DIRS = orig


# ---------- Forbidden symbols 100% ----------

def test_forbidden_scan_clean():
    assert scan_forbidden() == []


def test_forbidden_detects_score(tmp_path):
    import phase0.check_forbidden_symbols as m
    d = tmp_path / "engines" / "yuhai_ziping"
    d.mkdir(parents=True)
    (d / "bad.py").write_text("total_score = 90\n", encoding="utf-8")
    orig = m.SCAN_DIRS
    m.SCAN_DIRS = [tmp_path / "engines"]
    try:
        v = m.scan_files()
        assert any("total_score" in x for x in v)
    finally:
        m.SCAN_DIRS = orig


def test_forbidden_detects_llm_identifier(tmp_path):
    import phase0.check_forbidden_symbols as m
    d = tmp_path / "engines" / "yuhai_ziping"
    d.mkdir(parents=True)
    (d / "bad.py").write_text('def f():\n    llm_judgment(x)\n', encoding="utf-8")
    orig = m.SCAN_DIRS
    m.SCAN_DIRS = [tmp_path / "engines"]
    try:
        v = m.scan_files()
        assert any("llm" in x.lower() for x in v)
    finally:
        m.SCAN_DIRS = orig


# ---------- Golden permission 100% ----------

def test_golden_scan_clean():
    assert scan_golden() == []


def test_golden_agent_cannot_write():
    guard = GoldenPermissionGuard(ROOT / "governance" / "golden")
    rec = GoldenRecord("TG-001", "APPROVED", "Human")
    with pytest.raises(GoldenPermissionError):
        guard.assert_allowed(ActorRole.AGENT, GoldenAction.MODIFY, rec)
    # Agent 读/跑/报是允许的
    guard.assert_allowed(ActorRole.AGENT, GoldenAction.READ, rec)


def test_golden_registry_integrity():
    guard = GoldenPermissionGuard(ROOT / "governance" / "golden")
    problems = guard.check_registry_integrity([
        {"golden_id": "X", "status": "FROZEN", "approval_status": "NOT_APPROVED", "approved_by": None},
    ])
    assert len(problems) == 2
    assert guard.check_registry_integrity([
        {"golden_id": "Y", "status": "FROZEN", "approval_status": "APPROVED", "approved_by": "Human"},
    ]) == []


def test_technical_golden_registry_status():
    reg = json.loads((ROOT / "governance" / "golden" / "technical_golden_registry.json").read_text(encoding="utf-8"))
    ids = [g["golden_id"] for g in reg["golden_list"]]
    assert ids == [f"TG-{i:03d}" for i in range(1, 13)]
    assert all(g["approval_status"] == "APPROVED" for g in reg["golden_list"])
    assert all(g["approved_by"] == "Human Architect" for g in reg["golden_list"])


# ---------- Canonical Gate ----------

def test_canonical_gate_all_pass():
    gate = CanonicalGate()
    chart = {
        "canonical_input": {"ref": "r1"}, "frozen": True, "hash": "a" * 12,
        "time_basis": {}, "solar_term_boundary": {}, "pillars": {}, "hidden_stems": {},
        "shishen": {}, "wuxing": {}, "yinyang": {}, "nayin": {}, "xunkong": {},
        "changsheng": {}, "relations": {}, "shensha": {}, "palace_facts": {},
        "dayun": {}, "liunian": {}, "liuyue": {}, "current_relations": {},
        "recalculated": False, "charting_dependency": False,
        "schema_valid": True, "input_contract_valid": True,
    }
    summary = gate.run(chart)
    assert summary.all_passed
    assert len(summary.results) == 24


def test_canonical_gate_fail_closed():
    from shared_types.fail_closed import FailClosedError
    gate = CanonicalGate()
    chart = {"frozen": True, "hash": "a" * 12}  # 缺大多数字段
    with pytest.raises(FailClosedError):
        gate.run_or_fail(chart)
    summary = gate.run(chart)
    assert summary.fail_closed


# ---------- State model ----------

def test_state_guard_requires_evidence():
    with pytest.raises(StateModelError):
        StateGuard.require_evidence_for_judgment([])
    StateGuard.require_evidence_for_judgment(["E-YHZP-001-001"])


def test_divergence_requires_two_positions():
    assert StateGuard.divergence_requires([{"value": "A"}, {"value": "B"}])
    assert not StateGuard.divergence_requires([{"value": "A"}])
    assert not StateGuard.divergence_requires([{"value": "A"}, {"value": "A"}])
