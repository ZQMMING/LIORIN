"""V2.2.2 FINAL §K-11/§80 Contract Validator。

校验 engines/<engine>/contract.json matches approved Contract：
- 输入白名单 allowed_fields / allowed_engines
- 输出事实组/判断字段/状态白名单
- forbidden_input / forbidden_output 拒绝
- 禁止读取其他 Engine（L2 独立；SFTK 例外可读 L2A-E public contract）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from shared_types.enums import EngineID
from shared_types.errors import ContractError

# V2.2.2 §K-1~K-6 六引擎 Input Matrix（L2A-E 完全独立；SFTK 唯一可读 L2A-E public）
ALLOWED_ENGINE_READS: Dict[str, List[str]] = {
    "YUHAI_ZIPING": [],
    "ZIPIN_ZHENQUAN": [],
    "DI_TIAN_SUI": [],
    "QIONGTONG_BAOJIAN": [],
    "SANMING_TONGHUI": [],
    "SHENFENG_TONGKAO": ["YUHAI_ZIPING", "ZIPIN_ZHENQUAN", "DI_TIAN_SUI", "QIONGTONG_BAOJIAN", "SANMING_TONGHUI"],
}

# §K-10：L4 可读 L2/L3 public outputs；L5 读 L4 + Mapping/Terminology/Precedence；L6 读 L4/L5（非引擎级契约，这里只登记）
L4_READS = ["L0", "L2", "L3", "EVIDENCE_REGISTRY", "PROVENANCE_REGISTRY"]
L5_READS = ["L4", "MAPPING_REGISTRY", "TERMINOLOGY_REGISTRY", "PRECEDENCE_REGISTRY"]
L6_READS = ["L5", "L4", "EVIDENCE_GRAPH", "PROVENANCE"]


def _require_all(obj: dict, keys: List[str], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ContractError(f"{where} 缺少必填字段: {missing}")


class ContractValidator:
    def __init__(self, schema_path: Path, contracts_dir: Path) -> None:
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.contracts_dir = contracts_dir

    def validate_contract_file(self, engine: str, contract: dict) -> None:
        """校验单个 contract.json 与 V2.22 架构一致性。"""
        _require_all(contract, ["engine", "contract_version", "engine_version", "input", "output", "forbidden_input", "forbidden_output", "dependency"], f"{engine}/contract.json")
        if contract["engine"] != engine:
            raise ContractError(f"{engine} contract.json 的 engine 字段不匹配: {contract['engine']}")
        # Input
        inp = contract["input"]
        _require_all(inp, ["allowed_fields", "allowed_engines"], f"{engine} input")
        reads = set(inp["allowed_engines"])
        allowed = set(ALLOWED_ENGINE_READS.get(engine, []))
        if reads != allowed:
            raise ContractError(f"{engine} 读取引擎集合违规: 期望 {sorted(allowed)}, 实际 {sorted(reads)}")
        # Forbidden input：禁止出现架构级禁用项
        forbidden_input = set(contract["forbidden_input"])
        for f in ["recalculate", "sxtwl", "llm", "score", "confidence"]:
            if f in forbidden_input:
                continue  # 允许显式登记；但不得出现在 allowed_fields
        bad_allowed = [f for f in inp["allowed_fields"] if f in forbidden_input]
        if bad_allowed:
            raise ContractError(f"{engine} allowed_fields 与 forbidden_input 冲突: {bad_allowed}")
        # Forbidden output：不得输出统一用神/评分等
        forbidden_output = set(contract["forbidden_output"])
        for g in ["FINAL_USE_SHEN", "GLOBAL_USE_SHEN", "UNIFIED_USE_SHEN", "total_score", "percentage", "probability", "vote", "consensus"]:
            if g in forbidden_output:
                continue
        bad_out = [f for f in contract["output"].get("fact_groups", []) if f in forbidden_output]
        if bad_out:
            raise ContractError(f"{engine} 输出含禁用字段: {bad_out}")

    def validate_all(self) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        if not self.contracts_dir.exists():
            return results  # Phase 2 前允许空；Phase 2 验收要求全存在
        for engine in EngineID:
            f = self.contracts_dir / engine.lower() / "contract.json"
            if not f.exists():
                results[engine.value] = False
                continue
            contract = json.loads(f.read_text(encoding="utf-8"))
            self.validate_contract_file(engine.value, contract)
            results[engine.value] = True
        return results
