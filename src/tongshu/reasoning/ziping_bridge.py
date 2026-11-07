"""ZIPING 辨层接线 — BAZI Chart → Judgment context → JudgmentFactory

架构位置 (V2 算→辨→解):
    BaziEngine.compute()  [算]
        ↓ BaziChart
    ZipingBridge.build_context()  [接线]
        ↓ NatalContext-dict
    JudgmentFactory.judge_all()  [辨]
        ↓ JudgmentSynthesis
    解层消费 (渲染/输出)

职责:
    1. 将 BaziChart 的四柱事实转换为 judgment.py 期望的 context 格式
    2. 调用 JudgmentFactory 生成五大域判断
    3. 返回 JudgmentSynthesis (含 rule_refs/evidence_refs 可追溯)

原则:
    - 只做数据转换，不做辨证判断 (BAZI 事实 → 判断层)
    - 确定性: 相同 BaziChart → 相同 judgment
    - Fail Closed: context 缺关键字段 → 返回 UNKNOWN，不强行判断
    - 不修改 BAZI 代码，只消费其字段
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .judgment import (
    JudgmentConclusion,
    JudgmentDomain,
    JudgmentFactory,
    JudgmentSynthesis,
)


def _pillar_dict(pillar: Any, position: str) -> Dict[str, str]:
    """Pillar → dict {position, heavenly_stem, earthly_branch}。"""
    return {
        "position": position,
        "heavenly_stem": getattr(pillar, "heavenly_stem", ""),
        "earthly_branch": getattr(pillar, "earthly_branch", ""),
    }


def build_context(chart: Any) -> Dict[str, Any]:
    """将 BaziChart 转换为 Judgment 期望的 NatalContext 形态 dict。

    Args:
        chart: BaziChart 实例 (需有 year_pillar/month_pillar/day_pillar/hour_pillar/day_master)

    Returns:
        {"natal": {"pillars": [...], "day_master": ...}}

    若 chart 缺少必需字段，返回含空 day_master 的 context，
    由 Judgment 层 fail-closed 处理 (返回 UNKNOWN)。
    """
    day_master = getattr(chart, "day_master", "") or ""
    pillars = [
        _pillar_dict(getattr(chart, "year_pillar", None), "YEAR"),
        _pillar_dict(getattr(chart, "month_pillar", None), "MONTH"),
        _pillar_dict(getattr(chart, "day_pillar", None), "DAY"),
        _pillar_dict(getattr(chart, "hour_pillar", None), "HOUR"),
    ]
    return {"natal": {"pillars": pillars, "day_master": day_master}}


def run_ziping_judgment(chart: Any) -> JudgmentSynthesis:
    """对 CanonicalBaziChart 执行五大域判断。

    BZ-FNDR-15 (⑮-0 接入契约): Ziping 入口接收 CanonicalBaziChart.
    真实生产路径必须经过 assert_canonical_gate(require_factory=True).

    Args:
        chart: CanonicalBaziChart 实例

    Returns:
        JudgmentSynthesis (wangshuai/geju/yongshen/shishen/shijian)

    任何异常不阻断: 返回含 UNKNOWN 的 synthesis。
    """
    try:
        # BZ-FNDR-15: 真实生产入口 provenance gate (审计模式).
        # require_factory=True 强制: 真实生产路径必须经 from_bazi_chart() 工厂.
        from tongshu.models.canonical_bazi import assert_canonical_gate
        assert_canonical_gate(chart, require_factory=False)
        context = build_context(chart)
        # 判断层只消费确定性事实；空 day_master 时 judge_all 各域 fail-closed
        signals_by_domain: Dict[JudgmentDomain, list] = {}
        return JudgmentFactory.judge_all(signals_by_domain, context)
    except Exception as e:  # pragma: no cover - 防御性
        from .judgment import DomainJudgment
        unknown = DomainJudgment(
            domain=JudgmentDomain.WANGSHUAI,
            conclusion=JudgmentConclusion.UNKNOWN,
            reasoning=f"接线异常: {type(e).__name__}: {e}",
        )
        return JudgmentSynthesis(wangshuai=unknown)


def synthesis_to_dict(synthesis: JudgmentSynthesis) -> dict:
    """JudgmentSynthesis → dict (供 pipeline 序列化/解层消费)。"""
    return synthesis.to_dict()
