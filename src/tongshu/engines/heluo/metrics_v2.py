# -*- coding: utf-8 -*-
"""
S6-03: Interpretation Quality Score 评估体系

维度:
1. Classical Alignment (古籍一致性) - 30%
2. Logic Completeness (逻辑完整性) - 25%
3. Stability Score (稳定性) - 25%
4. Evidence Closure (证据闭合度) - 20%

目标: 为每个解释输出提供可量化的质量评分
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """质量等级。"""
    EXCELLENT = "excellent"   # >= 0.90
    GOOD = "good"            # >= 0.75
    ACCEPTABLE = "acceptable"  # >= 0.60
    NEEDS_REVIEW = "needs_review"  # < 0.60


@dataclass
class InterpretationQualityScore:
    """解释质量评分结果。"""
    # 总分
    overall_score: float
    quality_level: str
    
    # 各维度得分
    classical_alignment: float       # 古籍一致性
    logic_completeness: float        # 逻辑完整性
    stability_score: float           # 稳定性
    evidence_closure: float          # 证据闭合度
    
    # 详细指标
    classical_sources_matched: int
    classical_sources_total: int
    required_fields_present: int
    required_fields_total: int
    evidence_chains_complete: int
    evidence_chains_total: int
    interpretation_depth: int
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# 必需的字段
REQUIRED_INTERPRETATION_FIELDS = {
    "current_state": "当前状态描述",
    "opportunity": "机会因子",
    "risk": "风险因子",
    "recommended_action": "建议行动",
    "classical_reference": "古籍引用"
}

# 字典对齐权重
DIMENSION_WEIGHTS = {
    "classical_alignment": 0.30,
    "logic_completeness": 0.25,
    "stability_score": 0.25,
    "evidence_closure": 0.20
}


def evaluate_interpretation(
    interpretation: Dict[str, Any],
    classical_source: Optional[Dict] = None,
    evidence_chain: Optional[List[Dict]] = None,
    reference_outputs: Optional[List[Dict]] = None
) -> InterpretationQualityScore:
    """
    评估单个解释输出的质量。
    
    Args:
        interpretation: 解释输出字典
        classical_source: 古籍来源信息
        evidence_chain: 证据链条
        reference_outputs: 参考输出列表（用于稳定性计算）
    
    Returns:
        InterpretationQualityScore
    """
    if not interpretation:
        return _empty_score()
    
    # 计算各维度得分
    classical_score = _calc_classical_alignment(interpretation, classical_source)
    logic_score = _calc_logic_completeness(interpretation)
    stability_score = _calc_stability(interpretation, reference_outputs)
    evidence_score = _calc_evidence_closure(interpretation, evidence_chain)
    
    # 加权总分
    overall = (
        classical_score * DIMENSION_WEIGHTS["classical_alignment"] +
        logic_score * DIMENSION_WEIGHTS["logic_completeness"] +
        stability_score * DIMENSION_WEIGHTS["stability_score"] +
        evidence_score * DIMENSION_WEIGHTS["evidence_closure"]
    )
    
    # 确定质量等级
    quality_level = _get_quality_level(overall)
    
    # 生成警告和建议
    warnings = _generate_warnings(interpretation, classical_score, logic_score, evidence_score)
    # ⚠ 2026-10-22：下列三项是**占位分**，不是实测结论，此前静默抬高总分
    #   （无参考输出 → 稳定性直接给 1.0 满分），使用者无从分辨
    #   「实测很好」与「根本没测」。现逐项留痕。
    if not classical_source:
        warnings.append("古籍一致性未实测（未提供 classical_source），0.5 为占位分，不得当作实测结论")
    if not reference_outputs:
        warnings.append("稳定性未实测（未提供 reference_outputs），1.0 为占位分，不得当作实测结论")
    if not evidence_chain:
        warnings.append("证据闭合度未实测（未提供 evidence_chain），占位分，不得当作实测结论")
    suggestions = _generate_suggestions(interpretation, overall)
    
    # 统计详细指标
    source_matched = _count_classical_matches(interpretation, classical_source)
    fields_present = _count_present_fields(interpretation)
    evidence_complete = _count_complete_evidence(interpretation, evidence_chain)
    
    return InterpretationQualityScore(
        overall_score=round(overall, 4),
        quality_level=quality_level,
        classical_alignment=round(classical_score, 4),
        logic_completeness=round(logic_score, 4),
        stability_score=round(stability_score, 4),
        evidence_closure=round(evidence_score, 4),
        classical_sources_matched=source_matched[0],
        classical_sources_total=source_matched[1],
        required_fields_present=fields_present[0],
        required_fields_total=fields_present[1],
        evidence_chains_complete=evidence_complete[0],
        evidence_chains_total=evidence_complete[1],
        interpretation_depth=len(_get_interpretation_chain(interpretation)),
        warnings=warnings,
        suggestions=suggestions
    )


def evaluate_dataset(
    dataset: List[Dict],
    classical_sources: Optional[Dict] = None,
    evidence_chains: Optional[List[List[Dict]]] = None
) -> Dict[str, Any]:
    """
    评估整个数据集的质量。
    
    Args:
        dataset: 解释输出列表
        classical_sources: 古籍来源映射
        evidence_chains: 证据链列表
    
    Returns:
        数据集评估结果
    """
    if not dataset:
        return {"error": "Empty dataset"}
    
    scores = []
    for i, case in enumerate(dataset):
        interpretation = case.get("interpretation", {})
        classical = classical_sources.get(case.get("case_id")) if classical_sources else None
        evidence = evidence_chains[i] if evidence_chains else None
        reference = case.get("reference_outputs", [])
        
        score = evaluate_interpretation(
            interpretation,
            classical,
            evidence,
            reference
        )
        scores.append(score)
    
    # 计算统计数据
    avg_overall = sum(s.overall_score for s in scores) / len(scores)
    avg_classical = sum(s.classical_alignment for s in scores) / len(scores)
    avg_logic = sum(s.logic_completeness for s in scores) / len(scores)
    avg_stability = sum(s.stability_score for s in scores) / len(scores)
    avg_evidence = sum(s.evidence_closure for s in scores) / len(scores)
    
    # 质量分布
    excellent = sum(1 for s in scores if s.quality_level == "excellent")
    good = sum(1 for s in scores if s.quality_level == "good")
    acceptable = sum(1 for s in scores if s.quality_level == "acceptable")
    needs_review = sum(1 for s in scores if s.quality_level == "needs_review")
    
    return {
        "total_cases": len(dataset),
        "average_overall_score": round(avg_overall, 4),
        "dimension_scores": {
            "classical_alignment": round(avg_classical, 4),
            "logic_completeness": round(avg_logic, 4),
            "stability": round(avg_stability, 4),
            "evidence_closure": round(avg_evidence, 4)
        },
        "quality_distribution": {
            "excellent": excellent,
            "good": good,
            "acceptable": acceptable,
            "needs_review": needs_review
        },
        "pass_rate": round((excellent + good) / len(dataset) * 100, 2)
    }


def _empty_score() -> InterpretationQualityScore:
    """返回空评估结果。"""
    return InterpretationQualityScore(
        overall_score=0.0,
        quality_level=QualityLevel.NEEDS_REVIEW.value,
        classical_alignment=0.0,
        logic_completeness=0.0,
        stability_score=0.0,
        evidence_closure=0.0,
        classical_sources_matched=0,
        classical_sources_total=0,
        required_fields_present=0,
        required_fields_total=len(REQUIRED_INTERPRETATION_FIELDS),
        evidence_chains_complete=0,
        evidence_chains_total=0,
        interpretation_depth=0,
        warnings=["Empty interpretation"],
        suggestions=["Provide complete interpretation output"]
    )


def _calc_classical_alignment(
    interpretation: Dict,
    classical_source: Optional[Dict]
) -> float:
    """计算古籍一致性得分。

    ⚠ 2026-10-22 留痕：**没有 classical_source 时返回 0.5 是占位分**，
    不是实测结论；调用方会在 warnings 里标注该分未实测。
    """
    if not classical_source:
        return 0.5  # ⚠ 占位分：未实测
    
    # 检查古籍引用是否存在
    ref = interpretation.get("classical_reference", {})
    if not ref:
        return 0.3
    
    # 检查匹配程度
    matched = 0
    total = 0
    
    # 书籍匹配
    total += 1
    if ref.get("book") == classical_source.get("book_name"):
        matched += 1
    
    # 卷数匹配
    total += 1
    if ref.get("volume") == classical_source.get("volume"):
        matched += 1
    
    # 段落匹配
    total += 1
    if ref.get("paragraph") and classical_source.get("original_text"):
        if ref["paragraph"] in classical_source["original_text"]:
            matched += 1
    
    # 规则匹配
    total += 1
    if ref.get("rule") and classical_source.get("normalized_rule"):
        if ref["rule"] == classical_source["normalized_rule"]:
            matched += 1
    
    return matched / total if total > 0 else 0.0


def _calc_logic_completeness(interpretation: Dict) -> float:
    """计算逻辑完整性得分。"""
    if not interpretation:
        return 0.0
    
    present = 0
    total = len(REQUIRED_INTERPRETATION_FIELDS)
    
    for field_name in REQUIRED_INTERPRETATION_FIELDS:
        value = interpretation.get(field_name)
        if value is not None and str(value).strip():
            present += 1
    
    return present / total if total > 0 else 0.0


def _calc_stability(
    interpretation: Dict,
    reference_outputs: Optional[List[Dict]]
) -> float:
    """计算稳定性得分。

    ⚠ 2026-10-22 留痕：**没有参考输出时返回 1.0 是占位分，不是实测结论**
    ——「没测过」不等于「很稳定」。调用方（:func:`evaluate_interpretation`）
    会在 warnings 里显式标注该分未实测，不得据此下判断。
    """
    if not reference_outputs:
        return 1.0  # ⚠ 占位分：未实测，非「满分」
    
    # 计算与参考输出的相似度
    similarities = []
    for ref in reference_outputs:
        sim = _calculate_similarity(interpretation, ref)
        similarities.append(sim)
    
    return sum(similarities) / len(similarities) if similarities else 1.0


def _calc_evidence_closure(
    interpretation: Dict,
    evidence_chain: Optional[List[Dict]]
) -> float:
    """计算证据闭合度得分。"""
    if not evidence_chain:
        return 0.5  # 无证据链，默认中等
    
    # 检查证据链完整性
    complete = 0
    total = len(evidence_chain)
    
    for step in evidence_chain:
        if _is_evidence_complete(step):
            complete += 1
    
    return complete / total if total > 0 else 0.0


def _get_quality_level(score: float) -> str:
    """根据总分确定质量等级。"""
    if score >= 0.90:
        return QualityLevel.EXCELLENT.value
    elif score >= 0.75:
        return QualityLevel.GOOD.value
    elif score >= 0.60:
        return QualityLevel.ACCEPTABLE.value
    else:
        return QualityLevel.NEEDS_REVIEW.value


def _generate_warnings(
    interpretation: Dict,
    classical_score: float,
    logic_score: float,
    evidence_score: float
) -> List[str]:
    """生成警告信息。"""
    warnings = []
    
    if classical_score < 0.5:
        warnings.append("古籍引用不完整，建议补充经典原文")
    if logic_score < 0.7:
        warnings.append("解释缺少必要字段，请检查完整性")
    if evidence_score < 0.6:
        warnings.append("证据链不完整，建议补充中间推导步骤")
    
    return warnings


def _generate_suggestions(
    interpretation: Dict,
    overall_score: float
) -> List[str]:
    """生成改进建议。"""
    suggestions = []
    
    if overall_score < 0.75:
        suggestions.append("建议人工审核此案例")
    
    if interpretation.get("recommended_action") and len(str(interpretation["recommended_action"])) < 10:
        suggestions.append("建议行动过于简短，需补充详细说明")
    
    return suggestions


def _count_classical_matches(
    interpretation: Dict,
    classical_source: Optional[Dict]
) -> tuple:
    """统计古籍匹配情况。"""
    if not classical_source:
        return (0, 1)
    
    ref = interpretation.get("classical_reference", {})
    matched = 0
    total = 4  # book, volume, paragraph, rule
    
    if ref.get("book") == classical_source.get("book_name"):
        matched += 1
    if ref.get("volume") == classical_source.get("volume"):
        matched += 1
    if ref.get("paragraph") and classical_source.get("original_text"):
        if ref["paragraph"] in classical_source["original_text"]:
            matched += 1
    if ref.get("rule") and classical_source.get("normalized_rule"):
        if ref["rule"] == classical_source["normalized_rule"]:
            matched += 1
    
    return (matched, total)


def _count_present_fields(interpretation: Dict) -> tuple:
    """统计present的必需字段。"""
    present = 0
    total = len(REQUIRED_INTERPRETATION_FIELDS)
    
    for field_name in REQUIRED_INTERPRETATION_FIELDS:
        value = interpretation.get(field_name)
        if value is not None and str(value).strip():
            present += 1
    
    return (present, total)


def _count_complete_evidence(
    interpretation: Dict,
    evidence_chain: Optional[List[Dict]]
) -> tuple:
    """统计完整证据链数量。"""
    if not evidence_chain:
        return (0, 1)
    
    complete = 0
    for step in evidence_chain:
        if _is_evidence_complete(step):
            complete += 1
    
    return (complete, len(evidence_chain))


def _is_evidence_complete(step: Dict) -> bool:
    """检查单步证据是否完整。"""
    required = ["source_type", "source_text", "reasoning", "conclusion"]
    return all(step.get(k) for k in required)


def _get_interpretation_chain(interpretation: Dict) -> List[str]:
    """获取解释链的深度。"""
    chain = []
    current = interpretation
    
    while isinstance(current, dict):
        for key in ["current_state", "opportunity", "risk", "recommended_action"]:
            if key in current:
                chain.append(key)
        break
    
    return chain


def _calculate_similarity(
    interpretation1: Dict,
    interpretation2: Dict
) -> float:
    """计算两个解释输出的相似度。"""
    if not interpretation1 or not interpretation2:
        return 0.0
    
    # 只比较value，避免key值干扰
    values1 = {str(v).lower() for v in interpretation1.values() if v}
    values2 = {str(v).lower() for v in interpretation2.values() if v}
    
    if not values1 and not values2:
        return 1.0
    
    intersection = values1 & values2
    union = values1 | values2
    
    return len(intersection) / len(union) if union else 0.0


# 便捷函数
def evaluate_case(
    case: Dict,
    classical_source: Optional[Dict] = None,
    evidence_chain: Optional[List[Dict]] = None
) -> InterpretationQualityScore:
    """评估单个案例。"""
    interpretation = case.get("interpretation", {})
    reference = case.get("reference_outputs", [])
    return evaluate_interpretation(interpretation, classical_source, evidence_chain, reference)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试示例
    test_interpretation = {
        "current_state": "乾卦主事，阳气旺盛",
        "opportunity": {
            "type": "事业",
            "strength": 0.85,
            "description": "创业良机，宜主动进取"
        },
        "risk": {
            "type": "健康",
            "severity": 0.3,
            "description": "注意劳逸结合"
        },
        "recommended_action": "把握机遇，稳步前行",
        "classical_reference": {
            "book": "河洛理数",
            "volume": "卷一",
            "paragraph": "乾卦初九",
            "rule": "潜龙勿用"
        }
    }
    
    test_classical_source = {
        "book_name": "河洛理数",
        "volume": "卷一",
        "original_text": "乾卦初九，潜龙勿用",
        "normalized_rule": "潜龙勿用"
    }
    
    test_evidence_chain = [
        {"source_type": "rule", "source_text": "乾上乾下", "reasoning": "本命卦", "conclusion": "基础定位"},
        {"source_type": "calculation", "source_text": "阳男顺排", "reasoning": "大运方向", "conclusion": "推演依据"}
    ]
    
    score = evaluate_interpretation(
        test_interpretation,
        test_classical_source,
        test_evidence_chain
    )
    
    print("=" * 50)
    print("解释质量评估结果")
    print("=" * 50)
    print(f"总分: {score.overall_score:.4f}")
    print(f"质量等级: {score.quality_level}")
    print(f"\n维度得分:")
    print(f"  古籍一致性: {score.classical_alignment:.4f}")
    print(f"  逻辑完整性: {score.logic_completeness:.4f}")
    print(f"  稳定性: {score.stability_score:.4f}")
    print(f"  证据闭合度: {score.evidence_closure:.4f}")
    print(f"\n详细指标:")
    print(f"  古籍匹配: {score.classical_sources_matched}/{score.classical_sources_total}")
    print(f"  字段完整: {score.required_fields_present}/{score.required_fields_total}")
    print(f"  证据完整: {score.evidence_chains_complete}/{score.evidence_chains_total}")
    print(f"  解释深度: {score.interpretation_depth}")
    if score.warnings:
        print(f"\n警告: {score.warnings}")
    if score.suggestions:
        print(f"建议: {score.suggestions}")
