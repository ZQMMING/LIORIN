# -*- coding: utf-8 -*-
"""Z80-E: 12 宫位维 / 12 人生维度 对齐桥（体用层分离）。

背景
----
引擎历史上存在两套并行、互不知晓的维度体系：

    ┌─ answer_layer（Z80-E 起分层输出）
    │    dimensions : 12 宫位维（命宫/兄弟/夫妻/子女/财帛/疾厄/
    │                          迁移/仆役/官禄/田宅/福德/父母）
    │    answer     : {宫位维 → 规则条目}
    │    body_use   : {格局/应期/四化体用 → 条目}  ← 体用层
    │
    └─ interpretation.DIMENSION_ORDER（12 维）
         性情禀赋 / 交游人际 / 婚姻配偶 / 子女 / 财帛 / 身体疾厄 /
         迁移出行 / 事业功名 / 田宅家业 / 福德精神 / 父母长辈 / 才艺学业
         输入：chart + 多层四化；输出：逐维综合断语

Z80-E 后，两侧**维度层同为「一宫一维」**，映射为 1:1 直连；「格局/应期/
四化体用」属**体用层**（横跨宫位），在 12 维中无对应，进 `cross_dimension`。

文献依据（见微·斗数术语精解）：
  · 「格局是本宫与三方四正……的组合体」→ 跨宫
  · 「命宫为体，其余十一宫为用；主星为体，副星、四化为用」→ 体用分层
  · 「本命盘为体，限运为用」→ 应期属时间层
所以体用项**不是第 13/14/15 个维度**，而是与宫位层并列的另一层。

映射规则
--------
- 12 宫位维 → 按 `PALACE_DIM_TO_READING` 1:1 直连至 12 维（仅名称翻译）
- 体用项（格局/应期/四化体用）→ 归入 `cross_dimension` 跨维结论池
- 兼容旧契约：8 维输入经 `ANSWER_TO_READING_DIMENSION` 兜底；Z80-D 的
  「议题维仍在 answer 里」情形亦被识别（见 align 函数第 3 步）

设计约束
--------
1. **单向桥**：只做 answer → 12 维的投射，不反向污染。
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

# 无 12 维对应的体用项（显式声明，防遗漏）
# Z80-E：原 CROSS_DIMENSION_KEYS，语义由「议题维」改称「体用项」
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
    """把 answer_layer 的答案投射到 12 维体系。

    Args:
        answer: `answer_layer.build_answer()` 的返回值。
                Z80-E 契约：
                  {"dimensions": [12 宫位维], "answer": {宫位维→条目},
                   "body_use": {格局/应期/四化体用→条目}, "summary": {...}}
                兼容旧契约：
                  - Z80-D：answer 键含 12 宫位维 + 3 议题维（无 body_use 字段）
                  - Z80-C 及之前：answer 键为 8 维（性格/事业/婚姻/财运/健康…）
        dimension_order: 12 维顺序；默认取 interpretation.DIMENSION_ORDER

    Returns:
        DimensionAlignment

    投射规则（Z80-E 分层）:
        - 12 宫位维（命宫/兄弟/…/父母）→ 经 PALACE_DIM_TO_READING 1:1 直连
        - 体用项（格局/应期/四化体用）→ 进 cross_dimension 跨维池
          （来源优先取 body_use 字段；旧契约下则从 answer 的议题维取）
        - 兼容旧 8 维输入（性格/事业/婚姻/财运/健康）→ 一对多兜底

    用法:
        from tongshu.engines.ziwei.rules.answer_layer import build_answer
        from tongshu.engines.ziwei.rules.dimension_bridge import (
            align_answer_to_dimensions,
        )

        answer = build_answer(chart)
        aligned = align_answer_to_dimensions(answer)
        aligned.by_dimension["性情禀赋"]   # ← 宫位维「命宫」投射来的条目
        aligned.cross_dimension            # ← 格局/应期/四化体用（体用层）
    """
    if dimension_order is None:
        from .interpretation import DIMENSION_ORDER
        dimension_order = DIMENSION_ORDER

    by_dim: Dict[str, List[dict]] = {d: [] for d in dimension_order}
    cross: List[CrossDimensionItem] = []
    mapped_items = 0
    cross_items = 0

    answer_map = (answer or {}).get("answer", {}) or {}
    body_use_map = (answer or {}).get("body_use", {}) or {}

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
        if ans_dim in PALACE_DIM_TO_READING:
            continue
        for it in answer_map.get(ans_dim, []) or []:
            for tgt in targets:
                _project(ans_dim, it, tgt)

    # ── 3. 体用项 → 跨维池 ──
    #     Z80-E：优先从独立字段 body_use 取；旧契约下从 answer 的议题维取。
    seen_body_use_keys = set()
    for key in CROSS_DIMENSION_KEYS:
        items_from_body_use = body_use_map.get(key, []) or []
        if items_from_body_use:
            seen_body_use_keys.add(key)
            for it in items_from_body_use:
                _to_cross(key, it)
    # 兼容 Z80-D：议题维仍留在 answer 里的情况（body_use 未提供时）
    for key in CROSS_DIMENSION_KEYS:
        if key in seen_body_use_keys:
            continue
        for it in answer_map.get(key, []) or []:
            _to_cross(key, it)

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
        "body_use_keys": sorted(
            k for k in CROSS_DIMENSION_KEYS
            if (body_use_map.get(k) or answer_map.get(k))
        ),
        "cross_dimension_dimensions": len(
            set(CROSS_DIMENSION_KEYS) & (actual | set(body_use_map))
        ),
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
