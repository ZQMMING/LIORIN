"""H4: RELATIONAL INTERPRETATION ENGINE V1.0

核心功能:
1. 因子权重计算 (本命卦/元堂/后天卦/流年/流月/流日/大运/流时)
2. 五行生克修正
3. 时间衰减模型
4. 解释链生成
5. 置信度计算

输入: HeluoCalculationRun + 时间序列结果
输出: InterpretationOutput (状态/机会/风险/建议/解释链)
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 数据类型定义
# ═══════════════════════════════════════════════════════════════════
@dataclass
class HeluoInput:
    """H4 输入数据。"""
    # 本命卦相关
    prenatal_hexagram: str           # 如 "乾上乾下"
    yuan_tang: str                   # 如 "五爻"
    postnatal_hexagram: str          # 如 "乾上坤下"
    
    # 时间序列相关
    day_hexagram: str                # 流日卦
    year_cycle: str                  # 如 "乙巳"
    month_cycle: str                 # 如 "甲申"
    day_cycle: str                   # 如 "丙午"
    
    # 五行状态
    element_state: Dict[str, float]  # {木: 0.6, 火: 0.8, ...}
    
    # 爻位信息
    line_position: Dict[str, Any]    # {active_line: 5, position_type: "尊位", yinyang: "阳"}
    
    # 时间状态
    time_state: Dict[str, Any]       # {solar_term: "立秋", hour: 14, true_solar_time: True}
    
    # 大运
    da_yun_sequence: List[Dict] = field(default_factory=list)


@dataclass
class OpportunityFactor:
    """机会因子。"""
    type: str
    strength: float           # 0-1
    time_window: str
    classical_basis: str


@dataclass
class RiskFactor:
    """风险因子。"""
    type: str
    severity: float           # 0-1
    trigger_condition: str
    classical_basis: str


@dataclass
class RecommendedAction:
    """建议行动。"""
    primary: str
    secondary: List[str]
    avoid: List[str]
    confidence: float


@dataclass
class InterpretationStep:
    """解释链步骤。"""
    step: int
    logic: str
    source: str


@dataclass
class InterpretationOutput:
    """解释引擎输出。"""
    current_state: str
    opportunity: OpportunityFactor
    risk: RiskFactor
    recommended_action: RecommendedAction
    interpretation_chain: List[InterpretationStep]
    warnings: List[str]
    meta: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════
# 因子权重定义
# ═══════════════════════════════════════════════════════════════════
FACTOR_WEIGHTS = {
    "prenatal_hexagram": 0.25,   # 本命卦 - 先天根基
    "yuan_tang": 0.20,          # 元堂 - 时辰定位
    "postnatal_hexagram": 0.15, # 后天卦 - 时空变换
    "year_cycle": 0.12,         # 流年 - 年度大势
    "month_cycle": 0.10,        # 流月 - 月度机会
    "day_cycle": 0.08,          # 流日 - 当日时机
    "da_yun": 0.07,             # 大运 - 十年周期
    "hour_cycle": 0.03,         # 流时 - 时辰细节
}

# 五行修正系数
ELEMENT_MODIFIERS = {
    "当令": 0.15,
    "相生": 0.08,
    "相克": -0.10,
    "被克": -0.12,
    "休囚": -0.05,
}

# 时间衰减系数
TIME_DECAY = {
    "年": 0.8,    # 年度趋势
    "月": 0.9,    # 月度机会
    "日": 1.0,    # 当日时机（基准）
    "时": 0.7,    # 时辰细节
}


# ═══════════════════════════════════════════════════════════════════
# 核心算法
# ═══════════════════════════════════════════════════════════════════
class RelationalInterpretationEngine:
    """关系解释引擎 V1.0。"""
    
    def __init__(self, input_data: HeluoInput):
        self.input = input_data
        self.chain: List[InterpretationStep] = []
        self.warnings: List[str] = []
    
    def compute(self) -> InterpretationOutput:
        """执行完整解释链计算。"""
        # 1. 计算各因子权重
        weights = self._compute_factor_weights()
        
        # 2. 计算综合分数
        total_score = self._compute_total_score(weights)
        
        # 3. 生成解释链
        self._build_interpretation_chain(weights)
        
        # 4. 识别机会和风险
        opportunity = self._identify_opportunity(weights, total_score)
        risk = self._identify_risk(weights, total_score)
        
        # 5. 生成建议
        action = self._generate_recommended_action(opportunity, risk, total_score)
        
        # 6. 计算置信度
        confidence = self._compute_confidence()
        
        # 7. 生成当前状态描述
        current_state = self._generate_current_state()
        
        return InterpretationOutput(
            current_state=current_state,
            opportunity=opportunity,
            risk=risk,
            recommended_action=action,
            interpretation_chain=self.chain,
            warnings=self.warnings,
            meta={
                "algorithm_version": "H4-V1.0",
                "confidence_score": confidence,
                "evidence_closure": self._compute_evidence_closure(),
                "interpretation_type": "relational",
                "input_summary": self._summarize_input()
            }
        )
    
    def _compute_factor_weights(self) -> Dict[str, float]:
        """计算各因子权重（含五行修正）。"""
        weights = FACTOR_WEIGHTS.copy()
        
        # 应用五行修正
        element_modifier = self._calculate_element_modifier()
        for key in weights:
            weights[key] *= (1 + element_modifier)
        
        # 应用时间衰减
        time_modifier = self._calculate_time_decay()
        for key in weights:
            weights[key] *= time_modifier.get(key, 1.0)
        
        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _calculate_element_modifier(self) -> float:
        """计算五行修正因子。"""
        if not self.input.element_state:
            return 0.0
        
        # 简化版：取最大五行强度
        max_strength = max(self.input.element_state.values()) if self.input.element_state else 0
        return (max_strength - 0.5) * 0.2  # 归一化到 [-0.1, 0.1]
    
    def _calculate_time_decay(self) -> Dict[str, float]:
        """计算时间衰减系数。"""
        return TIME_DECAY.copy()
    
    def _compute_total_score(self, weights: Dict[str, float]) -> float:
        """计算综合评分 (-1 到 1)。"""
        # 本命卦基础分
        base_score = self._hexagram_base_score()
        
        # 加权综合
        weighted_sum = base_score * weights.get("prenatal_hexagram", 0)
        weighted_sum += 0.1 * weights.get("yuan_tang", 0)
        weighted_sum += 0.05 * weights.get("postnatal_hexagram", 0)
        
        # 时间因子
        year_factor = self._year_cycle_factor()
        month_factor = self._month_cycle_factor()
        day_factor = self._day_cycle_factor()
        
        weighted_sum += year_factor * weights.get("year_cycle", 0)
        weighted_sum += month_factor * weights.get("month_cycle", 0)
        weighted_sum += day_factor * weights.get("day_cycle", 0)
        
        return max(-1.0, min(1.0, weighted_sum))
    
    def _hexagram_base_score(self) -> float:
        """⛔ 已作废（2026-10-07）：本函数的自拟分数无原典依据。

        原实现返回一组按「上下卦」硬编码的分数
        （乾0.8 / 坤0.6 / 震巽0.5 / 坎离0.4 / 其余0.3），
        判据是 ``"乾" in hex`` 这种**字符串包含**——它既不是原典规则，
        也会误判：凡卦名含该字即命中，与卦的上下卦结构无关
        （如「地天泰」含「天」不命中，但「天泽履」含「天」亦不命中，
        而「泽天夬」会命中「天」，行为不可解释）。

        原典的真实判据见起例卷之中 L630–L648「贵命十体」六项
        （一卦名吉 / 二爻吉 / 三辞吉 / 四得时 / 五有援 / 六顺时），
        已落成 :mod:`gui_ming_liu_ju`，返回**原典判据名 + 原文依据 +
        吉/凶/不判**，而非自拟分数。

        Raises:
            NotImplementedError: 恒抛出。**不得**静默回退到旧分数。
        """
        raise NotImplementedError(
            "_hexagram_base_score 的卦象基础分无原典依据，已于 2026-10-07 作废。"
            "请改用 gui_ming_liu_ju.judge_liu_ju() 的六项原典判据"
            "（起例卷之中 L630–L648）。若确需 0-1 数值，须先补原典出处。"
        )
    
    def _year_cycle_factor(self) -> float:
        """⛔ 已作废（2026-10-07）：流年因子为单年硬编码，无原典依据。

        原实现是：

            # 乙巳年 - 火运
            if "乙" in year or "巳" in year:
                return 0.3
            return 0.0

        这**不是简化规则**，而是针对某一个具体年份写死的常量——
        它对 2025 乙巳之外的任何年份一律返回 0.0，对含「乙」或「巳」的
        任何组合一律返回 0.3。这既无原典依据，也不具备算法意义。

        原典中与流年相关的是**查表式**判据（流年卦、爻辞、元气化工等），
        见 :mod:`guajie` 的十二凶/判词/元气化工链与 :mod:`gui_ming_liu_ju`
        的六项判据，**不存在**「流年数值因子」这种东西。

        Raises:
            NotImplementedError: 恒抛出。**不得**静默回退。
        """
        raise NotImplementedError(
            "_year_cycle_factor 的流年因子（原为 '乙巳年-火运' 单年硬编码）"
            "无原典依据，已于 2026-10-07 作废。"
            "请改用 guajie 的流年卦查表判据或 gui_ming_liu_ju 的六项判据。"
        )
    
    def _month_cycle_factor(self) -> float:
        """流月因子。"""
        month = self.input.month_cycle
        if not month:
            return 0.0
        return 0.1
    
    def _day_cycle_factor(self) -> float:
        """流日因子。"""
        day = self.input.day_cycle
        if not day:
            return 0.0
        return 0.15
    
    def _build_interpretation_chain(self, weights: Dict[str, float]) -> None:
        """构建解释链。"""
        steps = []
        
        # Step 1: 本命卦分析
        steps.append(InterpretationStep(
            step=1,
            logic=f"本命卦{self.input.prenatal_hexagram}→刚健中正",
            source="《河洛理数·卷之一》"
        ))
        
        # Step 2: 元堂定位
        steps.append(InterpretationStep(
            step=2,
            logic=f"元堂{self.input.yuan_tang}→尊位当权",
            source="《河洛理数·卷之三》"
        ))
        
        # Step 3: 后天卦变换
        steps.append(InterpretationStep(
            step=3,
            logic=f"后天卦{self.input.postnatal_hexagram}→天地交泰",
            source="《河洛理数·卷之四》"
        ))
        
        # Step 4: 流年分析
        steps.append(InterpretationStep(
            step=4,
            logic=f"流年{self.input.year_cycle}→火运当令",
            source="《协纪辨方书》"
        ))
        
        # Step 5: 综合判定
        total_score = self._compute_total_score(weights)
        if total_score > 0.3:
            steps.append(InterpretationStep(
                step=5,
                logic="综合判定：阳居尊位，时逢进运",
                source="RELATIONAL_INTERPRETATION"
            ))
        elif total_score > 0:
            steps.append(InterpretationStep(
                step=5,
                logic="综合判定：平稳过渡，守正待时",
                source="RELATIONAL_INTERPRETATION"
            ))
        else:
            steps.append(InterpretationStep(
                step=5,
                logic="综合判定：需谨慎行事，以退为进",
                source="RELATIONAL_INTERPRETATION"
            ))
        
        self.chain = steps
    
    def _identify_opportunity(self, weights: Dict[str, float], score: float) -> OpportunityFactor:
        """识别机会。"""
        if score > 0.5:
            return OpportunityFactor(
                type="进德修业",
                strength=0.75,
                time_window="当前大运周期内",
                classical_basis="《河洛理数·卷之二》"
            )
        elif score > 0.2:
            return OpportunityFactor(
                type="稳中求进",
                strength=0.55,
                time_window="本月内",
                classical_basis="《河洛理数·卷之三》"
            )
        else:
            return OpportunityFactor(
                type="守正待机",
                strength=0.35,
                time_window="待定",
                classical_basis="《河洛理数·卷之四》"
            )
    
    def _identify_risk(self, weights: Dict[str, float], score: float) -> RiskFactor:
        """识别风险。"""
        if score < -0.3:
            return RiskFactor(
                type="困顿受阻",
                severity=0.7,
                trigger_condition="进退失据",
                classical_basis="《易·否卦》"
            )
        elif score < 0:
            return RiskFactor(
                type="波动起伏",
                severity=0.4,
                trigger_condition="急躁冒进",
                classical_basis="《河洛理数·卷之三》"
            )
        else:
            return RiskFactor(
                type="亢龙有悔",
                severity=0.2,
                trigger_condition="刚愎自用",
                classical_basis="《易·乾卦·上九》"
            )
    
    def _generate_recommended_action(self, opp: OpportunityFactor, risk: RiskFactor, score: float) -> RecommendedAction:
        """生成建议行动。"""
        if score > 0.5:
            return RecommendedAction(
                primary="积极进取，把握机遇",
                secondary=["广结善缘", "积累资源"],
                avoid=["刚愎自用", "急躁冒进"],
                confidence=0.82
            )
        elif score > 0:
            return RecommendedAction(
                primary="守正待时",
                secondary=["巩固基础", "学习提升"],
                avoid=["盲目扩张"],
                confidence=0.75
            )
        else:
            return RecommendedAction(
                primary="韬光养晦",
                secondary=["反思总结", "等待时机"],
                avoid=["冒险投机"],
                confidence=0.70
            )
    
    def _compute_confidence(self) -> float:
        """计算置信度。"""
        # 基于证据闭合度
        evidence_closure = self._compute_evidence_closure()
        
        # 基于输入完整性
        input_completeness = self._compute_input_completeness()
        
        # 综合置信度
        confidence = evidence_closure * 0.6 + input_completeness * 0.4
        
        return round(max(0.0, min(1.0, confidence)), 2)
    
    def _compute_evidence_closure(self) -> float:
        """证据闭合度：各证据维度中被**真实填充**的字段占比。

        2026-10-06 修正：本方法原为 ``return 0.85``（注释「简化版」），
        但它被 ``_compute_confidence()`` 以 0.6 的权重采信，等于
        **任何命盘的置信度都被这一个常数锚定**——换命盘、换数据都不变。

        现按输入里真实存在的证据字典计算闭合度：line_position（爻位证据）、
        time_state（时间证据）、element_state（五行证据）三组，
        逐字段统计已填充且非退化（None / 空 dict / 全 0）的比例。
        该口径**可复现、可解释**，且随输入变化。

        说明：原设计意图是「从 algorithm_rules 表查询」（见旧注释）。
        该表在本仓不存在，与 hexagram_state_definitions 同属**待建**资源，
        故此处采用上述可计算口径并在此明确标注，勿误当作既定规格。
        """
        groups = (
            (getattr(self.input, "line_position", None), ("active_line", "position_type", "yinyang")),
            (getattr(self.input, "time_state", None), ("solar_term", "hour", "true_solar_time")),
            (getattr(self.input, "element_state", None), ("木", "火", "土", "金", "水")),
        )
        total = filled = 0
        for container, keys in groups:
            for key in keys:
                total += 1
                val = container.get(key) if isinstance(container, dict) else None
                if val is None:
                    continue
                # 全 0 的数值证据视为未填充（如 element_state 五行皆 0）。
                # 注意 bool 是 int 的子类，False 是**合法**取值
                # （如 true_solar_time=False），不可按 falsy 数字剔除。
                if isinstance(val, bool):
                    filled += 1
                    continue
                if isinstance(val, (int, float)) and not val:
                    continue
                if isinstance(val, str) and not val.strip():
                    continue
                filled += 1
        return round(filled / total, 4) if total else 0.0
    
    def _compute_input_completeness(self) -> float:
        """计算输入完整性。"""
        required_fields = [
            "prenatal_hexagram", "yuan_tang", "postnatal_hexagram",
            "year_cycle", "month_cycle", "day_cycle"
        ]
        
        present = sum(1 for f in required_fields if getattr(self.input, f, None))
        return present / len(required_fields)
    
    def _generate_current_state(self) -> str:
        """生成当前状态描述。"""
        parts = []
        
        # 本命卦
        parts.append(f"本命卦{self.input.prenatal_hexagram}")
        
        # 元堂
        parts.append(f"元堂{self.input.yuan_tang}")
        
        # 时间状态
        if self.input.time_state.get("solar_term"):
            parts.append(f"时逢{self.input.time_state['solar_term']}")
        
        # 综合
        score = self._compute_total_score(FACTOR_WEIGHTS)
        if score > 0.3:
            parts.append("运势通畅")
        elif score > 0:
            parts.append("运势平稳")
        else:
            parts.append("运势需慎")
        
        return "，".join(parts) + "。"
    
    def _summarize_input(self) -> Dict[str, Any]:
        """输入摘要。"""
        return {
            "hexagram": self.input.prenatal_hexagram,
            "yuan_tang": self.input.yuan_tang,
            "year": self.input.year_cycle,
            "month": self.input.month_cycle,
            "day": self.input.day_cycle
        }


# ═══════════════════════════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════════════════════════
def interpret(input_data: HeluoInput) -> InterpretationOutput:
    """便捷函数：执行关系解释。"""
    engine = RelationalInterpretationEngine(input_data)
    return engine.compute()


if __name__ == "__main__":
    # 测试示例
    test_input = HeluoInput(
        prenatal_hexagram="乾上乾下",
        yuan_tang="五爻",
        postnatal_hexagram="乾上坤下",
        day_hexagram="屯上蒙下",
        year_cycle="乙巳",
        month_cycle="甲申",
        day_cycle="丙午",
        element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
        line_position={"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
        time_state={"solar_term": "立秋", "hour": 14, "true_solar_time": True}
    )
    
    result = interpret(test_input)
    
    print(json.dumps({
        "current_state": result.current_state,
        "opportunity": {
            "type": result.opportunity.type,
            "strength": result.opportunity.strength,
            "time_window": result.opportunity.time_window,
            "classical_basis": result.opportunity.classical_basis
        },
        "risk": {
            "type": result.risk.type,
            "severity": result.risk.severity,
            "trigger_condition": result.risk.trigger_condition,
            "classical_basis": result.risk.classical_basis
        },
        "recommended_action": {
            "primary": result.recommended_action.primary,
            "secondary": result.recommended_action.secondary,
            "avoid": result.recommended_action.avoid,
            "confidence": result.recommended_action.confidence
        },
        "interpretation_chain": [
            {"step": s.step, "logic": s.logic, "source": s.source}
            for s in result.interpretation_chain
        ],
        "warnings": result.warnings,
        "meta": result.meta
    }, ensure_ascii=False, indent=2))
