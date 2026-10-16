"""P1.5: HEXAGRAM_STATE_ENGINE 卦象状态引擎

计算卦象的状态因子:
- 动静状态 (静/动/变/互)
- 旺衰状态 (得令/失令)
- 体用关系 (体卦/用卦)
- 机会因子
- 风险因子
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════════════════════════
TRIGRAM_NAMES = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}

ELEMENT_NAMES = {
    "木": 1, "火": 2, "土": 3, "金": 4, "水": 5
}

# 五行生克关系
ELEMENT_GENERATES = {
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
}

ELEMENT_OVERCOMES = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
}


# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════
@dataclass
class HexagramState:
    """卦象状态定义。"""
    hexagram_id: str           # 如 "乾上乾下"
    state_type: str            # 静/动/变/互
    state_description: str
    opportunity_factor: float  # 0-1
    risk_factor: float         # 0-1
    element_bonus: dict        # 五行加成


@dataclass
class StateCalculationResult:
    """状态计算结果。"""
    hexagram: str
    state_type: str
    opportunity: float
    risk: float
    element_modifier: float
    net_factor: float
    interpretation: str


# ═══════════════════════════════════════════════════════════════════
# 核心算法
# ═══════════════════════════════════════════════════════════════════
def calculate_hexagram_state(
    hexagram: str,
    state_type: str = "静",
    element_state: Optional[dict] = None,
    month_branch: Optional[str] = None
) -> StateCalculationResult:
    """
    计算卦象状态。
    
    Args:
        hexagram: 卦象标识（如 "乾上乾下"）
        state_type: 状态类型（静/动/变/互）
        element_state: 五行状态 {木: 0.6, 火: 0.8, ...}
        month_branch: 月支（用于判断旺衰）
    
    Returns:
        StateCalculationResult
    """
    # 1. 基础因子（来自规则库）
    base_opportunity, base_risk = get_base_factors(hexagram, state_type)
    
    # 2. 五行修正
    element_modifier = calculate_element_modifier(element_state, month_branch)
    
    # 3. 净因子计算
    net_factor = base_opportunity - base_risk + element_modifier
    
    # 4. 解释生成
    interpretation = generate_interpretation(
        hexagram, state_type, base_opportunity, base_risk, element_modifier
    )
    
    return StateCalculationResult(
        hexagram=hexagram,
        state_type=state_type,
        opportunity=max(0, base_opportunity + element_modifier),
        risk=max(0, base_risk - element_modifier),
        element_modifier=round(element_modifier, 3),
        net_factor=round(net_factor, 3),
        interpretation=interpretation
    )


def get_base_factors(hexagram: str, state_type: str) -> Tuple[float, float]:
    """
    获取基础机会/风险因子。
    
    TODO: 从 hexagram_state_definitions 表读取
    """
    # 简化版规则
    if state_type == "静":
        return 0.5, 0.3
    elif state_type == "动":
        return 0.7, 0.4
    elif state_type == "变":
        return 0.6, 0.5
    elif state_type == "互":
        return 0.4, 0.3
    else:
        return 0.5, 0.3


def calculate_element_modifier(
    element_state: Optional[dict],
    month_branch: Optional[str]
) -> float:
    """
    计算五行修正因子。
    
    规则:
    - 当令（月支五行）: +0.15
    - 相生（生当令）: +0.08
    - 相克（克当令）: -0.10
    - 被克（被当令克）: -0.12
    - 休囚（被当令生）: -0.05
    """
    if not element_state or not month_branch:
        return 0.0
    
    # 月支五行
    branch_element = get_branch_element(month_branch)
    if not branch_element:
        return 0.0
    
    # 计算修正
    modifier = 0.0
    
    for element, strength in element_state.items():
        if element == branch_element:
            modifier += strength * 0.15  # 当令
        elif ELEMENT_GENERATES.get(branch_element) == element:
            modifier += strength * 0.08  # 相生
        elif ELEMENT_OVERCOMES.get(branch_element) == element:
            modifier -= strength * 0.10  # 相克
        elif ELEMENT_GENERATES.get(element) == branch_element:
            modifier -= strength * 0.12  # 被克
        elif ELEMENT_OVERCOMES.get(element) == branch_element:
            modifier -= strength * 0.05  # 休囚
    
    return modifier


def get_branch_element(branch: str) -> Optional[str]:
    """获取地支五行。"""
    BRANCH_ELEMENTS = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    return BRANCH_ELEMENTS.get(branch)


def generate_interpretation(
    hexagram: str,
    state_type: str,
    opportunity: float,
    risk: float,
    element_modifier: float
) -> str:
    """生成自然语言解释。"""
    parts = []
    
    if opportunity > 0.6:
        parts.append(" opportunities available")
    elif opportunity > 0.4:
        parts.append(" moderate opportunities")
    else:
        parts.append(" limited opportunities")
    
    if risk > 0.5:
        parts.append(" and notable risks")
    elif risk > 0.3:
        parts.append(" and some risks")
    
    if element_modifier > 0.1:
        parts.append(" with favorable elemental support")
    elif element_modifier < -0.1:
        parts.append(" with unfavorable elemental conditions")
    
    return f"{hexagram} ({state_type}){(''.join(parts)) if parts else ' neutral'}. "


if __name__ == "__main__":
    # 测试
    result = calculate_hexagram_state(
        hexagram="乾上乾下",
        state_type="动",
        element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
        month_branch="午"
    )
    
    print(json.dumps({
        "hexagram": result.hexagram,
        "state_type": result.state_type,
        "opportunity": result.opportunity,
        "risk": result.risk,
        "element_modifier": result.element_modifier,
        "net_factor": result.net_factor,
        "interpretation": result.interpretation
    }, ensure_ascii=False, indent=2))
