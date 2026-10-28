"""YHZP Phase 2 验收测试（§61/§K-11）。

- contract.json 存在且符合 contract.schema.json
- contract_validator.validate_contract_file(YUHAI_ZIPING) 通过（matches approved Contract）
- Input valid / Forbidden input rejected
- Output valid / Forbidden output rejected
- validator 与 contract.json 单一来源一致
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator  # noqa: E402

from shared_types.fail_closed import FailClosedError  # noqa: E402
from phase0.contract_validator import ContractValidator  # noqa: E402
from engines.yuhai_ziping.validator import (  # noqa: E402
    YHZPInputValidator, YHZPOutputValidator, CONTRACT_PATH,
)
from engines.yuhai_ziping.result import YHZPEngineResult  # noqa: E402

ENGINE_DIR = Path(__file__).resolve().parent.parent


def _full_chart() -> dict:
    return {
        "canonical_input": {"ref": "ref-001", "hash": "a" * 12}, "frozen": True, "hash": "a" * 12,
        "time_basis": {}, "solar_term_boundary": {}, "pillars": {}, "hidden_stems": {},
        "shishen": {}, "wuxing": {}, "yinyang": {}, "nayin": {}, "xunkong": {},
        "changsheng": {}, "relations": {}, "shensha": {}, "palace_facts": {},
        "dayun": {}, "liunian": {}, "liuyue": {}, "current_relations": {},
        "recalculated": False, "charting_dependency": False,
        "schema_valid": True, "input_contract_valid": True,
    }


def _result() -> dict:
    return YHZPEngineResult(canonical_input={"ref": "ref-001", "hash": "a" * 12}).to_dict()


def test_contract_json_exists_and_schema_valid():
    assert CONTRACT_PATH.exists()
    schema = json.loads((ROOT / "shared_schema" / "contract.schema.json").read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    errors = list(v.iter_errors(contract))
    assert errors == [], f"contract.json 违反 schema: {[e.message for e in errors]}"


def test_contract_matches_approved_contract():
    v = ContractValidator(ROOT / "shared_schema" / "contract.schema.json", ENGINE_DIR.parent)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    v.validate_contract_file("YUHAI_ZIPING", contract)  # 不抛异常 = PASS


def test_contract_input_fields_aligned_with_gate():
    """contract.allowed_fields 与 CanonicalGate G-001~024 依赖一致。"""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    allowed = set(contract["input"]["allowed_fields"])
    core = {"pillars", "hidden_stems", "shishen", "wuxing", "yinyang", "nayin", "xunkong", "changsheng", "relations"}
    assert core <= allowed, "L0 core facts 必须在 allowed_fields"


def test_contract_engine_read_matrix_empty():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["input"]["allowed_engines"] == []
    assert contract["dependency"]["reads"] == []


def test_input_valid_accepts_full_chart():
    assert YHZPInputValidator().validate(_full_chart()) == "ref-001"


def test_forbidden_input_rejected():
    v = YHZPInputValidator()
    chart = _full_chart()
    chart["sxtwl"] = {}  # contract.forbidden_input
    with pytest.raises(FailClosedError):
        v.validate(chart)
    chart2 = _full_chart()
    chart2["l2b"] = {}  # §K-1 禁止读取 L2B
    with pytest.raises(FailClosedError):
        v.validate(chart2)


def test_output_valid_accepts_result():
    YHZPOutputValidator().validate(_result())


def test_forbidden_output_rejected():
    v = YHZPOutputValidator()
    d = _result()
    d["facts"]["ten_god_facts"] = [{"fact_id": "f1", "global_yongshen": "甲"}]  # §B-5
    with pytest.raises(FailClosedError):
        v.validate(d)
    d2 = _result()
    d2["facts"]["unknown_group"] = []
    with pytest.raises(FailClosedError):
        v.validate(d2)


def test_unknown_fact_group_rejected():
    v = YHZPOutputValidator()
    d = _result()
    d["facts"]["signal_facts"] = []  # 不在 contract.fact_groups
    with pytest.raises(FailClosedError):
        v.validate(d)
