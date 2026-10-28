"""Judgment Builder（Phase 7 §66）。

- Fact → Rule → Evidence → Judgment 链；没有证据 → UNKNOWN，禁止 Agent 自行推断
- assertions：对 facts 的纯组装陈述（不产生新 Fact/新判断，§41 Evidence Graph：Assertion ← Judgment/Fact）
- YHZP 正式 Registry 无 judgment 类规则（340 条全 definition/activation）→
  judgments 为空是合法状态；机制由测试用构造规则验证
"""

from __future__ import annotations

from typing import Any, Dict, List

from engines.yuhai_ziping.result import YHZPEngineResult

GROUP_LABEL = {
    "ten_god_facts": "十神",
    "six_relative_facts": "六亲",
    "palace_facts": "宫位",
    "basic_structure_facts": "基础结构",
    "geju_candidates": "格局候选",
    "relation_facts": "关系",
}


def build_assertions(result: YHZPEngineResult) -> List[Dict[str, Any]]:
    """把六组 facts 组装为 assertions（结构化陈述，纯表达层）。"""
    assertions: List[Dict[str, Any]] = []
    for group, items in result.facts.to_dict().items():
        label = GROUP_LABEL.get(group, group)
        for f in items:
            assertions.append({
                "assertion_id": f"AST-{len(assertions) + 1:04d}",
                "fact_id": f["fact_id"],
                "group": group,
                "statement": f"{label}：{f['field']} = {f['value']}",
                "source_ids": f.get("source_ids", []),
                "evidence_ids": f.get("evidence_ids", []),
            })
    return assertions


class JudgmentBuilder:
    """Judgment 链验证器 + 组装器。

    YHZP 无 judgment 规则 → build() 返回空 judgments；
    若传入 judgment 规则（Human 审批后），逐条验证 Fact→Rule→Evidence 链，
    断链/无证据 → 不产 judgment（UNKNOWN 语义）。
    """

    def __init__(self) -> None:
        self.rule_engine = None  # Phase 7 无 judgment 规则源，预留

    def build(self, result: YHZPEngineResult) -> List[Dict[str, Any]]:
        """当前 YHZP Registry 无 judgment 规则 → 返回空（不臆造）。"""
        return []

    def validate_judgment(self, judgment: Dict[str, Any], result: YHZPEngineResult) -> bool:
        """链完整性：judgment 必须引用存在的 fact 且该 fact 有证据；否则 False（→UNKNOWN）。"""
        fact_ids = judgment.get("fact_ids") or []
        if not fact_ids:
            return False
        all_facts = []
        for items in result.facts.to_dict().values():
            all_facts.extend(items)
        by_id = {f["fact_id"]: f for f in all_facts}
        for fid in fact_ids:
            f = by_id.get(fid)
            if f is None:
                return False
            if not f.get("evidence_ids"):
                return False
        return True
