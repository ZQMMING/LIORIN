"""V2.2.2 FINAL §E-1/§57 Phase 0 Validator: validate_schemas.py

校验 shared_schema/ 下全部 JSON Schema：
1. JSON 语法合法
2. 使用 JSON Schema Draft 2020-12
3. 含 $id / $schema
4. 用 jsonschema 编译（Draft 2020-12 valid）
5. 关键 Schema 用正反样例实例验证（Schema validation works）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

# 使 CLI 可直接运行（python phase0/validate_schemas.py）
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from jsonschema import Draft202012Validator, ValidationError

from shared_types.errors import SchemaValidationError

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "shared_schema"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

REQUIRED_SCHEMAS = [
    "fact.schema.json", "assertion.schema.json", "rule.schema.json",
    "signal.schema.json", "divergence.schema.json", "engine_result.schema.json",
    "gap_report.schema.json", "source.schema.json", "evidence.schema.json",
    "judgment.schema.json", "provenance.schema.json", "contract.schema.json",
    "precedence.schema.json",
]

# 正反样例（schema 文件名 -> (合法实例, 非法实例)）
SAMPLE_INSTANCES: Dict[str, tuple] = {
    "source.schema.json": (
        {
            "source_id": "YHZP-001-001", "engine": "YUHAI_ZIPING", "book": "渊海子平",
            "chapter": "論五行所生之始", "text_id": "YHZP-T-001-001",
            "text_layer": "ORIGINAL", "source_text": "蓋聞天地未判，其名混沌；乾坤未分，是名胚腪。",
            "resource_id": "SRC-YHZP-001", "logical_uri": "source://yhzp/001/001",
            "relative_path": "sources/yhzp/chapter_001.md", "version": "1.0.0",
            "status": "CANDIDATE", "evidence_grade": "A",
        },
        {
            "source_id": "YHZP-001-001", "engine": "YUHAI_ZIPING", "book": "渊海子平",
            "chapter": "論五行所生之始", "text_id": "YHZP-T-001-001",
            "text_layer": "MODERN",  # 非法枚举
            "source_text": "x", "resource_id": "SRC-YHZP-001",
            "logical_uri": "source://yhzp/001/001", "relative_path": "sources/yhzp/chapter_001.md",
            "version": "1.0.0", "status": "CANDIDATE",
        },
    ),
    "rule.schema.json": (
        {
            "rule_id": "YHZP-001", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-003-001"],
            "rule_type": "definition", "scope": "natal", "subject": "stem_he", "predicate": "is",
            "preconditions": {"type": "conjunction", "conditions": [{"field": "stem", "operator": "equals", "value": "甲"}]},
            "operator": "emit", "output": {"field": "stem_he", "value": "甲己"},
            "evidence_requirement": "A", "version": "0.1.0", "status": "CANDIDATE",
        },
        {
            "rule_id": "YHZP-001", "engine": "YUHAI_ZIPING", "source_ids": ["YHZP-003-001"],
            "rule_type": "definition", "scope": "natal", "subject": "s", "predicate": "is",
            "preconditions": {"type": "conjunction", "conditions": [{"field": "s", "operator": "greater_than", "value": 1}]},  # 非法算子
            "operator": "emit", "output": {"field": "f", "value": "v"}, "version": "0.1.0", "status": "CANDIDATE",
        },
    ),
    "evidence.schema.json": (
        {
            "evidence_id": "E-YHZP-001-001", "source_id": "YHZP-001-001",
            "source_location": "卷一·論五行所生之始", "text_layer": "ORIGINAL",
            "evidence_grade": "A", "rule_id": "YHZP-001", "fact_ids": ["F-YHZP-001-001"],
        },
        {
            "evidence_id": "E-YHZP-001-001", "source_id": "YHZP-001-001",
            "source_location": "x", "text_layer": "ORIGINAL",
            "evidence_grade": "A+",  # 非法等级
            "rule_id": "YHZP-001", "fact_ids": [],
        },
    ),
}


def validate_all() -> Dict[str, List[str]]:
    """返回 {schema 文件名: [错误信息]}；空列表=通过。"""
    errors: Dict[str, List[str]] = {}
    for name in REQUIRED_SCHEMAS:
        path = SCHEMA_DIR / name
        if not path.exists():
            errors[name] = ["文件缺失"]
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors[name] = [f"JSON 语法错误: {exc}"]
            continue
        errs: List[str] = []
        if schema.get("$schema") != DRAFT_2020_12:
            errs.append(f"$schema 不是 Draft 2020-12: {schema.get('$schema')}")
        if not schema.get("$id"):
            errs.append("缺少 $id")
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001
            errs.append(f"Schema 校验失败: {exc}")
        if name in SAMPLE_INSTANCES:
            good, bad = SAMPLE_INSTANCES[name]
            v = Draft202012Validator(schema)
            if v.is_valid(good) is False:
                errs.append("正例校验未通过")
            if v.is_valid(bad) is True:
                errs.append("反例未被拒绝")
        if errs:
            errors[name] = errs
    return errors


def main() -> int:
    errors = validate_all()
    if not errors:
        print(f"validate_schemas PASS ({len(REQUIRED_SCHEMAS)} schemas, Draft 2020-12, 正反例全部通过)")
        return 0
    for name, errs in errors.items():
        for e in errs:
            print(f"FAIL {name}: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
