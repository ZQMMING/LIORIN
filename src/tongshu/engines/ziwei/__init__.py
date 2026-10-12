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
        build_answer              — 答案层八维度平行答案（南派+北派规则归位）
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
from .rules.answer_layer import DIMENSIONS as ANSWER_DIMENSIONS
from .rules.answer_layer import build_answer
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
    "ANSWER_DIMENSIONS",
]
