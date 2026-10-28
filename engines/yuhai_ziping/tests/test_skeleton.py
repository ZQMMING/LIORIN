"""YHZP Phase 1 Skeleton 测试（§60：Skeleton PASS 才能进 Phase 2）。

不涉及业务 Rule；只验证 package/result/validator 骨架。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared_types.enums import EngineStatus  # noqa: E402
from shared_types.fail_closed import FailClosedError  # noqa: E402
from engines.yuhai_ziping import ENGINE_ID, ENGINE_VERSION, CONTRACT_VERSION  # noqa: E402
from engines.yuhai_ziping.result import YHZPEngineResult, YHZPFactGroups  # noqa: E402
from engines.yuhai_ziping.validator import YHZPInputValidator, YHZPOutputValidator  # noqa: E402


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


def test_package_identity():
    assert ENGINE_ID == "YUHAI_ZIPING"
    assert ENGINE_VERSION == "0.1.0"
    assert CONTRACT_VERSION == "0.1.0"


def test_skeleton_dirs_exist():
    base = Path(__file__).resolve().parent.parent
    for d in ["calculation", "rule", "judgment", "evidence", "signal", "golden", "regression", "provenance", "production"]:
        assert (base / d).is_dir(), f"缺少目录 {d}"


def test_result_structure():
    r = YHZPEngineResult()
    d = r.to_dict()
    assert d["engine"] == "YUHAI_ZIPING"
    assert d["status"] == "PASS"
    assert set(d["facts"].keys()) == {
        "ten_god_facts", "six_relative_facts", "palace_facts",
        "basic_structure_facts", "geju_candidates", "relation_facts",
    }
    assert d["assertions"] == [] and d["signals"] == []


def test_input_validator_accepts_full_chart():
    v = YHZPInputValidator()
    ref = v.validate(_full_chart())
    assert ref == "ref-001"


def test_input_validator_fail_closed_on_missing():
    v = YHZPInputValidator()
    with pytest.raises(FailClosedError):
        v.validate({})  # 缺 canonical_input


def test_input_validator_rejects_rechart():
    v = YHZPInputValidator()
    chart = _full_chart()
    chart["recalculated"] = True
    with pytest.raises(FailClosedError):
        v.validate(chart)


def test_output_validator_accepts_empty_result():
    v = YHZPOutputValidator()
    r = YHZPEngineResult(canonical_input={"ref": "ref-001", "hash": "a" * 12})
    v.validate(r.to_dict())


def test_output_validator_rejects_bad_status():
    v = YHZPOutputValidator()
    d = YHZPEngineResult(canonical_input={"ref": "ref-001", "hash": "a" * 12}).to_dict()
    d["status"] = "SCORED"  # 非法
    with pytest.raises(FailClosedError):
        v.validate(d)


def test_output_validator_rejects_forbidden_field():
    v = YHZPOutputValidator()
    d = YHZPEngineResult(canonical_input={"ref": "ref-001", "hash": "a" * 12}).to_dict()
    d["facts"]["ten_god_facts"] = [{"fact_id": "f1", "global_yongshen": "甲"}]
    with pytest.raises(FailClosedError):
        v.validate(d)
