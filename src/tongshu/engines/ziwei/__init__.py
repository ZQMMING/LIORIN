"""紫微斗数引擎包。

对外统一入口，按三层架构组织：

    算层（Calculation）
        ZiweiEngine / ZiweiChart / FrozenZiweiChart
        确定性排盘（iztro），产出纯事实，不含判断。

    辨层（State / Signal）
        compute_multi_method_signals — 南北两派多方法信号
        两派平行归位，不投票、不融合。

    解层（Interpretation）
        build_life_reading        — 人生十二维度断语（累积大运/流年/流月/流日）
        build_answer              — 答案层分层输出（12 宫位维 + 体用层；南派+北派规则归位）
        build_domain_readings     — 十二宫逐宫综合解读 + 领域聚合
        ZiweiEvidenceProducer     — 证据生产者

用法：
    from tongshu.engines.ziwei_engine import ZiweiEngine
    from tongshu.engines.ziwei import (
        compute_multi_method_signals, build_life_reading,
        build_answer, build_domain_readings,
    )

    eng = ZiweiEngine()
    chart = eng.full_chart((1983, 9, 29), 12, "female")
    sig = compute_multi_method_signals(chart)
    reading = build_life_reading(chart, sig, target_year=2026)
    answer = build_answer(chart)
    domains = build_domain_readings(chart, eng.get_all_zihua(chart))
"""
from __future__ import annotations

from .evidence_producer import ZiweiEvidenceProducer

# ── 解层便捷入口（lazy 转发，避免包导入期拉起重依赖）──────────────
# Z80-E：answer_layer 分层输出 —— dimensions 仅 12 宫位维（与 interpretation
# 的 12 人生维度 1:1 对齐）；格局/应期/四化体用 归入独立字段 body_use（体用层）。
# ANSWER_DIMENSIONS 语义已修正为「12 宫位维」。
from .rules.answer_layer import PALACE_DIMENSIONS as ANSWER_DIMENSIONS
from .rules.answer_layer import BODY_USE_KEYS as ANSWER_BODY_USE_KEYS
from .rules.answer_layer import DIMENSIONS as LEGACY_ANSWER_DIMENSIONS
from .rules.answer_layer import build_answer
from .rules.classical_detail import build_classical_detail
from .rules.domain_reading import build_domain_readings
from .rules.interpretation import build_life_reading
from .rules.multi_method import compute_multi_method_signals

__all__ = [
    # 算层
    "ZiweiEvidenceProducer",
    # 辨层
    "compute_multi_method_signals",
    # 解层
    "build_life_reading",
    "build_answer",
    "build_domain_readings",
    "build_classical_detail",
    "ANSWER_DIMENSIONS",
    "ANSWER_BODY_USE_KEYS",
    "LEGACY_ANSWER_DIMENSIONS",
]
