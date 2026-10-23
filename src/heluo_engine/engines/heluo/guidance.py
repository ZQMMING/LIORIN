"""H14: Heluo Guidance Engine（河洛行动建议引擎）

职责：
  将 DiagnosisRuleGraph 的输出转化为结构化行动建议。
  设计原则：
    1. 辅助性：仅解释已有断言，不产生新判断
    2. 原典授权：每条建议来自原典原文或规则
    3. 无 LLM：纯规则模板生成
    4. 可审计：每条建议带 source_ref

架构：
  DiagnosisResult
    ├── assertions: List[CanonicalAssertion]
    ├── coverage: EvidenceCoverage
    └── judgment: Judgment
         ↓
  GuidanceEngine
    ├── _analyze_domain_patterns(assertions)
    ├── _build_guidance_sections(...)
    └── → HeluoGuidance
         ├── overview: str
         ├── action_items: List[ActionItem]
         ├── caution_items: List[CautionItem]
         ├── timing_advice: list[str]
         └── source_refs: list[str]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ActionItem:
    """一项正面行动建议。"""
    id: str
    title: str                   # 简短标题
    description: str             # 详细说明
    # ⚠ 2026-10-08 审计修（⚪18）：原注释写「基于原典权威度」，但**全模块没有一个
    # confidence 取自原典**——三处取值都是硬编码常数（0.85 / 0.9 / 0.6）或按断言条数
    # 线性折算（0.7*min(n,3)/3）。注释比实现claim得多，会让下游以为这是有依据的权重。
    # 现改为如实描述，并保留一个常量供统一调参。
    confidence: float            # 0-1（引擎自定标度，**无原典依据**，见 _CONF_BASE）
    source_ref: str              # 原典出处
    temporal_scope: str          # birth/year/month/day


@dataclass(frozen=True)
class CautionItem:
    """一项警示/注意项。"""
    id: str
    title: str
    description: str
    confidence: float
    source_ref: str
    temporal_scope: str


@dataclass(frozen=True)
class HeluoGuidance:
    """河洛诊断的行动建议。"""
    subject: str
    source_gua: str              # 先天卦
    target_gua: str              # 后天卦
    yuan_tang: str               # 元堂
    hua_gong_state: str          # 化工状态
    overview: str                # 总体判断（1-2句）
    action_items: List[ActionItem] = field(default_factory=list)
    caution_items: List[CautionItem] = field(default_factory=list)
    timing_advice: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "source_gua": self.source_gua,
            "target_gua": self.target_gua,
            "yuan_tang": self.yuan_tang,
            "hua_gong_state": self.hua_gong_state,
            "overview": self.overview,
            "action_items": [a.to_dict() for a in self.action_items],
            "caution_items": [c.to_dict() for c in self.caution_items],
            "timing_advice": self.timing_advice,
            "source_refs": self.source_refs,
        }


# ═══════════════════════════════════════════════════════════════
# 模板库（原典断语 + 工程化映射）
# ═══════════════════════════════════════════════════════════════

# 先天卦名 → 总体基调描述（原典《河洛真数》论命总纲）
SOURCE_GUA_TONE: dict[str, str] = {
    "乾为天": "纯阳之卦，刚健中正，宜主动进取，忌刚愎自用。",
    "坤为地": "纯阴之卦，柔顺承天，宜守正待时，忌妄动强求。",
    "地天泰": "天地交泰，阴阳和合，万事通达之象。",
    "天地否": "天地不交，阴阳闭塞，宜静守不宜进取。",
    "水火既济": "事已成，但需防盛极而衰，居安思危。",
    "火水未济": "事未成，但可图进取，待时而动。",
}

#: 引擎自定标度的基准置信度。
#: ⚠ 2026-10-08：**这不是原典权威度**，是本引擎自己定的显示刻度。
#: 原典只给定性断语（吉/凶/轻/重），没有给任何 0-1 权重；把它包装成「原典权威度」
#: 是伪引。现集中一处并显式命名，便于日后接到真正的依据上。
_CONF_BASE = 0.85

# 化工状态 → 建议倾向
HUAGONG_ADVICE: dict[str, str] = {
    "NORMAL": "化工得位，根基稳固，行事多有助力。",
    "RESCUED": "虽有波折，但能逢凶化吉，坚持正道可成。",
    "REVERSE": "化工反位，行事多阻，宜守不宜攻。",
    "UNRESOLVED": "化工不明，形势未定，需审时度势后再行决断。",
    # ⚠ 2026-10-07 审计修：以下两态 2026-10-07 才加入 hua_gong / diagnosis_rule_graph，
    #   本表未同步。KEZHI 是原典「忌克制，尤凶」的**最凶一档**，此前竟落到
    #   default「化工状态待判定」，产出 0 条建议 0 条警示——最凶档被当成未知档。
    "KEZHI": "化工受克，原典明言「尤凶」，宜彻底守成，不可进取。",
    "WEAK": "只得纳音级浅薄化工，福泽减半，宜安分培本，不可好高骛远。",
}

# 化工状态 → 行动建议模板
HUAGONG_ACTION_TEMPLATES: dict[str, List[dict]] = {
    "NORMAL": [
        {"title": "顺势而为", "desc": "化工得位，时机有利，可积极推进目标。", "scope": "year"},
        {"title": "巩固根基", "desc": "根基稳固，可考虑扩大影响力或深入发展。", "scope": "year"},
    ],
    "RESCUED": [
        {"title": "坚持正道", "desc": "虽有反复，但只要守住原则，终能化险为夷。", "scope": "year"},
        {"title": "寻求贵人", "desc": "可借助外力化解困境，留意身边能给予帮助的人。", "scope": "month"},
    ],
    "REVERSE": [
        {"title": "保守防守", "desc": "当前形势不利主动出击，宜退守巩固已有成果。", "scope": "year"},
        {"title": "减少开支", "desc": "化工反位，财务宜保守，避免大额投资或借贷。", "scope": "month"},
    ],
    "UNRESOLVED": [
        {"title": "观察等待", "desc": "形势不明朗，宜静观其变，等待更清晰的信号再行动。", "scope": "month"},
        {"title": "打好基础", "desc": "利用这段时期充实自身，为后续机会做准备。", "scope": "year"},
    ],
    "KEZHI": [
        {"title": "全面守成", "desc": "化工受克，原典明言「尤凶」，宜彻底收缩、不可主动出击。", "scope": "year"},
    ],
    "WEAK": [
        {"title": "培本固元", "desc": "仅得纳音级浅薄化工，福寿减半，宜务实积累。", "scope": "year"},
    ],
}


# ═══════════════════════════════════════════════════════════════
# 核心引擎
# ═══════════════════════════════════════════════════════════════

class HeluoGuidanceEngine:
    """
    河洛诊断 → 行动建议转换器。

    输入：DiagnosisResult（含 assertions + judgment）
    输出：HeluoGuidance（结构化行动建议）
    """

    def generate(
        self,
        assertions: List[Any],
        judgment: Any,
        source_gua: str,
        target_gua: str,
        yuan_tang: str,
        hua_gong_state: Optional[str] = None,
        subject: str = "unknown",
    ) -> HeluoGuidance:
        """
        从诊断结果生成行动建议。

        Args:
            assertions: CanonicalAssertion 列表
            judgment: Judgment 对象
            source_gua: 先天卦名
            target_gua: 后天卦名
            yuan_tang: 元堂名
            hua_gong_state: 化工状态（NORMAL/REVERSE/RESCUED/KEZHI/WEAK/UNRESOLVED）
            subject: 案例标识

        Returns:
            HeluoGuidance
        """
        # 1. 总体基调
        # 2026-10-08 审计修（🟡11）：judgment 原先收进签名就再没出现过——
        # 五个 _build_* 无一接收它，模块 docstring 画的「DiagnosisResult 含
        # assertions + judgment」架构图对不上代码。现把 judgment 下传给
        # _build_overview，由它在总览里如实交代本盘结论由哪些断言支撑。
        overview = self._build_overview(source_gua, hua_gong_state, judgment)

        # 2. 提取正面行动建议
        action_items = self._build_actions(assertions, hua_gong_state)

        # 3. 提取警示项
        caution_items = self._build_caution(assertions, hua_gong_state)

        # 4. 时序建议
        timing_advice = self._build_timing(assertions, hua_gong_state)

        # 5. 来源引用
        source_refs = self._collect_source_refs(assertions)

        return HeluoGuidance(
            subject=subject,
            source_gua=source_gua,
            target_gua=target_gua,
            yuan_tang=yuan_tang,
            hua_gong_state=hua_gong_state or "UNRESOLVED",
            overview=overview,
            action_items=action_items,
            caution_items=caution_items,
            timing_advice=timing_advice,
            source_refs=source_refs,
        )

    def _build_overview(
        self, source_gua: str, hua_gong_state: Optional[str], judgment: Any = None
    ) -> str:
        """生成总体判断描述。

        ⚠ 2026-10-08 审计修（🟡11）：原先 judgment 收下却不用。现用于如实交代
        **本盘结论由哪些断言支撑**——注意不再凭空造一个授权方名字：
        judgment.authorized_by 若存在就照登，不存在就不写。
        """
        tone = SOURCE_GUA_TONE.get(source_gua, f"卦象{source_gua}，需结合具体爻位分析。")
        huagong = HUAGONG_ADVICE.get(hua_gong_state or "", "化工状态待判定。")
        parts = [f"{tone} {huagong}"]
        if judgment is not None:
            sup = list(getattr(judgment, "supporting_assertions", None) or [])
            by = str(getattr(judgment, "authorized_by", "") or "")
            tail = f"本结论由 {len(sup)} 条断言支撑"
            if by:
                tail += f"（授权：{by}）"
            parts.append(tail + "。")
        return "".join(parts)

    def _build_actions(
        self, assertions: List[Any], hua_gong_state: Optional[str]
    ) -> List[ActionItem]:
        """从正面断言和化工状态生成行动建议。"""
        actions = []
        id_counter = 1

        # 化工状态模板建议
        templates = HUAGONG_ACTION_TEMPLATES.get(hua_gong_state or "UNRESOLVED", [])
        for tmpl in templates:
            actions.append(ActionItem(
                id=f"ACT-{id_counter:03d}",
                title=tmpl["title"],
                description=tmpl["desc"],
                confidence=_CONF_BASE,
                source_ref="河洛真数·论化工",
                temporal_scope=tmpl["scope"],
            ))
            id_counter += 1

        # 从断言中提取正面信号
        supportive_rules = sorted({
            getattr(a, "authorized_rule_id", "") or getattr(a, "source_rule", "")
            for a in assertions
            if hasattr(a, 'direction') and a.direction.value == "supportive"
        } - {""})
        supportive_count = len(
            [a for a in assertions
             if hasattr(a, 'direction') and a.direction.value == "supportive"])
        if supportive_count > 0:
            actions.append(ActionItem(
                id=f"ACT-{id_counter:03d}",
                title="把握当前趋势",
                description=(
                    f"当前有{supportive_count}条正面信号支持，"
                    "建议抓住时机推进重点事项。"
                ),
                confidence=0.7 * min(supportive_count, 3) / 3,
                # ⚠ 2026-10-08 审计修：原为 "V13_河洛诊断规则集" —— 该规则集**不存在**，
                #   是伪引。批次 C 把 diagnosis_rule_graph 的 authorized_by 改成了
                #   真实的 HELUO_RULES 清单，**却漏了这里**，同一处伪引两处不一致。
                #   现改为登记**实际支撑本条建议的规则 id**，取自断言自身，
                #   而非再编一个名字：拿不到就如实写空，不拿占位名顶替。
                #
                # ⚠ 2026-10-09 修：HL_HUA_GONG 本来就有**两条**断言
                #   （证据环一条 + 冻结态补一条），按列表拼会得到
                #   「…,HELUO_AUTH_HL_HUA_GONG,HELUO_AUTH_HL_HUA_GONG」——
                #   同一 id 出现两次。故此处用 set 去重。
                #   计数 supportive_count 仍按断言条数，两者口径不同、不可混用。
                source_ref=("HELUO_RULES::" + ",".join(supportive_rules)
                            if supportive_rules else ""),
                temporal_scope="year",
            ))
            id_counter += 1

        return actions

    def _build_caution(
        self, assertions: List[Any], hua_gong_state: Optional[str]
    ) -> List[CautionItem]:
        """从负面断言和化工状态生成警示项。"""
        cautions = []
        id_counter = 1

        # 化工反位 / 受克时的默认警示。
        # ⚠ 2026-10-07 审计修：旧条件只有 "REVERSE"，KEZHI（原典最凶一档）
        #   连一条警示都拿不到。WEAK 是减半的浅薄化工、非凶，故不入此表。
        _CAUTION_BY_STATE = {
            "REVERSE": ("谨慎决策", "化工反位，当前不宜做重大决策或冒险行动。", 0.9),
            "KEZHI": ("化工业已受克", "化工受克，原典「但忌克制，尤凶」——本岁宜彻底守成，"
                                       "不可主动出击，亦不宜大额投入。", 0.95),
        }
        if hua_gong_state in _CAUTION_BY_STATE:
            _t, _d, _c = _CAUTION_BY_STATE[hua_gong_state]
            cautions.append(CautionItem(
                id=f"CAU-{id_counter:03d}",
                title=_t,
                description=_d,
                confidence=_c,
                source_ref="河洛真数·论化工",
                temporal_scope="year",
            ))
            id_counter += 1

        # 从断言中提取负面信号
        caution_assertions = [
            a for a in assertions
            if hasattr(a, 'direction') and a.direction.value == "caution"
        ]
        for ca in caution_assertions:
            cautions.append(CautionItem(
                id=f"CAU-{id_counter:03d}",
                title=self._assertion_to_caution_title(ca),
                description=ca.semantic,
                confidence=ca.evidence.value if hasattr(ca, 'evidence') and hasattr(ca.evidence, 'value') else 0.6,
                source_ref=ca.source_rule,
                temporal_scope=ca.temporal_scope,
            ))
            id_counter += 1

        return cautions

    def _build_timing(
        self, assertions: List[Any], hua_gong_state: Optional[str]
    ) -> List[str]:
        """生成时序建议。"""
        advice = []
        temporal_domains = {}
        for a in assertions:
            scope = getattr(a, 'temporal_scope', 'birth')
            domain = getattr(a, 'domain', 'LIFE_EVENT')
            key = f"{scope}:{domain}"
            if key not in temporal_domains:
                temporal_domains[key] = []
            temporal_domains[key].append(a)

        for key, items in temporal_domains.items():
            scope, domain = key.split(":", 1)
            supportive = sum(
                1 for it in items
                if hasattr(it, 'direction') and it.direction.value == "supportive"
            )
            caution = sum(
                1 for it in items
                if hasattr(it, 'direction') and it.direction.value == "caution"
            )
            if supportive > caution:
                advice.append(f"{domain}（{scope}）：趋势向好，可积极作为。")
            elif caution > supportive:
                advice.append(f"{domain}（{scope}）：存在风险，宜谨慎行事。")
            else:
                advice.append(f"{domain}（{scope}）：平稳过渡，无明显利弊。")

        # 化工状态时序建议
        if hua_gong_state == "NORMAL":
            advice.append("全年整体：根基稳固，适合长期规划。")
        elif hua_gong_state == "REVERSE":
            advice.append("全年整体：局势不利，建议保守防守。")
        elif hua_gong_state == "RESCUED":
            advice.append("全年整体：先难后易，坚持正道可成。")

        return advice

    def _collect_source_refs(self, assertions: List[Any]) -> List[str]:
        """收集所有原典出处。"""
        refs = set()
        for a in assertions:
            ref = getattr(a, 'source_rule', '') or ''
            if ref:
                refs.add(ref)
        return sorted(refs)

    def _assertion_to_caution_title(self, assertion: Any) -> str:
        """从断言生成警示标题。"""
        semantic = getattr(assertion, 'semantic', '')
        if "元堂" in semantic:
            return "注意元堂位置"
        if "卦" in semantic:
            return "注意卦象变化"
        return "需关注事项"


# ═══════════════════════════════════════════════════════════════
# 便捷入口
# ═══════════════════════════════════════════════════════════════

def generate_guidance(
    assertions: List[Any],
    judgment: Any,
    source_gua: str,
    target_gua: str,
    yuan_tang: str,
    hua_gong_state: Optional[str] = None,
    subject: str = "unknown",
) -> HeluoGuidance:
    """便捷函数：从诊断结果生成行动建议。"""
    engine = HeluoGuidanceEngine()
    return engine.generate(
        assertions=assertions,
        judgment=judgment,
        source_gua=source_gua,
        target_gua=target_gua,
        yuan_tang=yuan_tang,
        hua_gong_state=hua_gong_state,
        subject=subject,
    )
