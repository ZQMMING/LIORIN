"""Provenance Recorder（Phase 10 §40）· 多引擎。

每次运行生成 Provenance Record：engine / engine_version / contract_version /
rule_version / source_version / input_ref / rule_ids / source_ids / evidence_ids / timestamp。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from engines.common.engine_registry import ENGINE_ID_MAP, ENGINE_DIR_MAP
from shared_types.fail_closed import FailClosedReason, FailClosedError

ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ProvenanceRecorder:
    def __init__(self, engine: str = "yhzp") -> None:
        if engine not in ENGINE_ID_MAP:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知引擎: {engine}")
        self.engine = engine
        self.engine_id = ENGINE_ID_MAP[engine]
        eng_dir = ROOT / "engines" / ENGINE_DIR_MAP[engine]
        contract_path = eng_dir / "contract.json"
        if not contract_path.exists():
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"缺少 {engine} contract.json")
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.contract_version = contract["contract_version"]
        rules_path = ROOT / "registries" / "rule" / f"rules.{engine}.jsonl"
        sources_path = ROOT / "registries" / "source" / f"sources.{engine}.jsonl"
        rules = [json.loads(l) for l in rules_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        srcs = [json.loads(l) for l in sources_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.rule_version = rules[0]["version"] if rules else "0.0.0"
        self.source_version = srcs[0]["version"] if srcs else "0.0.0"
        self.engine_version = contract.get("engine_version", "0.1.0")

    def record(self, result: Any, input_ref: str, rule_ids: List[str],
               source_ids: List[str], evidence_ids: List[str]) -> Dict[str, Any]:
        return {
            "engine": self.engine_id,
            "engine_version": self.engine_version,
            "contract_version": self.contract_version,
            "rule_version": self.rule_version,
            "source_version": self.source_version,
            "input_ref": input_ref,
            "rule_ids": sorted(set(rule_ids)),
            "source_ids": sorted(set(source_ids)),
            "evidence_ids": sorted(set(evidence_ids)),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }

    def record_from_result(self, result: Any) -> Dict[str, Any]:
        rule_ids: List[str] = []
        source_ids: List[str] = []
        evidence_ids: List[str] = []
        for items in result.facts.to_dict().values():
            for f in items:
                rule_ids.append(f["rule_id"])
                source_ids.extend(f.get("source_ids", []))
                evidence_ids.extend(f.get("evidence_ids", []))
        return self.record(result, result.canonical_input.get("ref", ""),
                           rule_ids, source_ids, evidence_ids)
