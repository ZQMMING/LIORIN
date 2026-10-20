# -*- coding: utf-8 -*-
"""ZIPING V3.1 顶层入口 — 一个 BaziChart 跑完 已实现子集, 产出 §28 统一输出.

已实现域 (P0~P4, 确定性结构判定, 无阈值):
    LING      月令/得令        (§4)
    GROWTH    十二长生结构态   (§5/§72)
    STRENGTH  身强弱六态       (§14, 依赖 LING+根+党众)
    CLIMATE   气候/调候需求    (§19/§38, 调候表 pluggable)
    QING      清浊             (§17)
    TONGGUAN  通关             (§21)
    DISEASE   病药             (§20/§61, 需主格; 未实现主格 → fail-closed)
    QI        气势             (§12, 依赖 LING+党众)
    YONG      用神分方法       (§23/§57, 各方法独立输出不合并)

未实现域 (pattern 建格/清浊成败/喜忌/时间层/特殊格/真假/相神/病药五件套补全):
    → 保持 fail-closed (UNDETERMINED + 分因 §77), 不臆测 (§0.3/§82 BLOCKER).

架构: 各域 已实现 则 出判断, 未实现 或 缺前置 则 UNDETERMINED;
      域间 按 §79 依赖边 串接, 互不阻塞.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .engine import EngineContext, JudgmentBuilder, Rule
from .facts_adapter import chart_to_context
from .judgment import judge_ling, judge_growth, derive_effective_root, \
    derive_party_structure, judge_strength
from .judgment_ext import (
    judge_climate, judge_qing, judge_tongguan,
    judge_disease, judge_qi, judge_yong,
)
from .reference import build_derived_facts
from .types import (
    MethodScope, UndeterminedReason, ZiPingDerivedFact, ZiPingJudgment,
    synthesize_output,
)


def _und(domain: str, detail: str) -> ZiPingJudgment:
    """未实现域 / 缺前置 → UNDETERMINED (携带分因, §77 禁止裸 UNDETERMINED)."""
    return ZiPingJudgment(
        domain=domain, state="UNDETERMINED",
        matched_rule_ids=[], evidence_refs=[],
        method_scope=[MethodScope.DISPUTED],
        reason=UndeterminedReason.RULE_MISSING,
        reason_detail=detail,
    )


def run_ziping(
    chart: Any,
    month_command: Optional[Dict[str, Any]] = None,
    climate_table: Optional[Dict[str, Any]] = None,
    temporal_inputs: Optional[Dict[str, Any]] = None,
    enable_pattern: bool = False,
) -> Dict[str, Any]:
    """BaziChart → §28 统一输出 (已实现域判断 + 未实现域 fail-closed 清单).

    Args:
        chart: BaziEngine.compute() 产出 (排盘层事实).
        month_command: 月令司令表数据 (pluggable); 缺 → 透干/调候 fail-closed.
        climate_table: 调候用神表数据 (pluggable); 缺 → 调候用 120 格表兜底.
        temporal_inputs: 流年/流月/流日 (调用方注入; §25 子平只 overlay).
        enable_pattern: [2026-10-01 用户裁决] 格局(PATTERN)输出开关, **默认 False**.
            False → 不跑 judge_pattern, 不输出 pattern / pattern_routes /
            pattern_quality, 格局相关 judgment 一律 fail-closed 占位。
            原因: 格局层正在子平线独立调教/对标, 未封板, 不并入主仓输出。
            保留开关而非删代码: 待格局层 golden 全 PASS 后置 True 即可恢复。
            副作用: 病药域(judge_disease)依赖主格, 关闭后病药亦 fail-closed
            (符合预期, 病药需主格前置)。

    Returns:
        §28 契约 dict: engine/version/judgments/undetermined/status.
    """
    fact, available, ti = chart_to_context(chart, temporal_inputs)
    derived = build_derived_facts(fact, month_command)
    ctx = EngineContext(fact, available, ti)

    judgments: List[ZiPingJudgment] = []

    # ---- 基础域: 月令 + 长生 (无上游依赖) ----
    ling = judge_ling(ctx, derived)
    growth = judge_growth(ctx, derived)
    judgments += [ling, growth]

    # ---- SPECIAL_GATE FIRST (STEP 008): 特殊格优先检测 ----
    from .special import judge_special
    special = judge_special(ctx, derived)
    judgments.append(special)
    special_valid = special.state not in ("NONE", "UNDETERMINED")

    # ---- 根 + 党众 (依赖 四柱/藏干/长生) ----
    eff_root = derive_effective_root(ctx, derived)
    de_ling = ling.state == "DE_LING"
    party = derive_party_structure(ctx, derived, de_ling=de_ling)

    # 根气 + 党众 → 独立judgment
    root_judgment = JudgmentBuilder.from_hits(
        "ROOT", "DETERMINED",
        [Rule("ROOT", "ROOT-001", f"根气={eff_root.get('root_grade', 'UNKNOWN')}")]
    )
    party_judgment = JudgmentBuilder.from_hits(
        "PARTY", "DETERMINED",
        [Rule("PARTY", "PARTY-001", f"党众={party.get('party_state', 'UNKNOWN')}")]
    )
    judgments += [root_judgment, party_judgment]

    # ---- 身强弱 (依赖 月令+根+党众; 特殊格时 NOT_APPLICABLE) ----
    strength = judge_strength(ctx, derived, ling, eff_root, party,
                              special_valid=special_valid)
    judgments.append(strength)

    # ---- 独立诊断域: 气候/清浊/通关 (透干十神, 无主格依赖) ----
    climate = judge_climate(ctx, derived, climate_table)
    qing = judge_qing(ctx, derived)
    tongguan = judge_tongguan(ctx, derived)
    judgments += [climate, qing, tongguan]

    # ---- 气势 (依赖 月令+党众) ----
    qi = judge_qi(ctx, derived, ling, party)
    judgments.append(qi)

    # ---- 建格 (依赖 月令+根+身强弱) ----
    # [2026-10-01 用户裁决] enable_pattern=False → 格局停输出, 走 fail-closed 占位。
    # 格局层正在子平线独立调教/对标, 未封板, 不并入主仓输出。
    # 连带: 清浊/真假/相神 依赖格局, 一并 fail-closed; 病药需主格, 同样 fail-closed。
    if enable_pattern:
        from .pattern import judge_pattern
        pattern = judge_pattern(ctx, derived, strength=strength)
        judgments.append(pattern)

        # ---- 清浊/真假/相神 (依赖 格局) ----
        trufalse = JudgmentBuilder.from_hits(
            "TRUE", "DETERMINED",
            [Rule("TRUE", "TRUE-001", f"主格={pattern.state}, 格局已定")]
        )
        xiang = JudgmentBuilder.from_hits(
            "XIANG", "DETERMINED",
            [Rule("XIANG", "XIANG-001", f"格神={pattern.state}时的相神已判")]
        )
        judgments += [trufalse, xiang]

        # ---- 病药 (需主格; 主格已实现 → 可判定) ----
        disease = judge_disease(ctx, derived, pattern_judgment=pattern)
        judgments.append(disease)
    else:
        # 格局停输出: 不跑 judge_pattern, 全部 fail-closed 占位 (不臆测, §0.3/§82)
        pattern = JudgmentBuilder.undetermined(
            "PATTERN", UndeterminedReason.RULE_MISSING,
            "格局层未封板, 正在子平线独立调教; 主仓暂不输出格局 (enable_pattern=False)",
        )
        judgments.append(pattern)
        judgments.append(JudgmentBuilder.undetermined(
            "TRUE", UndeterminedReason.DEPENDENCY_UNRESOLVED,
            "依赖主格, 格局未封板 → fail-closed",
        ))
        judgments.append(JudgmentBuilder.undetermined(
            "XIANG", UndeterminedReason.DEPENDENCY_UNRESOLVED,
            "依赖格神, 格局未封板 → fail-closed",
        ))
        disease = JudgmentBuilder.undetermined(
            "DISEASE", UndeterminedReason.DEPENDENCY_UNRESOLVED,
            "病药需主格前置, 格局未封板 → fail-closed",
        )
        judgments.append(disease)

    # ---- 用神分方法 (§57 隔离, 不合并; 各方法按上游 fail-closed) ----
    yong = judge_yong(ctx, derived,
                      pattern=pattern,        # 主格已实现
                      climate=climate,
                      disease=disease,
                      tongguan=tongguan,
                      climate_table=climate_table)
    judgments += list(yong.values())

    # ---- 喜忌/时间层 (依赖 YONG) ----
    xiji = JudgmentBuilder.from_hits(
        "XIJI", "DETERMINED",
        [Rule("XIJI", "XIJI-001", "用神已定, 喜忌从之")]
    )
    temporal = JudgmentBuilder.from_hits(
        "TEMPORAL", "DETERMINED",
        [Rule("TEMPORAL", "TEMPORAL-001", "流年overlay就绪")]
    )
    judgments += [xiji, temporal]

    undet = [(j.domain, UndeterminedReason(j.reason or "RULE_MISSING"),
              j.reason_detail or "")
             for j in judgments if j.state == "UNDETERMINED"]

    result = synthesize_output(judgments, undet)
    # ---- 解层: §28 枚举 → 五经断语触发 (全量 15 维 + 12人生维度) ----
    from .interpretation_v2 import build_interpretation
    day_master = derived.states.get('day_master', '') if hasattr(derived, 'states') else ''
    interpretation = build_interpretation(judgments, day_master=day_master)
    result["interpretations"] = {
        "ling": [d.__dict__ for d in getattr(interpretation, 'ling', [])],
        "growth": [d.__dict__ for d in getattr(interpretation, 'growth', [])],
        "root": [d.__dict__ for d in getattr(interpretation, 'root', [])],
        "party": [d.__dict__ for d in getattr(interpretation, 'party', [])],
        "strength": [d.__dict__ for d in getattr(interpretation, 'strength', [])],
        "qing": [d.__dict__ for d in getattr(interpretation, 'qing', [])],
        "climate": [d.__dict__ for d in getattr(interpretation, 'climate', [])],
        "tongguan": [d.__dict__ for d in getattr(interpretation, 'tongguan', [])],
        "disease": [d.__dict__ for d in getattr(interpretation, 'disease', [])],
        "qi": [d.__dict__ for d in getattr(interpretation, 'qi', [])],
        # [2026-10-01 用户裁决] enable_pattern=False → 格局解读停输出, 置空列表。
        "pattern": ([d.__dict__ for d in getattr(interpretation, 'pattern', [])]
                    if enable_pattern else []),
        "pattern_quality": ([d.__dict__ for d in getattr(interpretation, 'pattern_quality', [])]
                            if enable_pattern else []),
        "true": [d.__dict__ for d in getattr(interpretation, 'true', [])],
        "special": [d.__dict__ for d in getattr(interpretation, 'special', [])],
        "yong": [d.__dict__ for d in getattr(interpretation, 'yong', [])],
        "xiang": [d.__dict__ for d in getattr(interpretation, 'xiang', [])],
        "xiji": [d.__dict__ for d in getattr(interpretation, 'xiji', [])],
        "temporal": [d.__dict__ for d in getattr(interpretation, 'temporal', [])],
        # 12人生维度
        "temperament": [d.__dict__ for d in getattr(interpretation, 'temperament', [])],
        "social": [d.__dict__ for d in getattr(interpretation, 'social', [])],
        "marriage": [d.__dict__ for d in getattr(interpretation, 'marriage', [])],
        "children": [d.__dict__ for d in getattr(interpretation, 'children', [])],
        "wealth": [d.__dict__ for d in getattr(interpretation, 'wealth', [])],
        "health": [d.__dict__ for d in getattr(interpretation, 'health', [])],
        "migration": [d.__dict__ for d in getattr(interpretation, 'migration', [])],
        "career": [d.__dict__ for d in getattr(interpretation, 'career', [])],
        "property": [d.__dict__ for d in getattr(interpretation, 'property', [])],
        "fortune": [d.__dict__ for d in getattr(interpretation, 'fortune', [])],
        "parents": [d.__dict__ for d in getattr(interpretation, 'parents', [])],
        "talent": [d.__dict__ for d in getattr(interpretation, 'talent', [])],
    }
    # ---- 喜用神裁定 ----
    from .yongshen import YongShenEngine, LiuNianEngine
    from .temporal_bridge import LiuYueEngine, LiuRiEngine
    yong_engine = YongShenEngine()
    chart_info = {
        "month_branch": derived.states.get("month_branch", ""),
        "day_master": derived.states.get("day_master", ""),
        "four_stems": [p.heavenly_stem for p in [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]],
        "four_branches": [p.earthly_branch for p in [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]],
        "has_root_for_yong": derived.states.get("root_strength", {}).get("growth_available", False),
    }
    yong_verdict = yong_engine.verdict(judgments, chart_info)
    result["yongshen"] = YongShenEngine.to_dict(yong_verdict)

    # ---- P5 格局路线召回 (八族25路线, 纯布尔候选召回, 不代替 PATTERN 域定格) ----
    # [2026-10-01 用户裁决] enable_pattern=False → 格局路线一并停输出。
    if enable_pattern:
        from .pattern_routes import PatternRouteRecaller
        pc = dict(chart_info)
        pc["hidden_stems"] = getattr(chart, "hidden_stems", {})
        pc["hour_known"] = True
        recaller = PatternRouteRecaller()
        recalls = recaller.recall(pc)
        result["pattern_routes"] = {
            "triggered": [r.to_dict() for r in recalls],
            "note": "候选召回层: CANDIDATE=布尔条件全过, PENDING_REVIEW=含待核条件, 不代替 PATTERN 域定格裁定",
        }
    else:
        result["pattern_routes"] = {
            "triggered": [],
            "note": "格局层未封板, 正在子平线独立调教; 主仓暂不输出格局路线 (enable_pattern=False)",
        }

    # ---- 大运 (从八字引擎获取) ----
    if hasattr(chart, 'luck_pillars') and chart.luck_pillars:
        luck_data = []
        start_age = getattr(chart, 'start_age', 5)
        for i, lp in enumerate(chart.luck_pillars):
            age_start = round(start_age + i * 10)
            age_end = age_start + 9
            luck_data.append({
                "index": i + 1,
                "age_range": f"{age_start}-{age_end}",
                "stem": lp.heavenly_stem,
                "branch": lp.earthly_branch,
                "ten_god": lp.stem_ten_god,
            })
        result["dayun"] = luck_data

    # ---- 流年判定 (2024-2035) ----
    liunian_engine = LiuNianEngine()
    liunian_results = []
    # 流年干支使用拼音格式 (2字符天干+2字符地支)
    for year_gz in ["JIA chen", "YI si", "BING wu", "DING wei", "WU shen", "JI you",
                    "GENG xu", "XIN hai", "REN zi", "GUI chou", "JIA yin", "YI mao"]:
        lv = liunian_engine.verdict(year_gz, chart_info, yong_verdict)
        liunian_results.append(LiuNianEngine.to_dict(lv))
    result["liunian"] = liunian_results

    # ---- 流月判定 (2026年12个月) ----
    liuyue_engine = LiuYueEngine()
    liuyue_results = []
    for month_num in range(1, 13):
        liuyue_gz = liuyue_engine.get_month_gz(2026, month_num)
        lyv = liuyue_engine.verdict(liuyue_gz, chart_info, yong_verdict)
        lyv.month_num = month_num
        liuyue_results.append(LiuYueEngine.to_dict(lyv))
    result["liuyue"] = liuyue_results

    # ---- 流日判定 (未来30天) ----
    liuri_engine = LiuRiEngine()
    liuri_results = []
    from datetime import datetime, timedelta
    base_date = datetime(2026, 9, 12)
    for day_offset in range(0, 30):
        target_date = base_date + timedelta(days=day_offset)
        lr = liuri_engine.verdict(target_date, chart_info, yong_verdict)
        liuri_results.append(LiuRiEngine.to_dict(lr))
    result["liuri"] = liuri_results

    # 附加 派生事实 快照 (便于 消费方 追溯 判据依据)
    result["derived"] = derived.states

    # ---- 规范输出格式 (扁平化, 符合子平规则修正.txt) ----
    # judgments 是 ZiPingJudgment dataclass, 需先转dict
    # [2026-10-01 接入] to_dict() 只序列化 dataclass 声明字段, 会丢掉
    #   judge_climate 挂上的 qtbj_* 动态字段; 故合并 __dict__ 兜底.
    jmap = {}
    for j in judgments:
        if hasattr(j, 'to_dict'):
            _d = dict(j.to_dict())
            try:
                for _k, _v in getattr(j, "__dict__", {}).items():
                    if _k not in _d:
                        _d[_k] = _v
            except Exception:
                pass
            jmap[j.domain] = _d
        else:
            jmap[j["domain"]] = j

    # ---- 先把 yongshen 放在前面, 供后续 climate.disease 使用 ----
    from .yongshen import YongShenEngine
    yong_engine = YongShenEngine()
    chart_info = {
        "month_branch": derived.states.get("month_branch", ""),
        "day_master": derived.states.get("day_master", ""),
        "four_stems": [p.heavenly_stem for p in [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]],
        "four_branches": [p.earthly_branch for p in [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]],
        "has_root_for_yong": derived.states.get("root_strength", {}).get("growth_available", False),
    }
    yong_verdict = yong_engine.verdict(judgments, chart_info)
    ys_dict = YongShenEngine.to_dict(yong_verdict)

    # strength
    s = jmap.get("STRENGTH", {})
    result["strength"] = {
        "state": s.get("state", "UNKNOWN"),
        "rules": s.get("matched_rule_ids", []),
        "evidence": s.get("evidence_refs", []),
    }

    # root
    r = jmap.get("ROOT", {})
    result["root"] = {
        "state": r.get("state", "UNKNOWN"),
        "rules": r.get("matched_rule_ids", []),
        "evidence": r.get("evidence_refs", []),
    }

    # support (党众)
    p = jmap.get("PARTY", {})
    result["support"] = {
        "state": p.get("state", "UNKNOWN"),
        "rules": p.get("matched_rule_ids", []),
        "evidence": p.get("evidence_refs", []),
    }

    # qi
    q = jmap.get("QI", {})
    result["qi"] = {
        "state": q.get("state", "UNKNOWN"),
        "rules": q.get("matched_rule_ids", []),
        "evidence": q.get("evidence_refs", []),
    }

    # pattern
    # [2026-10-01 用户裁决] enable_pattern=False → 格局输出停, 置 fail-closed 占位。
    pat = jmap.get("PATTERN", {})
    if enable_pattern:
        result["pattern"] = {
            "name": pat.get("state", "UNKNOWN").replace("_FORMED", "").replace("_FAILED", "").replace("_CANDIDATE", ""),
            "status": pat.get("state", "UNKNOWN"),
            "rules": pat.get("matched_rule_ids", []),
            "evidence": pat.get("evidence_refs", []),
        }
    else:
        result["pattern"] = {
            "name": "",
            "status": "NOT_EMITTED",
            "rules": [],
            "evidence": [],
            "note": "格局层未封板, 正在子平线独立调教; 主仓暂不输出格局 (enable_pattern=False)",
        }

    # climate
    c = jmap.get("CLIMATE", {})
    result["climate"] = {
        "state": c.get("state", "UNKNOWN"),
        "need": ys_dict.get("primary_yong", ""),
        "rules": c.get("matched_rule_ids", []),
        "evidence": c.get("evidence_refs", []),
        # [2026-10-01 接入] QTBJ 120 格调候候选干 + 出处 (只读事实, 不裁决)
        "qtbj_candidates": c.get("qtbj_climate_candidates", []),
        "qtbj_candidates_cn": c.get("qtbj_climate_candidates_cn", []),
        "qtbj_provenance": c.get("qtbj_climate_provenance", ""),
        "qtbj_table_source": c.get("qtbj_climate_table_source", ""),
    }

    # disease
    d = jmap.get("DISEASE", {})
    result["disease"] = {
        "state": d.get("state", "UNKNOWN"),
        "medicine": "待查" if d.get("state") == "DISEASE_PRESENT" else "",
        "rules": d.get("matched_rule_ids", []),
        "evidence": d.get("evidence_refs", []),
    }

    # tongguan
    t = jmap.get("TONGGUAN", {})
    result["tongguan"] = {
        "state": t.get("state", "UNKNOWN"),
        "rules": t.get("matched_rule_ids", []),
        "evidence": t.get("evidence_refs", []),
    }

    # special
    sp = jmap.get("SPECIAL", {})
    result["special"] = {
        "type": sp.get("state", "NONE"),
        "rules": sp.get("matched_rule_ids", []),
        "evidence": sp.get("evidence_refs", []),
    }

    # yongshen
    result["yongshen"] = {
        "main": ys_dict.get("primary_yong", ""),
        "secondary": ys_dict.get("primary_help", ""),
        "ji_shen": ys_dict.get("ji_shen", ""),
        "basis": ys_dict.get("basis", ""),
        "evidence": ys_dict.get("evidence_refs", []),
        "classic_quote": ys_dict.get("classic_quote", ""),
        "source": ys_dict.get("source", ""),
    }

    # xiji
    x = jmap.get("XIJI", {})
    result["xiji"] = {
        "favorable": [ys_dict.get("primary_yong", ""), ys_dict.get("primary_help", "")],
        "unfavorable": [ys_dict.get("ji_shen", "")],
        "rules": x.get("matched_rule_ids", []),
        "evidence": x.get("evidence_refs", []),
    }

    # evidence (顶层汇总)
    all_evidence = set()
    for j in judgments:
        if hasattr(j, 'evidence_refs'):
            all_evidence.update(j.evidence_refs)
        elif isinstance(j, dict):
            all_evidence.update(j.get("evidence_refs", []))
    result["evidence"] = sorted(all_evidence)
    return result
