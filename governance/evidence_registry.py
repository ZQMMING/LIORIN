"""V2.2.2 FINAL §39/§57 Evidence Registry 骨架。

Evidence Record 至少包括：evidence_id/source_id/source_location/text_layer/evidence_grade/rule_id/fact_ids。
Evidence 不得脱离 Source；是证据质量描述，不是概率。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from jsonschema import Draft202012Validator

from shared_types.errors import RegistryError

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "shared_schema" / "evidence.schema.json"


class EvidenceRegistry:
    def __init__(self, storage: Path) -> None:
        self.storage = storage
        self.storage.mkdir(parents=True, exist_ok=True)
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(schema)
        self._records: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        f = self.storage / "evidence_registry.jsonl"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._records[rec["evidence_id"]] = rec

    def add(self, record: dict, source_ids_known: set) -> str:
        """录入 Evidence；要求 source 已知（Evidence 不得脱离 Source，§39）。"""
        errors = list(self.validator.iter_errors(record))
        if errors:
            raise RegistryError(f"Evidence 违反 Schema: {errors[0].message}")
        if record["source_id"] not in source_ids_known:
            raise RegistryError(f"Evidence {record['evidence_id']} 引用的 Source {record['source_id']} 不存在")
        if record["evidence_id"] in self._records:
            raise RegistryError(f"Evidence {record['evidence_id']} 重复")
        self._records[record["evidence_id"]] = record
        with open(self.storage / "evidence_registry.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record["evidence_id"]

    def get(self, evidence_id: str) -> Optional[dict]:
        return self._records.get(evidence_id)

    def all(self) -> List[dict]:
        return list(self._records.values())
