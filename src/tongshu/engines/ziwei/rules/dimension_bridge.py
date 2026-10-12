# -*- coding: utf-8 -*-
"""Z80-B: 八维/十二维体系对齐桥。

背景
----
引擎历史上存在两套并行、互不知晓的维度体系：

    ┌─ answer_layer.DIMENSIONS（8 维，Z74d）
    │    性格 / 格局 / 事业 / 婚姻 / 财运 / 健康 / 应期 / 四化体用
    │    输入：南北两派规则命中；输出：逐维平行答案条目
    │
    └─ interpretation.DIMENSION_ORDER（12 维）
         性情禀赋 / 交游人际 / 婚姻配偶 / 子女 / 财帛 / 身体疾厄 /
         迁移出行 / 事业功名 / 田宅家业 / 福德精神 / 父母长辈 / 才艺学业
         输入：chart + 多层四化；输出：逐维综合断语

二者语义**部分重叠但不相等**（如 8 维的「格局」「应期」「四化体用」
在 12 维中无对应宫位维度）。因此不能简单合并，只能**建立映射桥**：

- 8 维条目 → 按映射表归入 12 维（一对多）
- 无对应的 8 维项（格局/应期/四化体用）→ 归入 `cross_dimension` 跨维结论池
- 12 维中无 8 维来源的（子女/父母/田宅/迁移等）→ 保持 12 维自身产出

设计约束
--------
1. **不改两侧契约**：answer_layer 的 8 维、interpretation 的 12 维对外均不变。
2. **单向桥**：只做 8 → 12 的投射，不反向污染 8 维。
3. **不丢信息**：无法归位的项进 `cross_dimension`，不静默丢弃。
4. **可审计**：每条投射保留来源 rule_id 与 source 派别。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# ============================================================================
# 8 维 → 12 维 映射表
# ============================================================================

# 键 = answer_layer 的 8 维名，值 = 对应的 12 维名列表（一对多）
ANSWER_TO_READING_DIMENSION: Dict[str, List[str]] = {
    # 性格 → 性情禀赋（命宫）+ 福德精神（内心）
    "性格":   ["性情禀赋", "福德精神"],
    # 事业 → 事业功名 + 迁移出行（事业与外出常互涉）
    "事业":   ["事业功名", "迁移出行"],
    # 婚姻 → 婚姻配偶
    "婚姻":   ["婚姻配偶"],
    # 财运 → 财帛 + 田宅家业（财与产同源）
    "财运":   ["财帛", "田宅家业"],
    # 健康 → 身体疾厄 + 福德精神（身心互涉）
    "健康":   ["身体疾厄", "福德精神"],
    # 以下三维在 12 维宫位体系中**无对应维度**，归入跨维结论池：
    #   格局    — 整体格局，非单一宫位
    #   应期    — 时间维度，非宫位维度
    #   四化体用 — 钦天结构方法，非宫位维度
}

# 无 12 维对应的 8 维项（显式声明，防遗漏）
CROSS_DIMENSION_KEYS: List[str] = ["格局", "应期", "四化体用"]


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class CrossDimensionItem:
    """无法归入单一 12 维的跨维条目。"""
    dimension: str        # 原 8 维名
    source: str           # sanhe / qintian
    rule_id: str
    text: str
    evidence_grade: int = 1

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "source": self.source,
            "rule_id": self.rule_id,
            "text": self.text,
            "evidence_grade": self.evidence_grade,
        }


@dataclass
class DimensionAlignment:
    """一次对齐的结果。

    Attributes:
        by_dimension: {12维名: [投射来的答案条目 dict]}
        cross_dimension: 无 12 维对应的 8 维条目池
        coverage: 映射统计
    """
    by_dimension: Dict[str, List[dict]] = field(default_factory=dict)
    cross_dimension: List[CrossDimensionItem] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "by_dimension": self.by_dimension,
            "cross_dimension": [c.to_dict() for c in self.cross_dimension],
            "coverage": self.coverage,
        }


# ============================================================================
# 主函数
# ============================================================================

def align_answer_to_dimensions(
    answer: dict,
    dimension_order: List[str] | None = None,
) -> DimensionAlignment:
    """把 answer_layer 的 8 维答案投射到 12 维体系。

    Args:
        answer: `answer_layer.build_answer()` 的返回值
                （须含 "answer": {8维名: [条目]}）
        dimension_order: 12 维顺序；默认取 interpretation.DIMENSION_ORDER

    Returns:
        DimensionAlignment

    用法:
        from tongshu.engines.ziwei.rules.answer_layer import build_answer
        from tongshu.engines.ziwei.rules.dimension_bridge import (
            align_answer_to_dimensions,
        )

        answer = build_answer(chart)
        aligned = align_answer_to_dimensions(answer)
        aligned.by_dimension["性情禀赋"]   # ← 8 维「性格」投射来的条目
        aligned.cross_dimension            # ← 格局/应期/四化体用
    """
    if dimension_order is None:
        from .interpretation import DIMENSION_ORDER
        dimension_order = DIMENSION_ORDER

    by_dim: Dict[str, List[dict]] = {d: [] for d in dimension_order}
    cross: List[CrossDimensionItem] = []
    mapped_items = 0
    cross_items = 0

    answer_map = (answer or {}).get("answer", {}) or {}

    # ── 1. 有 12 维对应的 8 维：一对多投射（深拷贝，防下游改写污染 8 维）──
    for ans_dim, targets in ANSWER_TO_READING_DIMENSION.items():
        items = answer_map.get(ans_dim, []) or []
        for it in items:
            for tgt in targets:
                if tgt not in by_dim:
                    continue
                by_dim[tgt].append({
                    "from_answer_dimension": ans_dim,
                    "source": it.get("source", ""),
                    "rule_id": it.get("rule_id", ""),
                    "text": it.get("text", ""),
                    "evidence_grade": it.get("evidence_grade", 1),
                })
                mapped_items += 1

    # ── 2. 无 12 维对应的 8 维：进跨维池 ──
    for ans_dim in CROSS_DIMENSION_KEYS:
        for it in answer_map.get(ans_dim, []) or []:
            cross.append(CrossDimensionItem(
                dimension=ans_dim,
                source=it.get("source", ""),
                rule_id=it.get("rule_id", ""),
                text=it.get("text", ""),
                evidence_grade=it.get("evidence_grade", 1),
            ))
            cross_items += 1

    # ── 3. 映射完整性校验：8 维必须全部有归宿 ──
    declared = set(ANSWER_TO_READING_DIMENSION) | set(CROSS_DIMENSION_KEYS)
    actual = set(answer_map.keys())
    unmapped = actual - declared
    if unmapped:
        # 未声明的新维度不得静默丢弃 —— 全部进跨维池并记录
        for ans_dim in sorted(unmapped):
            for it in answer_map.get(ans_dim, []) or []:
                cross.append(CrossDimensionItem(
                    dimension=ans_dim,
                    source=it.get("source", ""),
                    rule_id=it.get("rule_id", ""),
                    text=it.get("text", ""),
                    evidence_grade=it.get("evidence_grade", 1),
                ))
                cross_items += 1

    coverage = {
        "answer_dimensions": len(actual),
        "mapped_answer_dimensions": len(set(ANSWER_TO_READING_DIMENSION) & actual),
        "cross_dimension_dimensions": len(set(CROSS_DIMENSION_KEYS) & actual),
        "unmapped_dimensions": sorted(unmapped),
        "mapped_items": mapped_items,
        "cross_items": cross_items,
        "reading_dimensions_covered": sorted(
            d for d, v in by_dim.items() if v
        ),
        "reading_dimensions_empty": sorted(
            d for d, v in by_dim.items() if not v
        ),
    }

    return DimensionAlignment(
        by_dimension=by_dim,
        cross_dimension=cross,
        coverage=coverage,
    )


__all__ = [
    "ANSWER_TO_READING_DIMENSION",
    "CROSS_DIMENSION_KEYS",
    "CrossDimensionItem",
    "DimensionAlignment",
    "align_answer_to_dimensions",
]
