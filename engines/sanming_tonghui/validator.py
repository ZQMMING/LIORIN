"""YHZP Input/Output Validator（Phase 2：以 contract.json 为单一权威来源）。

输入：Frozen Canonical Bazi Chart 引用（§3：MUST consume / MUST NOT modify / MUST NOT re-chart）。
契约来源：engines/yuhai_ziping/contract.json（Human-approved Contract，V2.2.2 附录 B）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

from shared_types.enums import EngineStatus
from shared_types.fail_closed import FailClosedReason, FailClosedError
from phase0.canonical_gate import CanonicalGate

ENGINE_DIR = Path(__file__).resolve().parent
ENGINES_DIR = ENGINE_DIR.parent.parent
CONTRACT_PATH = ENGINE_DIR / "contract.json"


class _ContractLoader:
    """contract.json 加载器（缓存 + 缺失即 FAIL_CLOSED）。"""

    _cache: Dict[str, dict] = {}

    @classmethod
    def load(cls) -> dict:
        key = str(CONTRACT_PATH)
        if key not in cls._cache:
            if not CONTRACT_PATH.exists():
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"缺少 {key}")
            cls._cache[key] = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        return cls._cache[key]


class YHZPInputValidator:
    """输入校验：只接受 Frozen Canonical Bazi Chart；按 contract.json allowed_fields 白名单。"""

    def __init__(self) -> None:
        self.gate = CanonicalGate()
        self.contract = _ContractLoader.load()
        self.allowed_fields = set(self.contract["input"]["allowed_fields"])
        self.forbidden_input = set(self.contract["forbidden_input"])

    def validate(self, canonical_chart: Dict[str, Any]) -> str:
        """返回 canonical_input ref；Gate 或契约违规 → FAIL_CLOSED。"""
        if not isinstance(canonical_chart, dict):
            raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, "canonical_chart 非字典")
        ref = canonical_chart.get("canonical_input", {}).get("ref")
        if not ref:
            raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, "缺少 canonical_input.ref")
        # §3.4 / contract.forbidden_input：禁用输入字段。
        # 布尔标志类（recalculated/charting_dependency）只在为 True 时拒绝；
        # 结构类（sxtwl/l2b/score 等）存在即违规。
        bool_flags = {"recalculated", "charting_dependency"}
        for key in canonical_chart:
            if key in bool_flags:
                if canonical_chart[key] is True:
                    raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, f"禁用输入标志: {key}")
            elif key in self.forbidden_input or key.startswith("l2") or key == "l3":
                raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, f"禁用输入字段: {key}")
        summary = self.gate.run_or_fail(canonical_chart)
        if not summary.all_passed:
            raise FailClosedError(FailClosedReason.CANONICAL_GATE, f"Gate 未全过: {summary.failed_gates}")
        return ref


class YHZPOutputValidator:
    """输出校验：EngineResult 必须符合 §70 结构、fact_groups 白名单且无禁用输出（contract.forbidden_output）。"""

    def __init__(self) -> None:
        schema_path = ENGINES_DIR / "shared_schema" / "engine_result.schema.json"
        self.validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        self.contract = _ContractLoader.load()
        self.allowed_fact_groups = set(self.contract["output"]["fact_groups"])
        self.forbidden_output = set(self.contract["forbidden_output"])

    def validate(self, result_dict: Dict[str, Any]) -> None:
        errors = list(self.validator.iter_errors(result_dict))
        if errors:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"EngineResult 违反 Schema: {errors[0].message}")
        facts = result_dict.get("facts", {})
        if isinstance(facts, dict):
            unknown = [g for g in facts if g not in self.allowed_fact_groups]
            if unknown:
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知 fact 组: {unknown}")
            for group, items in facts.items():
                for item in items:
                    if isinstance(item, dict):
                        bad = [f for f in self.forbidden_output if f in {k.upper() for k in item.keys()} or f.lower() in {k.lower() for k in item.keys()}]
                        if bad:
                            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"输出含禁用字段: {bad}")
        if result_dict.get("status") not in set(self.contract["output"]["statuses"]):
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法 status: {result_dict.get('status')}")
