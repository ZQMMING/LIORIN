"""H12: Heluo Diagnosis Rule Graph（河洛诊断规则图）

职责：
  将 EngineEvidence + EVENT_SIGNAL 组合为规则图，
  输出 CanonicalAssertion 列表和 EvidenceCoverage。

设计原则：
  1. 不产生新方向：仅引用 EngineEvidence 的 rule_id + EVENT_SIGNAL 的 direction
  2. 原典授权：每个规则节点标注原典出处
  3. 互补不比较：多个证据来自不同维度时，保留全部，不做投票/加权
  4. 禁止"聚合成群即判断"：需经 Authorized Judgment Rule 授权才产生 Judgment

V13 §二对齐：
  EngineEvidence → RuleGraph → CanonicalAssertion → EvidenceCoverage → Judgment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...spec.canonical import (
    EngineEvidence,
    CanonicalAssertion,
    AssertionDirection,
    EvidenceRef,
    EvidenceCoverage,
    Judgment,
)
from ..heluo.hua_gong import HuaGongState


# ═══════════════════════════════════════════════════════════════
# 规则节点定义
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RuleNode:
    """规则图中的一个节点。"""
    rule_id: str
    rule_name: str
    source_ref: str
    confidence: float
    is_authorized: bool = True

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "is_authorized": self.is_authorized,
        }


# 河洛诊断规则注册表（原典授权）
HELUO_RULES: Dict[str, RuleNode] = {
    "HL_TIAN_DI_SHU": RuleNode(
        "HL_TIAN_DI_SHU", "天干地支取数",
        "起例卷上·天干取数定局", confidence=1.0, is_authorized=True,
    ),
    "HL_PRENATAL_HEXAGRAM": RuleNode(
        "HL_PRENATAL_HEXAGRAM", "先天卦计算",
        "起例卷上·八字内天数地数例", confidence=1.0, is_authorized=True,
    ),
    "HL_YUANTANG": RuleNode(
        "HL_YUANTANG", "元堂定位",
        "三才发秘·详元堂爻位式", confidence=1.0, is_authorized=True,
    ),
    "HL_POSTNATAL_HEXAGRAM": RuleNode(
        "HL_POSTNATAL_HEXAGRAM", "后天卦变换",
        "起例卷上·换后天卦例", confidence=1.0, is_authorized=True,
    ),
    "HL_HUA_GONG": RuleNode(
        "HL_HUA_GONG", "化工状态判定",
        "起例卷下·论化工", confidence=0.9, is_authorized=True,
    ),
    # ⚠ 2026-10-07 审计修：以下三条注册了但 HeLuoEvidenceProducer 从不产出，
    #   属「注册了却不存在」的空授权——confidence=1.0 / is_authorized=True 会让人
    #   以为已接入。引擎侧算法本身在 timeline_yun / guajie 里确实存在，只是
    #   **没有对应的 EngineEvidence**。如实标注而不擅自删除（注册表即授权面，
    #   删了等于放弃授权）；接入证据时删掉本段注释即可。
    "HL_DAYUN": RuleNode(          # TODO(证据未接入): 已注册未产出，见上
        "HL_DAYUN", "大运爻位值运",
        "起例卷上·小象阳爻九年运行例", confidence=1.0, is_authorized=True,
    ),
    "HL_YUEGUA": RuleNode(         # TODO(证据未接入): 已注册未产出，见上
        "HL_YUEGUA", "流月卦",
        "起例卷下·论月卦从世应起诀", confidence=0.95, is_authorized=True,
    ),
    "HL_RIGUA": RuleNode(          # TODO(证据未接入): 已注册未产出，见上
        "HL_RIGUA", "流日卦",
        "起例卷下·起日卦定式", confidence=0.95, is_authorized=True,
    ),
    "HL_JIEHOU_GUA": RuleNode(
        "HL_JIEHOU_GUA", "节候卦",
        "易冒引河洛理数", confidence=0.9, is_authorized=True,
    ),
}

# 规则 ID → 领域映射
# ⚠ 2026-10-07 审计修：HL_TIAN_DI_SHU 原先漏登记，落到 default "LIFE_EVENT"——
#   本命天数地数属基本盘，归入「人生事件」领域是语义错配。
RULE_DOMAIN_MAP: Dict[str, str] = {
    "HL_TIAN_DI_SHU": "CAREER",
    "HL_PRENATAL_HEXAGRAM": "FAMILY",
    "HL_POSTNATAL_HEXAGRAM": "FAMILY",
    "HL_YUANTANG": "FAMILY",
    "HL_HUA_GONG": "FAMILY",
    "HL_DAYUN": "CAREER",
    "HL_YUEGUA": "CAREER",
    "HL_RIGUA": "DAILY",
    "HL_JIEHOU_GUA": "LIFE_EVENT",
}


# 化工状态 → 方向映射（原典断语）
# 2026-10-07 补 KEZHI：原典 L582「又有大象与小象化工虽相反，却又有相生者则吉，
# **但忌克制，尤凶**」。此前 RESCUED 无条件判吉，致坎(水)克离(火)之盘误作吉断——
# 而原典明说此为最凶一档。KEZHI 现映射为 CAUTION，不作 SUPPORTIVE。
HUAGONG_DIRECTION: Dict[str, AssertionDirection] = {
    HuaGongState.NORMAL.value:   AssertionDirection.SUPPORTIVE,
    HuaGongState.RESCUED.value:  AssertionDirection.SUPPORTIVE,  # 仅限五行确实相生
    HuaGongState.REVERSE.value:  AssertionDirection.CAUTION,
    HuaGongState.KEZHI.value:    AssertionDirection.CAUTION,     # L582「忌克制，尤凶」
    HuaGongState.WEAK.value:     AssertionDirection.NEUTRAL,      # L576「终是浅薄，福寿减半」
    HuaGongState.UNRESOLVED.value: AssertionDirection.NEUTRAL,
}


# ═══════════════════════════════════════════════════════════════
# 诊断规则图构建
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DiagnosisResult:
    """诊断规则图构建结果。"""
    assertions: List[CanonicalAssertion]
    coverage: Optional[EvidenceCoverage]
    judgment: Optional[Judgment]

    def to_dict(self) -> dict:
        return {
            "assertions": [a.to_dict() for a in self.assertions],
            "coverage": self.coverage.to_dict() if self.coverage else None,
            "judgment": self.judgment.to_dict() if self.judgment else None,
        }


#: 最近一次 build_diagnosis_graph 中因「未在 HELUO_RULES 注册」而被丢弃的 rule_id。
#: 非空即表示有事实产出了却没进断言链，调用方应据此披露，而不是当成「没产出」。
_DROPPED_RULES: List[str] = []


def dropped_rules() -> List[str]:
    """最近一次 build_diagnosis_graph 丢弃的 rule_id 清单（正常应为空）。"""
    return list(_DROPPED_RULES)


def build_diagnosis_graph(
    evidences: List[EngineEvidence],
    signals: List[dict],
    frozen_state: Optional[Any] = None,
    subject: str = "unknown",
) -> DiagnosisResult:
    """
    构建河洛诊断规则图。

    Args:
        evidences: EngineEvidence 列表（来自 HeLuoEvidenceProducer）
        signals: EVENT_SIGNAL dict 列表（来自 yi_interpreter）
        frozen_state: FrozenHeluoState 对象（可选）
        subject: 案例标识（case_id）

    Returns:
        DiagnosisResult（含 assertions + coverage + judgment）
    """
    assertions: List[CanonicalAssertion] = []
    domain_map: Dict[str, List[str]] = {}  # domain → assertion_ids

    # ── 从 EngineEvidence 提取事实断言 ──────────────────────────
    dropped_rule_ids: List[str] = []
    for ev in evidences:
        rule_node = HELUO_RULES.get(ev.rule_id)
        if rule_node is None or not rule_node.is_authorized:
            # ⚠ 2026-10-07 审计修：原代码此处直接 continue，**不留任何痕迹**。
            #   实测 HeLuoEvidenceProducer 产出的 HL_HEXAGRAM_STRUCTURE 未在
            #   HELUO_RULES 注册 → 这条证据被静默吞掉，下游看不到卦体结构事实，
            #   却也无从判断「是没产出」还是「产出后丢了」。
            #   现登记到 dropped_rule_ids，由 dropped_rules() 供调用方披露。
            dropped_rule_ids.append(ev.rule_id)
            continue

        domain = RULE_DOMAIN_MAP.get(ev.rule_id, "LIFE_EVENT")

        # 匹配对应的 EVENT_SIGNAL 获取方向
        direction = _signal_direction_for_evidence(ev, signals)

        evidence_ref = EvidenceRef(
            evidence_id=ev.evidence_id,
            engine=ev.engine.value,
            value=ev.value,
            source_rule_ref=rule_node.source_ref,
            source_field=ev.source_field,
            temporal_scope=ev.temporal_scope.value,
            rule_id=ev.rule_id,
            calculation_version=ev.calculation_version,
            contract_version=ev.contract_version,
        )

        assertion = CanonicalAssertion(
            assertion_id=f"{ev.engine.value}_{ev.rule_id}",
            subject=subject,
            domain=domain,
            semantic=f"河洛{rule_node.rule_name}",
            direction=direction,
            temporal_scope=ev.temporal_scope.value,
            source_engine=ev.engine.value,
            source_rule=rule_node.rule_id,
            authorized_rule_id=f"HELUO_AUTH_{rule_node.rule_id}",
            evidence=evidence_ref,
        )
        assertions.append(assertion)
        domain_map.setdefault(domain, []).append(assertion.assertion_id)

    # ── 从 FrozenHeluoState 补充 H6 化工断言 ────────────────────
    if frozen_state and hasattr(frozen_state, 'hua_gong_state') and frozen_state.hua_gong_state:
        state_str = frozen_state.hua_gong_state
        dir_val = HUAGONG_DIRECTION.get(state_str, AssertionDirection.NEUTRAL)
        domain = "FAMILY"

        evidence_ref = EvidenceRef(
            evidence_id="HL_HUA_GONG",
            engine="HELUO",
            value=state_str,
            source_rule_ref="起例卷下·论化工",
            rule_id="HL_HUA_GONG",
        )

        assertion = CanonicalAssertion(
            assertion_id="HELUO_HL_HUA_GONG",
            subject=subject,
            domain=domain,
            semantic=f"化工状态: {state_str}",
            direction=dir_val,
            temporal_scope="birth",
            source_engine="HELUO",
            source_rule="HL_HUA_GONG",
            authorized_rule_id="HELUO_AUTH_HL_HUA_GONG",
            evidence=evidence_ref,
        )
        assertions.append(assertion)
        domain_map.setdefault(domain, []).append(assertion.assertion_id)

    # ── 从 EVENT_SIGNAL 提取流年/流月断言 ──────────────────────
    for sig in signals:
        direction_str = sig.get("direction", "NEUTRAL")
        rule_id = sig.get("rule_id", "")
        hexagram = sig.get("hexagram", "")
        confidence = sig.get("confidence", 0.5)
        time_scope = sig.get("time_scope", {})
        evidence_list = sig.get("evidence", [])

        dir_val = AssertionDirection.NEUTRAL
        if direction_str == "POSITIVE":
            dir_val = AssertionDirection.SUPPORTIVE
        elif direction_str == "NEGATIVE":
            dir_val = AssertionDirection.CAUTION

        temporal = "year"
        if "month" in time_scope:
            temporal = "month"
        elif "day" in time_scope:
            temporal = "day"

        domain = _sig_domain(direction_str, rule_id)

        evidence_ref = EvidenceRef(
            evidence_id=f"EVE_{rule_id}",
            engine="HELUO",
            value=hexagram,
            source_rule_ref="yi_interpreter.py·爻辞语义",
            rule_id=rule_id,
        )

        assertion = CanonicalAssertion(
            assertion_id=f"HELUO_{rule_id}",
            subject=subject,
            domain=domain,
            semantic=f"{hexagram}·{direction_str}（置信{confidence:.2f}）",
            direction=dir_val,
            temporal_scope=temporal,
            source_engine="HELUO",
            source_rule=rule_id,
            authorized_rule_id=f"HELUO_AUTH_{rule_id}",
            evidence=evidence_ref,
        )
        assertions.append(assertion)
        domain_map.setdefault(domain, []).append(assertion.assertion_id)

    # ── 构建 EvidenceCoverage ───────────────────────────────────
    coverage = None
    if domain_map:
        all_assertion_ids: List[str] = []
        for ids in domain_map.values():
            all_assertion_ids.extend(ids)
        coverage = EvidenceCoverage(
            domain="MULTI_DOMAIN",
            semantic="河洛理数全链路诊断",
            evidence_count=len(all_assertion_ids),
            source_engines=["HELUO"],
            evidence_types=["evidence", "signal", "hua_gong"],
            assertion_ids=all_assertion_ids,
        )

    # ── 构建 Judgment（需授权规则） ─────────────────────────────
    judgment = None
    if assertions and len(assertions) >= 2:
        # ⚠ 2026-10-07 审计修：此处原写死 authorized_by="V13_河洛诊断规则集"，
        #   而全仓**没有任何叫这个名字的规则注册表**（只在此处与 guidance.py 出现），
        #   实际唯一门槛是上面那句 len(assertions) >= 2——把一条**计数条件**
        #   包装成了「经某某规则集授权」的结论，正违反本模块第 11 行自己写的
        #   「禁止聚合成群即判断：需经 Authorized Judgment Rule 授权才产生 Judgment」。
        #   现改为列出**真正授权本结论的规则节点**（每条断言的 authorized_rule_id
        #   来自 HELUO_RULES 中 is_authorized=True 的节点）。计数门槛仍保留为
        #   「最小证据量」，但不再冒充授权来源。
        _auth = sorted({a.authorized_rule_id for a in assertions
                        if getattr(a, "authorized_rule_id", "")})
        judgment = Judgment(
            judgment_id="HELUO_DIAG_001",
            domain="MULTI_DOMAIN",
            semantic="河洛理数诊断结论",
            evidence_coverage=coverage or EvidenceCoverage(
                domain="MULTI_DOMAIN",
                semantic="",
                evidence_count=len(assertions),
                source_engines=["HELUO"],
                evidence_types=["evidence"],
                assertion_ids=[a.assertion_id for a in assertions],
            ),
            authorized_by="HELUO_RULES::" + (",".join(_auth) if _auth else "NONE"),
            supporting_assertions=[a.assertion_id for a in assertions],
        )

    _DROPPED_RULES.clear()
    _DROPPED_RULES.extend(sorted(set(dropped_rule_ids)))

    return DiagnosisResult(
        assertions=assertions,
        coverage=coverage,
        judgment=judgment,
    )


def _signal_direction_for_evidence(ev: EngineEvidence, signals: List[dict]) -> AssertionDirection:
    """匹配 EngineEvidence 到对应的 EVENT_SIGNAL，返回方向。"""
    prefix = ev.rule_id[:4]  # e.g., "HL_T"
    for sig in signals:
        sig_rule = sig.get("rule_id", "")
        if sig_rule.startswith(prefix) or prefix in sig_rule:
            d = sig.get("direction", "NEUTRAL")
            if d == "POSITIVE":
                return AssertionDirection.SUPPORTIVE
            if d == "NEGATIVE":
                return AssertionDirection.CAUTION
    return AssertionDirection.NEUTRAL


def _sig_domain(direction: str, rule_id: str = "") -> str:
    """根据 EVENT_SIGNAL 方向推断领域。"""
    if "LIUNIAN" in rule_id or "LIANYU" in rule_id:
        return "CAREER"
    if direction == "POSITIVE":
        return "CAREER"
    if direction == "NEGATIVE":
        return "LIFE_EVENT"
    return "FAMILY"
