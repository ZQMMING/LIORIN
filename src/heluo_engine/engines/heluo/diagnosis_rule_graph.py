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

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...spec.canonical import (
    EngineEvidence,
    CanonicalAssertion,
    AssertionDirection,
    EvidenceRef,
    EvidenceCoverage,
    Judgment,
)
from .hua_gong import HuaGongState


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
    #
    # ✅ 2026-10-25 已接入：``evidence_producer`` 现产出这三条（及 HL_LIUNIAN_GUA）
    #   的证据，方向取自原典爻辞判据（起例卷之上 L212「三辞吉」），
    #   判不出时为「不判」（None）。实现见 ``time_layer_judgment`` 模块。
    "HL_DAYUN": RuleNode(          # 2026-10-25 已接入证据
        "HL_DAYUN", "大运爻位值运",
        "起例卷上·小象阳爻九年运行例", confidence=1.0, is_authorized=True,
    ),
    # 2026-10-24 新增：引擎**有**流年层（timeline 流年卦 + 小象行年爻断语），
    #   但注册表**缺**流年规则节点 ⇒ 流年证据无法进诊断图（静默丢失）。
    #   出处：《河洛真数·起例卷之上》小象阳爻九年运行例（L133 起）
    #   「一岁在同人九三（阳）爻；二岁取应爻变…」—— 与 HL_DAYUN 同源。
    "HL_LIUNIAN_GUA": RuleNode(
        "HL_LIUNIAN_GUA", "流年卦（小象行年爻）",
        "起例卷上·小象阳爻九年运行例", confidence=1.0, is_authorized=True,
    ),
    "HL_YUEGUA": RuleNode(         # 2026-10-25 已接入证据
        "HL_YUEGUA", "流月卦",
        "起例卷下·论月卦从世应起诀", confidence=0.95, is_authorized=True,
    ),
    "HL_RIGUA": RuleNode(          # 2026-10-25 已接入证据
        "HL_RIGUA", "流日卦",
        "起例卷下·起日卦定式", confidence=0.95, is_authorized=True,
    ),
    "HL_JIEHOU_GUA": RuleNode(
        "HL_JIEHOU_GUA", "节候卦",
        "易冒引河洛理数", confidence=0.9, is_authorized=True,
    ),
    # ✅ 2026-10-25 补注册：此前 ``evidence_producer`` **产出**了这条证据，
    #   但注册表里没有 ⇒ 被诊断图当作「未注册」**静默丢弃**
    #   （虽由 dropped_rules() 披露，但仍是能力损失）。
    #   卦体（正体/互体/伏体）是原典**核心概念**，非边角：
    #     · L140「凡卦有互体，有伏体，以正体内外卦除初上二爻，用中四爻，
    #       交互成卦，谓之互体…本卦如正体互体无取，而其中各含一卦隐而不见者，
    #       谓之伏体」——正体/互体/伏体的**定义**；
    #     · L161「正体若无，须看互体，互体又无，推及伏体，妙在通变，不可执一」
    #       ——**看卦次序**；
    #     · L107「非独正体得之为佳，**互体得之尤贵**」——互体之吉凶地位。
    "HL_HEXAGRAM_STRUCTURE": RuleNode(
        "HL_HEXAGRAM_STRUCTURE", "卦体（正体/互体/伏体）",
        "起例卷之上·卦体互体伏体（L140 定义 / L161 看卦次序）",
        confidence=0.9, is_authorized=True,
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
    # 2026-10-24 新增：流年卦（引擎有流年层，此前无规则节点 ⇒ 流年证据进不了图）
    "HL_LIUNIAN_GUA": "CAREER",
    "HL_YUEGUA": "CAREER",
    "HL_RIGUA": "DAILY",
    "HL_JIEHOU_GUA": "LIFE_EVENT",
    # 2026-10-25 补登记：卦体（正体/互体/伏体）——原典核心概念，
    #   此前证据被产出却因未注册而被丢弃。归入「人生事件」（本命盘结构事实）。
    "HL_HEXAGRAM_STRUCTURE": "LIFE_EVENT",
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
    signals: List[Any],
    frozen_state: Optional[Any] = None,
    subject: str = "unknown",
) -> DiagnosisResult:
    """
    构建河洛诊断规则图。

    Args:
        evidences: EngineEvidence 列表（来自 HeLuoEvidenceProducer）
        signals: 事件信号列表。**2026-10-08 起同时接受三种形态**：
            - ``dict``（旧，键 ``rule_id`` / ``direction``）
            - ``CanonicalSignal`` 数据类（管线实产，规则 id 在 ``rule_refs`` 列表里）
            - 任意带 ``rule_refs`` / ``direction`` 属性的对象
          原实现只认 dict，真跑管线会抛 AttributeError，见 ``_sig_field`` 注释。
        frozen_state: FrozenHeluoState 对象（可选）
        subject: 案例标识（case_id）

    Returns:
        DiagnosisResult（含 assertions + coverage + judgment）
    """
    assertions: List[CanonicalAssertion] = []
    domain_map: Dict[str, List[str]] = {}  # domain → assertion_ids
    _DROPPED_RULES.clear()
    _UNMATCHED_EVIDENCE.clear()
    _HELUO_OWN_BASIS.clear()

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

        # 方向：先问河洛自己的判据，问不到才回落信号层（批次 K）
        #
        # ⚠ 2026-10-25 新增：**时间层规则**（大运/流年/流月/流日）的方向
        #   不来自 frozen_state（那里没有时间层数据），而来自**证据自身**：
        #   证据生产器已用原典爻辞判据（起例卷之上 L212「三辞吉」）判过，
        #   结果放在 ``ev.attributes["passed"]``（True=吉 / False=凶 / None=不判）。
        #   ⇒ 先从证据取；取不到（不判）再走 frozen_state / 信号层。
        direction, own_basis = heluo_own_direction(ev.rule_id, frozen_state)
        if direction is None and ev.rule_id in _TIME_LAYER_RULE_IDS:
            _d, _b = _time_layer_direction_from_evidence(ev)
            if _d is not None:
                direction = _d
                own_basis = _b
                _HELUO_OWN_BASIS[ev.rule_id] = _b
        if direction is None:
            direction = _signal_direction_for_evidence(ev, signals)
        else:
            _HELUO_OWN_BASIS[ev.rule_id] = own_basis

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
    # ⚠ 2026-10-08：此处原先也是纯 `sig.get(...)`，与 _signal_direction_for_evidence
    #   是**同一处类型缺陷的两份拷贝**。只修一处的话，真跑管线仍会在此炸。
    #   现统一走 _sig_field（dict / 数据类都认），不再各写各的。
    for sig in signals or []:
        direction_str = _sig_direction_str(sig)
        rule_id = (_sig_rule_ids(sig) or [""])[0]
        hexagram = _sig_field(sig, "hexagram", "")
        confidence = _sig_field(sig, "confidence", 0.5)
        time_scope = _sig_field(sig, "time_scope", {})

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


