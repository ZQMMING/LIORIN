"""Rule Engine（Phase 4 §63）：消费正式 RuleRegistry，纯规则解释器（多引擎）。

- preconditions 匹配（§46 白名单算子 equals/in/not_in/exists/not_exists + conjunction/disjunction 一层）
- operator=emit：匹配时输出 output fact（§45）；require/suppress 供上层（Phase 7+）使用
- 关键失败 FAIL_CLOSED（§72），不继续向下游传播
- 多引擎：RuleEngine(engine="yhzp") 加载 registries/rule/rules.{engine}.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from shared_types.fail_closed import FailClosedReason, FailClosedError

ROOT = Path(__file__).resolve().parent.parent.parent.parent
RULES_DIR = ROOT / "registries" / "rule"
SOURCES_DIR = ROOT / "registries" / "source"

GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


def _field_value(chart: Dict[str, Any], field: str) -> Any:
    """点路径取值（如 'pillars.day_stem'）；不存在返回 _MISSING。"""
    cur: Any = chart
    for part in field.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


_MISSING = object()


def _eval_condition(chart: Dict[str, Any], cond: Dict[str, Any]) -> bool:
    op = cond["operator"]
    field = cond["field"]
    value = cond.get("value", _MISSING)
    actual = _field_value(chart, field)
    if op == "equals":
        return actual is not _MISSING and actual == value
    if op == "in":
        if not isinstance(value, list):
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, "in 算子 value 必须为列表")
        if isinstance(actual, list):
            return any(x in value for x in actual)  # 多值字段：任一命中
        return actual is not _MISSING and actual in value
    if op == "not_in":
        if not isinstance(value, list):
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, "not_in 算子 value 必须为列表")
        if isinstance(actual, list):
            return not any(x in value for x in actual)
        return actual is not _MISSING and actual not in value
    if op == "exists":
        return actual is not _MISSING and actual is not None and actual != ""
    if op == "not_exists":
        return actual is _MISSING or actual is None or actual == ""
    raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知算子: {op}")


def _eval_preconditions(chart: Dict[str, Any], pre: Dict[str, Any]) -> bool:
    agg = pre.get("type", "conjunction")
    results = [_eval_condition(chart, c) for c in pre.get("conditions", [])]
    if agg == "conjunction":
        return all(results)
    if agg == "disjunction":
        return any(results)
    raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知聚合: {agg}")


class RuleEngine:
    """加载正式 RuleRegistry（按 engine 参数化），对 L0 chart 执行匹配。"""

    def __init__(self, engine: str = "yhzp") -> None:
        rules_path = RULES_DIR / f"rules.{engine}.jsonl"
        sources_path = SOURCES_DIR / f"sources.{engine}.jsonl"
        if not rules_path.exists() or not sources_path.exists():
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"缺少 {engine} Registry 文件")
        self.engine = engine
        self.rules: List[Dict[str, Any]] = [
            json.loads(l) for l in rules_path.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        self.source_grade: Dict[str, str] = {}
        for l in sources_path.read_text(encoding="utf-8").splitlines():
            if l.strip():
                s = json.loads(l)
                self.source_grade[s["source_id"]] = s["evidence_grade"]
        self._compile()

    def _compile(self) -> None:
        """编译期校验：全部规则算子/operator/绑定合法；不合法即 FAIL_CLOSED。"""
        allowed_ops = {"equals", "in", "not_in", "exists", "not_exists"}
        allowed_aggs = {"conjunction", "disjunction"}
        seen = set()
        for r in self.rules:
            rid = r["rule_id"]
            if rid in seen:
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"重复 rule_id: {rid}")
            seen.add(rid)
            if r.get("operator") not in {"emit", "require", "suppress"}:
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法 operator: {r.get('operator')} @ {rid}")
            pre = r.get("preconditions", {})
            if pre.get("type") not in allowed_aggs:
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法聚合: {pre.get('type')} @ {rid}")
            for c in pre.get("conditions", []):
                if c.get("operator") not in allowed_ops:
                    raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"非法算子: {c.get('operator')} @ {rid}")
            missing = [sid for sid in r.get("source_ids", []) if sid not in self.source_grade]
            if missing:
                raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"Rule 无 Source 绑定: {missing} @ {rid}")

    def _best_grade(self, source_ids: List[str]) -> str:
        grades = [self.source_grade[sid] for sid in source_ids if sid in self.source_grade]
        if not grades:
            raise FailClosedError(FailClosedReason.CONTRACT_INVALID, "无可用证据等级")
        return max(grades, key=lambda g: GRADE_RANK[g])

    def run(self, chart: Dict[str, Any]) -> List[Dict[str, Any]]:
        """对 chart 执行全部 emit 规则；返回 fact 列表（含证据链）。"""
        facts: List[Dict[str, Any]] = []
        for r in self.rules:
            if r.get("operator") != "emit":
                continue
            if not _eval_preconditions(chart, r["preconditions"]):
                continue
            outputs = r["output"] if isinstance(r["output"], list) else [r["output"]]
            for out in outputs:
                facts.append({
                    "rule_id": r["rule_id"],
                    "source_ids": r["source_ids"],
                    "evidence_grade": self._best_grade(r["source_ids"]),
                    "field": out["field"],
                    "value": out["value"],
                })
        return facts
