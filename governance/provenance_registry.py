"""V2.2.2 FINAL §40/§57 Provenance Registry 骨架。

Provenance 至少记录：engine/engine_version/contract_version/rule_version/source_version/
input_ref/rule_ids/source_ids/evidence_ids/timestamp。
可移植、可审计；禁止开发机绝对路径。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from jsonschema import Draft202012Validator

from shared_types.errors import RegistryError

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "shared_schema" / "provenance.schema.json"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProvenanceRegistry:
    def __init__(self, storage: Path) -> None:
        self.storage = storage
        self.storage.mkdir(parents=True, exist_ok=True)
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(schema)
        self._records: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        f = self.storage / "provenance_registry.jsonl"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._records[rec["provenance_id"]] = rec

    def record(self, entry: dict) -> str:
        """录入 Provenance；要求 timestamp 存在，rule/source/evidence 可追溯。"""
        entry.setdefault("timestamp", utcnow_iso())
        errors = list(self.validator.iter_errors(entry))
        if errors:
            raise RegistryError(f"Provenance 违反 Schema: {errors[0].message}")
        if entry["provenance_id"] in self._records:
            raise RegistryError(f"Provenance {entry['provenance_id']} 重复")
        self._records[entry["provenance_id"]] = entry
        with open(self.storage / "provenance_registry.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["provenance_id"]

    def get(self, provenance_id: str) -> Optional[dict]:
        return self._records.get(provenance_id)

    def all(self) -> List[dict]:
        return list(self._records.values())