# ═══════════════════════════════════════════════════════════════════
# 河洛自有判据 → 断言方向（2026-10-08 批次 K）
# ═══════════════════════════════════════════════════════════════════
# 诊断方向**优先**取自河洛自己的判据，而不是等信号层：
# 信号引擎当前只产出 1 条八字信号，河洛信号为 0，若只依赖信号，
# 六条河洛断言会永远停在默认值 neutral —— 而 neutral 与「判过了是中���」
# 在输出上完全一样，没人能分辨。
#
# 取不到（河洛判据判不了）时**回落信号层**，再取不到才是不判并登记。


def _dir_from_jiu_ji(result: Any) -> AssertionDirection | None:
    """六项判据的**单项** JuResult → 断言方向；「不判」返回 None。

    ⚠ 这里必须收单项，不能收 ``judge_liu_ju()`` 返回的整张 dict
    （形如 ``{"卦名": JuResult(...), "爻位": ...}``）—— 传整张进来
    会取不到 ``.passed``，直接 AttributeError。
    同时容忍 dict 形态的 JuResult（测试替身会给 dict）。
    """
    if result is None:
        return None
    if isinstance(result, dict):
        if "passed" in result:
            passed = result.get("passed")
        else:                       # 整张 dict → 取「卦名」这一项
            item = result.get("卦名")
            if item is None:
                return None
            passed = item.get("passed") if isinstance(item, dict) \
                else getattr(item, "passed", None)
    else:
        passed = getattr(result, "passed", None)
    if passed is None:
        return None
    return (AssertionDirection.SUPPORTIVE if passed
            else AssertionDirection.CAUTION)


