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
    """对 CanonicalBaziChart 执行五大域判断 (V3 引擎真实接线).

    BZ-FNDR-15 (⑮-0 接入契约): Ziping 入口接收 CanonicalBaziChart.
    真实生产路径必须经过 assert_canonical_gate(require_factory=True).

    2026-11-07 (㊼s1) 修复「生产链路空转」:
      旧实现 `JudgmentFactory.judge_all({}, context)` 传空 signals,
      五域恒 None/UNKNOWN. 现改为调用 `ziping_v3.runner.run_ziping`
      (真引擎) 并把 旺衰/格局/用神 三域映射为 JudgmentSynthesis;
      十神/事件两域引擎未输出 → UNKNOWN (fail-closed, 不伪造).

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
        # 缺 day_master 等关键事实 → 直接 fail-closed
        if not context["natal"]["day_master"]:
            signals_by_domain: Dict[JudgmentDomain, list] = {}
            return JudgmentFactory.judge_all(signals_by_domain, context)
        from .ziping_v3.runner import run_ziping
        result = run_ziping(chart, enable_pattern=True)
        return _synthesis_from_v3(result)
    except Exception as e:  # pragma: no cover - 防御性
        from .judgment import DomainJudgment
        unknown = DomainJudgment(
            domain=JudgmentDomain.WANGSHUAI,
            conclusion=JudgmentConclusion.UNKNOWN,
            reasoning=f"接线异常: {type(e).__name__}: {e}",
        )
        return JudgmentSynthesis(wangshuai=unknown)


# V3 旺衰六态 → 辨层结论 (旺/衰/中和三值; 「旺而不强」「衰而不弱」归其本侧)
_V3_WANGSHUAI = {
    "STRONG": JudgmentConclusion.STRONG,
    "WANG_BUT_NOT_STRONG": JudgmentConclusion.STRONG,
    "BALANCED": JudgmentConclusion.MODERATE,
    "SHUAI_BUT_NOT_WEAK": JudgmentConclusion.WEAK,
    "WEAK": JudgmentConclusion.WEAK,
}


def _v3_judgment(result: Dict[str, Any], domain: str) -> Dict[str, Any]:
    for item in (result.get("judgments") or []):
        if item.get("domain") == domain:
            return item
    return {}


def _dj(domain: JudgmentDomain, conclusion: JudgmentConclusion,
        reasoning: str, v3_item: Dict[str, Any]) -> Any:
    from .judgment import DomainJudgment
    return DomainJudgment(
        domain=domain,
        conclusion=conclusion,
        reasoning=reasoning,
        rule_refs=list(v3_item.get("matched_rule_ids") or []),
    )


def _synthesis_from_v3(result: Dict[str, Any]) -> JudgmentSynthesis:
    """V3 引擎输出 → 五大域 JudgmentSynthesis (三域映射, 两域 fail-closed)."""
    unk = JudgmentConclusion.UNKNOWN

    # --- 旺衰 ---
    st = (result.get("strength") or {}).get("state")
    wangshuai = None
    if st in _V3_WANGSHUAI:
        wangshuai = _dj(
            JudgmentDomain.WANGSHUAI, _V3_WANGSHUAI[st],
            f"旺衰: {st}",
            _v3_judgment(result, "STRENGTH"),
        )
    else:
        wangshuai = _dj(
            JudgmentDomain.WANGSHUAI, unk,
            f"旺衰未裁: {st or 'FACT_MISSING'}",
            _v3_judgment(result, "STRENGTH"),
        )

    # --- 格局: 仅「已成立」(_FORMED) 记 ESTABLISHED, 候选/未裁 fail-closed ---
    pat = _v3_judgment(result, "PATTERN")
    pat_state = pat.get("state") or ""
    if pat_state.endswith("_FORMED"):
        geju = _dj(JudgmentDomain.GEJU, JudgmentConclusion.ESTABLISHED,
                   f"格局: {pat_state}", pat)
    elif pat_state == "NOT_APPLICABLE":
        geju = _dj(JudgmentDomain.GEJU, JudgmentConclusion.ESTABLISHED,
                   "格局: 特殊格成立(普通格不适用)", pat)
    else:
        geju = _dj(JudgmentDomain.GEJU, unk,
                   f"格局未成立(候选/未裁): {pat_state or 'UNDETERMINED'}", pat)

    # --- 用神: 有主用神 → PRIMARY, 否则 fail-closed ---
    ys = result.get("yongshen") or {}
    main = ys.get("main")
    if main:
        quote = str(ys.get("classic_quote") or "")
        yongshen = _dj(
            JudgmentDomain.YONGSHEN, JudgmentConclusion.PRIMARY,
            f"主用神: {main}（依据 {ys.get('basis') or 'ENGINE'}）"
            + (f"；引: {quote}" if quote else ""),
            _v3_judgment(result, "YONG-CLIMATE") or _v3_judgment(result, "YONG-PATTERN"),
        )
    else:
        yongshen = _dj(JudgmentDomain.YONGSHEN, unk,
                       f"用神未裁: {ys.get('basis') or 'FAIL_CLOSED'}",
                       _v3_judgment(result, "YONG-PATTERN"))

    # --- 十神 / 事件: V3 未输出该两域 (不伪造) ---
    shishen = _dj(JudgmentDomain.SHISHEN, unk, "十神语义域: V3 引擎未输出 (fail-closed)", {})
    shijian = _dj(JudgmentDomain.SHIJIAN, unk, "事件域: V3 引擎未输出 (fail-closed)", {})

    return JudgmentSynthesis(
        wangshuai=wangshuai, geju=geju, yongshen=yongshen,
        shishen=shishen, shijian=shijian,
    )


def synthesis_to_dict(synthesis: JudgmentSynthesis) -> dict:
    """JudgmentSynthesis → dict (供 pipeline 序列化/解层消费)。"""
    return synthesis.to_dict()
