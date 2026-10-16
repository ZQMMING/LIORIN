"""
P1.2-B.1 — JudgmentRuleLibrary（AuthorizedJudgmentRule）

设计原则：
  1. Judgment 必须由原典授权规则产生，禁止"聚合即判断"
  2. EvidenceCoverage 只做结构性组织，不产生 Judgment
  3. 规则从 JSON 文件加载，支持热更新
  4. 禁止 evidence_count 作为 Judgment 触发条件（避免隐性投票）
  5. Judgment 条件必须是显式原典授权（多源互补结构、时序条件等）
"""
from __future__ import annotations

import enum
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..spec.canonical import EvidenceCoverage, EvidenceRef
from .assertion_rule_library import RuleProvenance

logger = logging.getLogger(__name__)


class JudgmentCondition(str, enum.Enum):
    """Judgment 授权条件类型。

    禁止使用 evidence_count 阈值驱动 Judgment，所有条件必须来自原典授权。
    """
    MULTI_SOURCE = "MULTI_SOURCE"       # 多引擎互补（各体系独立证据）
    TEMPORAL = "TEMPORAL"              # 时序条件（大运/流年/流月叠加）
    ATTRIBUTE = "ATTRIBUTE"            # 属性条件（特定 attributes 组合）
    GRAPH = "GRAPH"                    # 关系图条件（多个 Atom 关联）
    SINGLE_SOURCE_AUTHORIZED = "SINGLE_SOURCE_AUTHORIZED"  # 单源但原典明确授权


@dataclass(frozen=True)
class JudgmentRule:
    """授权判断规则：决定何时 EvidenceCoverage 升级为 Judgment。

    authorized_by 字段即为 Judgment.authorized_by 的值。
    注意：禁止使用 evidence_count 作为判断依据。
    """

    rule_id: str
    domain: str
    semantic: str
    condition_type: JudgmentCondition
    condition: Dict[str, Any]  # 结构化条件（见各 JudgmentCondition 说明）
    provenance: RuleProvenance  # 原典溯源

    @property
    def canonical_source(self) -> str:
        """兼容旧字段：返回工作名+章节的字符串摘要。"""
        if self.provenance.source_chapter:
            return f"{self.provenance.source_work}·{self.provenance.source_chapter}"
        return self.provenance.source_work


class JudgmentRuleLibrary:
    """授权判断规则库。

    从 JSON 文件加载规则，提供 find_judgment / list_rules 接口。
    """

    def __init__(self, rules: Optional[List[JudgmentRule]] = None):
        self._rules: List[JudgmentRule] = rules or []

    def find_judgment(self, coverage: EvidenceCoverage) -> Optional[JudgmentRule]:
        """根据 EvidenceCoverage 匹配授权规则。

        匹配逻辑（按优先级）：
        1. domain + semantic 必须精确匹配
        2. condition_type 对应的条件检查

        注意：evidence_count 不作为判断依据，仅记录覆盖面。

        Args:
            coverage: EvidenceCoverage 对象

        Returns:
            匹配的 JudgmentRule；None 表示无授权
        """
        for rule in self._rules:
            if rule.domain != coverage.domain:
                continue
            if rule.semantic != coverage.semantic:
                if not self._match_condition(rule, coverage):
                    continue
                return rule
        return None

    def _match_condition(
        self, rule: JudgmentRule, coverage: EvidenceCoverage
    ) -> bool:
        cond = rule.condition
        cond_type = rule.condition_type

        try:
            if cond_type == JudgmentCondition.MULTI_SOURCE:
                # 多引擎互补：source_engines 必须包含 condition["engines"] 中指定的引擎
                required_engines = set(cond.get("engines", []))
                if not required_engines:
                    return False
                return required_engines.issubset(set(coverage.source_engines))

            elif cond_type == JudgmentCondition.TEMPORAL:
                # TEMPORAL: 时序条件（NOT_IMPLEMENTED — placeholder）
                # TODO: 实现真正的时序匹配（需要从 assertion_ids 反查 temporal 信息）
                raise NotImplementedError(
                    f"JudgmentCondition.TEMPORAL 尚未实现，rule_id={rule.rule_id}"
                )

            elif cond_type == JudgmentCondition.ATTRIBUTE:
                # ATTRIBUTE: 属性条件（NOT_IMPLEMENTED — placeholder）
                # TODO: 实现真正的属性匹配（需要从 assertion_ids 反查 attributes）
                raise NotImplementedError(
                    f"JudgmentCondition.ATTRIBUTE 尚未实现，rule_id={rule.rule_id}"
                )

            elif cond_type == JudgmentCondition.GRAPH:
                # GRAPH: 关系图条件（NOT_IMPLEMENTED — placeholder）
                # TODO: 实现真正的图结构匹配
                raise NotImplementedError(
                    f"JudgmentCondition.GRAPH 尚未实现，rule_id={rule.rule_id}"
                )

            elif cond_type == JudgmentCondition.SINGLE_SOURCE_AUTHORIZED:
                # 单源但原典明确授权：不要求多引擎，但必须有 canonical_source
                return bool(rule.canonical_source)

        except (KeyError, TypeError):
            logger.warning(
                "JudgmentCondition %s failed for rule %s", cond_type, rule.rule_id
            )
            return False

        return False

    def list_rules(self) -> List[JudgmentRule]:
        """列出所有规则。"""
        return list(self._rules)

    @staticmethod
    def load(path: str) -> "JudgmentRuleLibrary":
        """从 JSON 文件加载规则库。

        JSON 格式（禁止使用 required_evidence_count）：
        {
          "_meta": {"version": "1.0", "description": "..."},
          "rules": [
            {
              "rule_id": "JUD-001",
              "domain": "CAREER",
              "semantic": "OUTPUT_ACTIVATION",
              "condition_type": "MULTI_SOURCE",
              "condition": {"engines": ["ZI_PING", "BLIND_SCHOOL"]},
              "canonical_source": "滴天髓·食神章"
            },
            {
              "rule_id": "JUD-002",
              "domain": "FINANCE",
              "semantic": "WEALTH_FLOW",
              "condition_type": "SINGLE_SOURCE_AUTHORIZED",
              "condition": {},
              "canonical_source": "子平真诠·论财星"
            }
          ]
        }
        """
        path_obj = Path(path)
        if not path_obj.exists():
            logger.warning("JudgmentRuleLibrary: rules file not found: %s", path)
            return JudgmentRuleLibrary()

        with open(path_obj, encoding="utf-8") as f:
            data = json.load(f)

        rules = []
        for rule_dict in data.get("rules", []):
            prov_dict = rule_dict.get("provenance", {})
            provenance = RuleProvenance(
                source_work=prov_dict.get("source_work", rule_dict.get("canonical_source", "")),
                source_chapter=prov_dict.get("source_chapter", ""),
                passage_ref=prov_dict.get("passage_ref", ""),
                verification_status=prov_dict.get("verification_status", "unverified"),
                verified_by=prov_dict.get("verified_by", ""),
                verification_version=prov_dict.get("verification_version", ""),
            )
            rules.append(
                JudgmentRule(
                    rule_id=rule_dict["rule_id"],
                    domain=rule_dict["domain"],
                    semantic=rule_dict["semantic"],
                    condition_type=JudgmentCondition(rule_dict["condition_type"]),
                    condition=rule_dict.get("condition", {}),
                    provenance=provenance,
                )
            )

        logger.info("JudgmentRuleLibrary: loaded %d rules from %s", len(rules), path)
        return JudgmentRuleLibrary(rules)
