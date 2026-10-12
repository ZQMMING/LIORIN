# -*- coding: utf-8 -*-
"""Z80-D: 15 维 / 12 维体系对齐桥。

背景
----
引擎历史上存在两套并行、互不知晓的维度体系：

    ┌─ answer_layer.DIMENSIONS_15（15 维，Z80-D）
    │    12 宫位维：命宫 / 兄弟 / 夫妻 / 子女 / 财帛 / 疾厄 /
    │              迁移 / 仆役 / 官禄 / 田宅 / 福德 / 父母
    │    + 3 议题维：格局 / 应期 / 四化体用
    │    输入：南北两派规则命中；输出：逐维平行答案条目
    │    （Z80-C 及之前为 8 维「性格/格局/事业/婚姻/财运/健康/应期/四化体用」，
    │      按议题切；因桶数少于十二宫，导致多宫共挤一桶 + 归位错误）
    │
    └─ interpretation.DIMENSION_ORDER（12 维）
         性情禀赋 / 交游人际 / 婚姻配偶 / 子女 / 财帛 / 身体疾厄 /
         迁移出行 / 事业功名 / 田宅家业 / 福德精神 / 父母长辈 / 才艺学业
         输入：chart + 多层四化；输出：逐维综合断语

Z80-D 后，两侧**同为「一宫一维」口径**，映射退化为 1:1 直连；3 议题维
在 12 维中无对应宫位，进 `cross_dimension` 跨维结论池。

映射规则
--------
- 12 宫位维 → 按 `PALACE_DIM_TO_READING` 1:1 直连至 12 维（仅名称翻译）
- 3 议题维 → 归入 `cross_dimension` 跨维结论池
- 兼容旧 8 维输入 → 经 `ANSWER_TO_READING_DIMENSION` 一对多兜底（迁移期）

设计约束
--------
1. **单向桥**：只做 15 → 12 的投射，不反向污染 15 维。
2. **不丢信息**：无法归位的项进 `cross_dimension`，不静默丢弃。
3. **可审计**：每条投射保留来源 rule_id 与 source 派别。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# ============================================================================
# 15 维 → 12 维 映射表（Z80-D：一宫一维后，宫位维 1:1 直连）
# ============================================================================
#
# Z80-D 变更：answer_layer 已由 8 维升级为 15 维（12 宫位维 + 3 议题维）。
#   其中 12 宫位维与 interpretation 的 12 维**同构**（都是一宫一维），
#   故映射退化为 1:1 直连；3 议题维仍无 12 维对应，进跨维池。
#
# 命名差异说明（两套体系对同一宫用了不同维名）：
#   answer_layer 用「宫名」直接作维名（命宫/兄弟/夫妻/…）
#   interpretation 用「近义维名」（性情禀赋/交游人际/婚姻配偶/…）
# 二者指向同一宫，此表做名称翻译。

# 键 = answer_layer 15 维名（宫位维），值 = interpretation 12 维名（1:1）
PALACE_DIM_TO_READING: Dict[str, str] = {
    "命宫": "性情禀赋",
    "兄弟": "交游人际",
    "夫妻": "婚姻配偶",
    "子女": "子女",
    "财帛": "财帛",
    "疾厄": "身体疾厄",
    "迁移": "迁移出行",
    "仆役": "才艺学业",
    "官禄": "事业功名",
    "田宅": "田宅家业",
    "福德": "福德精神",
    "父母": "父母长辈",
}

# 兼容旧名：Z80-C 及之前的 8 维名 → 15 维宫位维列表
# 供下游迁移期使用（旧调用方若仍按 8 维名取数，可经此换算）。
ANSWER_TO_READING_DIMENSION: Dict[str, List[str]] = {
    "性格": ["性情禀赋", "福德精神"],
    "事业": ["事业功名", "迁移出行"],
    "婚姻": ["婚姻配偶"],
    "财运": ["财帛", "田宅家业"],
    "健康": ["身体疾厄", "福德精神"],
}

# 无 12 维对应的议题维（显式声明，防遗漏）
CROSS_DIMENSION_KEYS: List[str] = ["格局", "应期", "四化体用"]


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class CrossDimensionItem:
    """无法归入单一 12 维的跨维条目（议题维或未声明维）。"""
    dimension: str        # 15 维名（格局/应期/四化体用等）
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
    """把 answer_layer 的 15 维答案投射到 12 维体系。

    Args:
        answer: `answer_layer.build_answer()` 的返回值
                （须含 "answer": {15维名: [条目]}）
        dimension_order: 12 维顺序；默认取 interpretation.DIMENSION_ORDER

    Returns:
        DimensionAlignment

    投射规则（Z80-D）:
        - 12 宫位维（命宫/兄弟/…/父母）→ 经 PALACE_DIM_TO_READING 1:1 直连
        - 3 议题维（格局/应期/四化体用）→ 进 cross_dimension 跨维池
        - 兼容：若输入仍是 Z80-C 及之前的 8 维（性格/事业/婚姻/财运/健康），
          则经 ANSWER_TO_READING_DIMENSION 一对多兜底投射，行为与旧版一致。

    用法:
        from tongshu.engines.ziwei.rules.answer_layer import build_answer
        from tongshu.engines.ziwei.rules.dimension_bridge import (
            align_answer_to_dimensions,
        )

        answer = build_answer(chart)
        aligned = align_answer_to_dimensions(answer)
        aligned.by_dimension["性情禀赋"]   # ← 15 维「命宫」投射来的条目
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

    def _project(ans_dim: str, it: dict, tgt: str) -> None:
        """把单条答案条目投射到目标 12 维（深拷贝字段，防下游改写）。"""
        nonlocal mapped_items
        if tgt not in by_dim:
            return
        by_dim[tgt].append({
            "from_answer_dimension": ans_dim,
            "source": it.get("source", ""),
            "rule_id": it.get("rule_id", ""),
            "text": it.get("text", ""),
            "evidence_grade": it.get("evidence_grade", 1),
        })
        mapped_items += 1

    def _to_cross(ans_dim: str, it: dict) -> None:
        """把单条答案条目放入跨维池。"""
        nonlocal cross_items
        cross.append(CrossDimensionItem(
            dimension=ans_dim,
            source=it.get("source", ""),
            rule_id=it.get("rule_id", ""),
            text=it.get("text", ""),
            evidence_grade=it.get("evidence_grade", 1),
        ))
        cross_items += 1

    # ── 1. 12 宫位维 → 12 维：1:1 直连投射 ──
    for ans_dim, tgt in PALACE_DIM_TO_READING.items():
        for it in answer_map.get(ans_dim, []) or []:
            _project(ans_dim, it, tgt)

    # ── 2. 兼容旧 8 维名：一对多兜底投射（迁移期）──
    for ans_dim, targets in ANSWER_TO_READING_DIMENSION.items():
        # 若同一维名已按宫位维直连处理过，跳过（15 维新名与旧名不冲突，
        # 但防御性检查避免未来命名重叠导致重复投射）
        if ans_dim in PALACE_DIM_TO_READING:
            continue
        for it in answer_map.get(ans_dim, []) or []:
            for tgt in targets:
                _project(ans_dim, it, tgt)

    # ── 3. 3 议题维：进跨维池 ──
    for ans_dim in CROSS_DIMENSION_KEYS:
        for it in answer_map.get(ans_dim, []) or []:
            _to_cross(ans_dim, it)

    # ── 4. 映射完整性校验：凡未声明的维度一律进跨维池，不得静默丢弃 ──
    declared = (
        set(PALACE_DIM_TO_READING)
        | set(ANSWER_TO_READING_DIMENSION)
        | set(CROSS_DIMENSION_KEYS)
    )
    actual = set(answer_map.keys())
    unmapped = actual - declared
    for ans_dim in sorted(unmapped):
        for it in answer_map.get(ans_dim, []) or []:
            _to_cross(ans_dim, it)

    coverage = {
        "answer_dimensions": len(actual),
        "mapped_answer_dimensions": len(
            set(PALACE_DIM_TO_READING) & actual
        ) + len(set(ANSWER_TO_READING_DIMENSION) & actual),
        "palace_dimensions_mapped": sorted(
            set(PALACE_DIM_TO_READING) & actual
        ),
        "legacy_dimensions_mapped": sorted(
            set(ANSWER_TO_READING_DIMENSION) & actual
        ),
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
    "PALACE_DIM_TO_READING",
    "ANSWER_TO_READING_DIMENSION",
    "CROSS_DIMENSION_KEYS",
    "CrossDimensionItem",
    "DimensionAlignment",
    "align_answer_to_dimensions",
]
