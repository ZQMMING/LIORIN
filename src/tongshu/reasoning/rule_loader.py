"""RuleLoader — single source of rules (T203).

Rules live as one JSON file per rule under backend/data/rules/*.json; evidence
under backend/data/evidence/*.json. The loader validates every record against
the frozen schemas (rule.schema.json v1.1 / evidence.schema.json) at load time
— a malformed record raises, it never loads silently.

This replaces the hardcoded seed dicts previously built in pipeline.py
(`_build_seed_rule_db`), making data/rules the single source of truth.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

log = logging.getLogger(__name__)


class RuleLoadError(RuntimeError):
    """Raised when a rule / evidence record fails schema validation."""


class RuleLoader:
    """规则与证据加载器（façade 模式）。

    Args:
        data_dir: 传统 JSON 数据目录（必填。即使 source='postgres'，
            也保留作为异地落地归档。
        schema_dir: schema 文件目录（必填）。
        source: 数据源选择。
            - "json"（默认）：加载 backend/data/rules/*.json + evidence/*.json
            - "postgres"：shuntian_kb 的 rules 与 evidence 表（等 Claude C9 交付）

    公共接口 100% 向后兼容。
    """

    def __init__(
        self,
        data_dir: Path,
        schema_dir: Path,
        source: str = "json",
    ) -> None:
        if source == "json":
            from ._rule_backends import _JsonRuleBackend
            self._backend = _JsonRuleBackend(data_dir, schema_dir)
        elif source == "postgres":
            from ._rule_backends import _PostgresRuleBackend
            self._backend = _PostgresRuleBackend()
        else:
            raise ValueError(
                f"unknown RuleLoader source: {source!r} (expected 'json' | 'postgres')"
            )
        self._rules_dir = Path(data_dir) / "rules"
        self._evidence_dir = Path(data_dir) / "evidence"
        self._schema_dir = Path(schema_dir)
        self._source = source

    @staticmethod
    def _load_schema(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_rules(self) -> None:
        if not self._rules_dir.is_dir():
            raise RuleLoadError(f"rules dir missing: {self._rules_dir}")
        validator = Draft202012Validator(self._rule_schema)
        for path in sorted(self._rules_dir.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                rule = json.load(f)
            errs = sorted(validator.iter_errors(rule), key=lambda e: list(e.path))
            if errs:
                detail = errs[0].message
                raise RuleLoadError(f"{path.name}: schema invalid — {detail}")
            self._rules.append(rule)

    def _load_evidence(self) -> None:
        if not self._evidence_dir.is_dir():
            log.warning("evidence dir missing: %s (DoD #4 追溯不闭合)", self._evidence_dir)
            return
        validator = Draft202012Validator(self._evidence_schema)
        for path in sorted(self._evidence_dir.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                ev = json.load(f)
            errs = sorted(validator.iter_errors(ev), key=lambda e: list(e.path))
            if errs:
                raise RuleLoadError(f"{path.name}: evidence schema invalid — {errs[0].message}")
            self._evidence.append(ev)

    # ------------------------------------------------------------------ #
    # 公共方法委托至 backend（façade 模式）
    # ------------------------------------------------------------------ #

    @property
    def rules(self) -> list[dict]:
        return self._backend.rules

    @property
    def evidence(self) -> list[dict]:
        return self._backend.evidence

    @property
    def evidence_ids(self) -> set[str]:
        return self._backend.evidence_ids

    def get(self, rule_id: str) -> dict | None:
        return self._backend.get(rule_id)

    def verify_evidence_refs(self) -> list[str]:
        """Rules referencing evidence that has no record on disk.

        Closes UR-011 per-rule: every evidence_refs entry must resolve to a
        data/evidence/*.json record.

        委托至 backend（json 后端：本地检查；
        postgres 后端：走 DB 查询，§限制不走本地。）
        """
        return self._backend.verify_evidence_refs()
