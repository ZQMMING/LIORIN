"""Regression Harness（Phase 8 §67）。

基线快照：样例命盘 → FactsBuilder 输出 → 规范化快照（JSON）。
回归对比：重跑 → diff → report（新增/删除/变更 fact 数）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SNAPSHOT_DIR = ROOT / "engines" / "yuhai_ziping" / "regression" / "snapshots"

DEMO_CHART: Dict[str, Any] = {
    "canonical_input": {"ref": "ref-demo-001", "hash": "a" * 12},
    "pillars": {
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "丙", "branch": "寅"},
        "day": {"stem": "甲", "branch": "午"},
        "hour": {"stem": "戊", "branch": "午"},
    },
    "gender": "男", "xunkong": {"xun": "甲午旬"},
    "shishen": {"day_branch_hidden": ["丁"]},
    "changsheng": {}, "nayin": {}, "relations": {},
}


def normalize(facts_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """规范化：只保留判定相关键，排序（稳定快照）。"""
    keys = ["rule_id", "field", "value", "context", "source_ids", "evidence_ids", "evidence_grade"]
    out = []
    for f in facts_list:
        out.append({k: f[k] for k in keys if k in f})
    out.sort(key=lambda x: (x["rule_id"], x["context"], str(x["value"])))
    return out


def snapshot_all(result: Any) -> Dict[str, List[Dict[str, Any]]]:
    return {g: normalize(items) for g, items in result.facts.to_dict().items()}


def capture(snapshot_path: Path) -> Dict[str, Any]:
    """生成基线快照文件。"""
    from engines.yuhai_ziping.calculation.facts_builder import FactsBuilder
    result = FactsBuilder().build(DEMO_CHART)
    snap = snapshot_all(result)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def compare(baseline: Dict[str, List[Dict[str, Any]]], current: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """diff 两个快照 → 回归报告。"""
    report: Dict[str, Any] = {"groups": {}}
    for g in baseline:
        b = {json.dumps(x, ensure_ascii=False) for x in baseline[g]}
        c = {json.dumps(x, ensure_ascii=False) for x in current.get(g, [])}
        report["groups"][g] = {
            "baseline": len(b),
            "current": len(c),
            "added": len(c - b),
            "removed": len(b - c),
        }
    report["pass"] = all(v["added"] == 0 and v["removed"] == 0 for v in report["groups"].values())
    return report