#: 时间层规则 id（方向取自**证据自身**，不走 frozen_state）
#: ⚠ 2026-10-25：此前这四条「注册了却从不产出证据」；现由
#   ``evidence_producer`` 产出（事实 + 有据方向），见
#   ``time_layer_judgment`` 模块。
_TIME_LAYER_RULE_IDS = frozenset({
    "HL_DAYUN", "HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA",
})


def _time_layer_direction_from_evidence(
    ev: EngineEvidence,
) -> tuple[AssertionDirection | None, str]:
    """时间层证据 → (方向, 依据)。**判不出就返回 (None, 理由)**。

    方向取自证据生产器写入的 ``attributes["passed"]``：
      · ``True``  → SUPPORTIVE（吉，原典 L212「三辞吉」）
      · ``False`` → CAUTION（凶）
      · ``None``  → **不判**（原典未言 / 门槛不满足 ⇒ 宁可不判）

    ⚠ 该三态由 ``time_layer_judgment`` 判定并附原典依据；本函数**只做搬运**，
      不自行推断方向，也不产生任何数值分数。
    """
    attrs = getattr(ev, "attributes", None) or {}
    if not isinstance(attrs, dict):
        return None, "证据无 attributes ⇒ 时间层不判"
    if "passed" not in attrs:
        return None, "证据无 passed 字段 ⇒ 时间层不判"
    passed = attrs.get("passed")
    detail = str(attrs.get("detail", "") or "")
    basis = str(attrs.get("basis", "") or "")
    if passed is True:
        return (AssertionDirection.SUPPORTIVE,
                "爻辞判吉（%s）%s" % (basis, detail))
    if passed is False:
        return (AssertionDirection.CAUTION,
                "爻辞判凶（%s）%s" % (basis, detail))
    return None, "时间层判据**不判**（%s）%s" % (basis, detail)


