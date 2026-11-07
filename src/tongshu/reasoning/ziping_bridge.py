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

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .judgment import (
    DomainJudgment,
    JudgmentConclusion,
    JudgmentDomain,
    JudgmentFactory,
    JudgmentSynthesis,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _unknown(domain: JudgmentDomain, reasoning: str) -> DomainJudgment:
    """fail-closed 单域判断: 明确给出未知原因, 不伪造结论。"""
    return DomainJudgment(
        domain=domain,
        conclusion=JudgmentConclusion.UNKNOWN,
        reasoning=reasoning,
        rule_refs=["ZIPING_ENGINES_P0"],
    )


def _pillars_from_chart(chart: Any) -> Dict[str, list]:
    """BaziChart → engines 生产入口要求的 canonical pillars dict。"""
    getter = getattr(chart, "get_pillars_chinese", None)
    if not callable(getter):
        raise ValueError("chart 缺 get_pillars_chinese()")
    pillars = getter()
    if not isinstance(pillars, dict):
        raise ValueError("get_pillars_chinese() 未返回 dict")
    out = {}
    for pos in ("year", "month", "day", "hour"):
        text = pillars.get(pos) or ""
        if len(text) != 2:
            raise ValueError(f"{pos} 柱缺干支")
        out[pos] = [text[0], text[1]]
    return out


def _rule_id(gc: Dict[str, Any]) -> str:
    """p0 规则码：`PZZQ255: 印格重…` → `PZZQ255`。"""
    text = str((gc.get("ge_evidence") or {}).get("rule_text") or "")
    return text.split(":", 1)[0].strip() if ":" in text else ""


def _ge_evidence_refs(gc: Dict[str, Any]) -> list:
    """ge_evidence 里的切片锚（zhun/zhu/pang/xiong）→ 已登记证据 ID。"""
    from . import p0_evidence

    gv = gc.get("ge_evidence") or {}
    refs = []
    for key in ("zhun", "zhu", "pang", "xiong"):
        refs.extend(list(gv.get(key) or []))
    return p0_evidence.resolve(refs)


def _engines_p0_synthesis(result: Dict[str, Any]) -> JudgmentSynthesis:
    """engines(p0 线) production_entry 输出 → 五大域。

    映射口径(不夸大):
    - 旺衰: p0 线只输出得令/失令候选, 明言"不判身强身弱" → UNKNOWN。
    - 格局: ge_cheng['cheng_bai'] CHENG→ESTABLISHED / BAI→BROKEN / 其余 UNKNOWN。
    - 用神: zhenglun.yongyao.primary_medicine.wuxing → PRIMARY(用药方向, 非吉凶裁决)。
    - 十神/事件: p0 线未输出 → UNKNOWN。
    - 证据锚: 结论必须带可解析的 p0_v2 切片 ID（G1 证据闸要求），
      无锚则该域降级 UNKNOWN（不产无证据 claim）。
    """
    from . import p0_evidence

    facts = result.get("engine_result") or {}
    zhenglun = result.get("zhenglun") or {}

    gc = facts.get("ge_cheng") or {}
    cheng = gc.get("cheng_bai")
    ge_name = gc.get("ge") or ""
    ge_ev = _ge_evidence_refs(gc)
    rule_refs = [r for r in ("ZIPING_ENGINES_P0", _rule_id(gc)) if r]
    if cheng == "CHENG" and ge_name and ge_ev:
        geju = DomainJudgment(
            domain=JudgmentDomain.GEJU,
            conclusion=JudgmentConclusion.ESTABLISHED,
            reasoning=f"格局={ge_name}; cheng_bai=CHENG; 证据锚={len(ge_ev)} 片",
            rule_refs=rule_refs,
            evidence_refs=ge_ev,
        )
    elif cheng == "BAI" and ge_ev:
        geju = DomainJudgment(
            domain=JudgmentDomain.GEJU,
            conclusion=JudgmentConclusion.BROKEN,
            reasoning=f"格局={ge_name or '未知'}; cheng_bai=BAI",
            rule_refs=rule_refs,
            evidence_refs=ge_ev,
        )
    else:
        geju = _unknown(
            JudgmentDomain.GEJU,
            f"格局未成/无证据锚: ge={ge_name or '未知'} cheng_bai={cheng!r} refs={len(ge_ev)}")

    yy = zhenglun.get("yongyao") or {}
    pm = yy.get("primary_medicine") or {}
    wx = pm.get("wuxing")
    state = yy.get("state")
    yy_ev = p0_evidence.resolve(list(yy.get("evidence_refs") or []))
    if not yy_ev and state == "GE_FALLBACK":
        # 格体喜神派生用药，其依据即格局证据
        yy_ev = ge_ev
    if wx and state not in ("PATTERN_CONFLICT_NOT_EVALUABLE", "NO_CANDIDATE") and yy_ev:
        yongshen = DomainJudgment(
            domain=JudgmentDomain.YONGSHEN,
            conclusion=JudgmentConclusion.PRIMARY,
            reasoning=(f"用药方向={wx}; 功能={pm.get('function')}; "
                       f"层状态={state}; 证据锚={len(yy_ev)} 片"),
            rule_refs=[r for r in ("ZIPING_ENGINES_P0", str(state or "YONGYAO_RESOLVE")) if r],
            evidence_refs=yy_ev,
        )
    else:
        yongshen = _unknown(JudgmentDomain.YONGSHEN,
                            f"用药未裁定/无证据锚: state={state!r} refs={len(yy_ev)}")

    return JudgmentSynthesis(
        wangshuai=_unknown(
            JudgmentDomain.WANGSHUAI,
            "p0 线旺衰轨只输出得令/失令候选(PZZQ「旺衰只回答得令/失令, 不回答身强身弱」), 不判身强身弱"),
        geju=geju,
        yongshen=yongshen,
        shishen=_unknown(JudgmentDomain.SHISHEN, "p0 engines 线未输出十神域"),
        shijian=_unknown(JudgmentDomain.SHIJIAN, "p0 engines 线未输出事件域"),
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

    [2026-11-07 用户裁决] 子平引擎最终版本 = D:\\shuntian-ziping-p0 (engines p0 线).
    本桥接改为调用 engines.production_entry(唯一生产入口, G-P01~G-P05 gate),
    再把 engine_result/zhenglun 映射为五域; 映射不能确定的域一律 UNKNOWN 并写明原因。

    Args:
        chart: CanonicalBaziChart 实例

    Returns:
        JudgmentSynthesis (wangshuai/geju/yongshen/shishen/shijian)

    任何异常不阻断: 返回五域全 UNKNOWN 的 synthesis。
    """
    try:
        # BZ-FNDR-15: 真实生产入口 provenance gate (审计模式).
        from tongshu.models.canonical_bazi import assert_canonical_gate
        assert_canonical_gate(chart, require_factory=False)
    except Exception as exc:
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"canonical gate 拒绝: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "canonical gate 未通过"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "canonical gate 未通过"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "canonical gate 未通过"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "canonical gate 未通过"),
        )

    try:
        pillars = _pillars_from_chart(chart)
    except Exception as exc:
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"四柱不可用: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "四柱不可用"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "四柱不可用"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "四柱不可用"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "四柱不可用"),
        )

    try:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from engines.production_entry import (
            FrozenCanonicalBaziChart,
            production_entry,
        )
        result = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    except Exception as exc:  # pragma: no cover - 防御性
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI,
                               f"engines 生产入口异常: {type(exc).__name__}: {exc}"),
            geju=_unknown(JudgmentDomain.GEJU, "engines 生产入口异常"),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, "engines 生产入口异常"),
            shishen=_unknown(JudgmentDomain.SHISHEN, "engines 生产入口异常"),
            shijian=_unknown(JudgmentDomain.SHIJIAN, "engines 生产入口异常"),
        )

    if not result.get("gate_passed"):
        reason = f"engines gate 失败({result.get('gate')}): {result.get('reason')}"
        return JudgmentSynthesis(
            wangshuai=_unknown(JudgmentDomain.WANGSHUAI, reason),
            geju=_unknown(JudgmentDomain.GEJU, reason),
            yongshen=_unknown(JudgmentDomain.YONGSHEN, reason),
            shishen=_unknown(JudgmentDomain.SHISHEN, reason),
            shijian=_unknown(JudgmentDomain.SHIJIAN, reason),
        )

    return _engines_p0_synthesis(result)


def synthesis_to_dict(synthesis: JudgmentSynthesis) -> dict:
    """JudgmentSynthesis → dict (供 pipeline 序列化/解层消费)。"""
    return synthesis.to_dict()