def heluo_own_direction(rule_id: str, frozen_state: Any
                        ) -> tuple[AssertionDirection | None, str]:
    """河洛自有判据 → (方向, 依据)。**判不了就返回 (None, 理由)**。

    只用已落码的判据，不臆造阈值：
      · 数格：只判「凶」，不判「吉」→ 不凶时返回 None，不硬报 SUPPORTIVE
      · 六项：卦名 / 爻位 / 爻辞 / 得时 / 有援 / 顺时，各项自带「不判」
    """
    if frozen_state is None:
        return None, "无冻结态"
    try:
        from .gui_ming_liu_ju import (GUA_MING_GOOD_EXAMPLES, judge_liu_ju,
                                       judge_yao_wei)
        from .numbers import short_hexagram_name
    except Exception as exc:                     # pragma: no cover
        return None, "六项判据不可用：%s" % exc

    if rule_id == "HL_TIAN_DI_SHU":
        try:
            from .guajie import judge_shu_xiong
            # ⚠ 必须用**原始** tian_shu / di_shu，不是归一后的 tian_reduced /
            #   di_reduced。数格表的天数档位是「至弱 4–8 / 不足 9–24 / 正 25 /
            #   有余 ≥30」（L38/L42/L47），那是原始和的量纲；
            #   guajie.build_guajie_from_result 也是这么传的。
            #   传归一值会让 8 落进「至弱」，**几乎所有盘都被判成数凶**。
            #
            # ⚠ 2026-10-09 修：birth_month 也**不能传 None**。数格判据含
            #   阳月/阴月加减，原先这里硬传 None，导��**诊断层与解卦层对
            #   同一份数据给出不同结论**（实测 1983-11-03：解卦层判
            #   「以弱敌强」shu_xiong=True，诊断层却因 None 落到「不凶」）。
            #   现从 frozen_state.birth_date 取真实生月；取不到才回落 None
            #   并在依据里注明。
            _bm = None
            _bd = str(getattr(frozen_state, "birth_date", "") or "")
            if len(_bd) >= 7 and _bd[4] == "-":
                try:
                    _bm = int(_bd[5:7])
                except ValueError:
                    _bm = None
            # ⚠ 2026-10-25 审计修（真实缺陷）：``judge_shu_xiong`` 的
            #   ``birth_month`` 是**必填 int**，内部用它做「阳月/阴月」判定
            #   （``birth_month in YANG_YUE_LING`` 等）。
            #   原先此处取不到生月就传 ``None`` ⇒ 落进「既非阳月也非阴月」的
            #   隐式分支 ⇒ **静默判错**（缺失被当成正常，比答错更坏）。
            #   ⇒ 取不到生月就**不判数格**，并把理由写进依据。
            if _bm is None:
                return None, "数格未产出：缺生月（数格判据须按阳月/阴月加减，缺生月不猜）"
            sx = judge_shu_xiong(frozen_state.tian_shu,
                                 frozen_state.di_shu, _bm,
                                 frozen_state.gender or "")
        except Exception as exc:
            return None, "数格判不了：%s" % exc
        if sx is None:
            return None, "数格未产出"
        if getattr(sx, "shu_xiong", False):
            return (AssertionDirection.CAUTION,
                    "数格判凶（%s）：%s" % (getattr(sx, "pattern", "") or "数凶",
                                           getattr(sx, "pattern", "")))
        # ⚠ 数格只判凶、不判吉。此处返回 None 让它走信号档，
        #   **不得**把「不凶」当成「吉」——那是把没有判据说成有判据。
        return None, "数格只判凶不判吉，此项不判方向"

    if rule_id == "HL_YUANTANG":
        idx = getattr(frozen_state, "yuan_tang_index", None)
        if idx is None:
            return None, "元堂索引缺失"
        r = _dir_from_jiu_ji(judge_yao_wei(idx))
        if r is None:
            return None, "六项·爻位不判"
        return r, "六项·爻位：元堂在第%d爻（二五爻为吉，L636）" % idx

    if rule_id == "HL_PRENATAL_HEXAGRAM":
        name = (getattr(frozen_state, "prenatal_name", "") or "").strip()
        if not name:
            return None, "先天卦名缺失"
        # ⚠ 2026-10-24 第三轮审计修：原实现把**全名**（如「地天泰」）直接
        #   传给 judge_liu_ju，而 GUA_MING_GOOD_EXAMPLES 装的是**简称**
        #   （「泰」「大有」「同人」「晋」「豫」）⇒ 精确成员判断恒不成立
        #   ⇒ 「一卦名吉」这条原典判据**永不触发**，方向静默回落 NEUTRAL。
        #   而 interpretation.py:360 的同一判据**已**用 short_hexagram_name 归一
        #   —— 同一条判据两处口径不一致，本处是漏的那一处。
        #   修法：按 interpretation.py 的同一口径归一（numbers.short_hexagram_name
        #   是判词层单一来源，不另立手抄表）。
        short = short_hexagram_name(name)
        if not short:
            return None, f"先天卦名「{name}」无法归一为简称"
        if not any(g in name for g in GUA_MING_GOOD_EXAMPLES):
            return None, ("六项·卦名：原文明举吉卦%s，本卦%s不在其列"
                          "（原文作「之类」=举例未穷举，故不判）"
                          % ("、".join(GUA_MING_GOOD_EXAMPLES), name))
        r = _dir_from_jiu_ji(
            judge_liu_ju(gua_name=short))
        if r is None:
            return None, "六项·卦名不判"
        return r, "六项·卦名：%s 在原文明举吉卦之列" % name

    if rule_id == "HL_HUA_GONG":
        # 证据环里的这条化工断言：方向同样走 HUAGONG_DIRECTION（L573/L576/L582），
        # 与下方 frozen_state 分支补的那条保持一致。此前只有后者接上，
        # 同一条规则出现「一条有方向、一条没有」的不一致。
        st = getattr(frozen_state, "hua_gong_state", None)
        if not st:
            return None, "无化工状态"
        d = HUAGONG_DIRECTION.get(st)
        if d is None:
            return None, "化工状态 %s 未在 HUAGONG_DIRECTION 中" % st
        if d == AssertionDirection.NEUTRAL:
            return None, "化工状态 %s → 中性（WEAK/UNRESOLVED 本就不分吉凶）" % st
        return d, "化工状态 %s（L573/L576/L582）" % st

    return None, "该规则暂无河洛自有判据"


def _sig_field(sig: Any, name: str, default: Any = "") -> Any:
    """从一个 signal 上取字段，**dict 与数据类都支持**。

    ⚠ 2026-10-08：此函数是本轮修的**真缺陷**。原先这里直接 `sig.get(...)`，
    也就是**只认 dict**。而管线实际产出的是 `CanonicalSignal` 数据类
    （PipelineResult.canonical_signals 是 dict[str, list[CanonicalSignal]]），
    于是 `build_diagnosis_graph` 一旦被真实链路调到就抛
    AttributeError: 'CanonicalSignal' object has no attribute 'get'。

    为什么此前没人发现：单元测试喂的都是自造的 dict signals，类型碰巧对得上；
    只有真跑管线才会撞上。这正是「吃引擎、跑真实案例」的价值。

    两类 signal 的字段名也不同（dict 用 ``rule_id``，数据类只有
    ``rule_refs`` 列表），故取值按「属性优先、其次字典、再次默认」三级回落。
    """
    if isinstance(sig, dict):
        return sig.get(name, default)
    return getattr(sig, name, default)


def _sig_rule_ids(sig: Any) -> List[str]:
    """取一个 signal 上**全部**可能携带的规则 id。

    CanonicalSignal 没有 ``rule_id``，只有 ``rule_refs: list[str]``；
    旧 dict 形态才有 ``rule_id``。两者都收下，返回统一为一组字符串。
    """
    out: List[str] = []
    one = _sig_field(sig, "rule_id", "")
    if isinstance(one, str) and one:
        out.append(one)
    for name in ("rule_refs", "rules", "rule_ids"):
        v = _sig_field(sig, name, None)
        if isinstance(v, (list, tuple, set)):
            out.extend(str(x) for x in v if x)
    return out


def _sig_direction_str(sig: Any) -> str:
    """取 signal 方向，统一成字符串。

    ``EventDirection`` 是枚举时取其 ``.value``——直接拿枚举跟字符串比会永假，
    那样每条证据都会静默落成 NEUTRAL。
    """
    d = _sig_field(sig, "direction", "NEUTRAL")
    return str(getattr(d, "value", d) or "NEUTRAL")


def _signal_direction_for_evidence(
    ev: EngineEvidence, signals: List[Any]
) -> AssertionDirection:
    """匹配 EngineEvidence 到对应的 EVENT_SIGNAL，返回方向。

    匹配不上时返回 NEUTRAL——但**必须登记**，否则「没有信号」与
    「有信号但方向未知」两种情况在输出上完全一样，没人能发现河洛信号根本没产出。
    """
    prefix = ev.rule_id[:4]  # e.g., "HL_T"
    for sig in signals or []:
        for sig_rule in _sig_rule_ids(sig):
            if sig_rule.startswith(prefix) or prefix in sig_rule:
                d = _sig_direction_str(sig)
                if d == "POSITIVE":
                    return AssertionDirection.SUPPORTIVE
                if d == "NEGATIVE":
                    return AssertionDirection.CAUTION
    _UNMATCHED_EVIDENCE.append(ev.rule_id)
    return AssertionDirection.NEUTRAL


#: 最近一次 build_diagnosis_graph 中**没匹配到任何 signal** 的河洛 rule_id。
#: 非空即表示这些断言的方向是「无信号可依」的默认值，不是判出来的 NEUTRAL。
_UNMATCHED_EVIDENCE: List[str] = []


_HELUO_OWN_BASIS: Dict[str, str] = {}


def heluo_own_basis() -> Dict[str, str]:
    """本次构建中，由**河洛自有判据**定出方向的 rule_id → 依据。"""
    return dict(_HELUO_OWN_BASIS)


def unmatched_evidence() -> List[str]:
    """最近一次未匹配到 signal 的 rule_id（正常应为空）。

    ⚠ 实测（2026-10-08 真实盘 1983-11-03）：管线当前只产出 **1 条** signal，
    且来自**八字引擎**（rule_refs 全为 ZPZ-*），**河洛信号为 0**。
    故本清单非空是**当前真实状态**，不是缺陷复发——但它意味着
    「诊断方向」目前拿不到信号层的支持，全靠各规则自身的默认方向。
    """
    return list(_UNMATCHED_EVIDENCE)


def _sig_domain(direction: str, rule_id: str = "") -> str:
    """根据 EVENT_SIGNAL 方向推断领域。"""
    if "LIUNIAN" in rule_id or "LIANYU" in rule_id:
        return "CAREER"
    if direction == "POSITIVE":
        return "CAREER"
    if direction == "NEGATIVE":
        return "LIFE_EVENT"
    return "FAMILY"
