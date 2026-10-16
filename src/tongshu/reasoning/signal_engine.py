"""Signal Engine - extracts Universal Signals from Bazi / Ziwei / Huangli charts.

Per architecture_decisions_v1.md DECISION-002, signals MUST be preserved
across three layers (BASELINE / CYCLE_CONTEXT / DAILY_ACTIVATION) independently.

T201/T205 (v3.1): rule matching runs through RuleMatcher (typed condition DSL)
and resolve_conflicts (precedence + specificity; an unresolvable tie drops the
Signal). The single source of rules is backend/data/rules/*.json via RuleLoader.
"""

from __future__ import annotations
from dataclasses import dataclass, replace, field
from datetime import datetime, timezone

from ..engines.bazi_engine import STEM_ELEMENT
from ..spec.signal_ontology import USO_TYPES
from ..spec.signal_layers import SIGNAL_LAYERS
from ..spec.canonical_signal import (
    CanonicalSignal,
    SourceEngine,
    SignalLayer,
    SignalTemporalScope,
)
from .matcher import RuleContext, RuleMatcher, resolve_conflicts, rule_refs_of
from .bazi_ten_gods import (
    SEASON_BY_BRANCH,
    hidden_main_stem_is_transparent,
    hidden_main_stem,
    month_hidden_main_ten_god,
    ten_god,
    transparent_ten_gods as transparent_ten_gods_list,
)
from .bazi_fixed_tables import (
    longhu_stage,
    road_branch,
    absolute_branch,
    tianyi_guiren,
)

# 河洛五行映射（上卦→五行）
_HELUO_TRIGRAM_ELEMENT = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 河洛五行→八字五行键名映射
_HELUO_WUXING_TO_BASI_KEY = {
    "金": "METAL", "木": "WOOD", "水": "WATER", "火": "FIRE", "土": "EARTH",
}

# 河洛不利时节（谷雨-芒种≈辰月，即农历三月）
_HELUO_UNFAVORABLE_BRANCHES = {"辰"}

# 五行失衡阈值（本命卦五行在八字中占比）
_WUXING_OVER_THRESHOLD = 0.30  # >30% 为过旺
_WUXING_UNDER_THRESHOLD = 0.10  # <10% 为不及


def extract_heluo_context(heluo_result, bazi) -> dict:
    """从HeluoResult提取规则匹配所需的河洛字段。

    返回dict，键为RuleContext中的heluo_*字段名。全部字段缺失时返回空dict。
    五行失衡判定：本命卦五行在八字四柱五行分布中占比>30%为over，<10%为under。
    """
    if heluo_result is None:
        return {}
    out = {}
    benming_wuxing = None
    # 本命卦五行 = 先天卦上卦五行
    prenatal = getattr(heluo_result, "prenatal", None)
    if prenatal and getattr(prenatal, "upper_gua", None):
        elem = _HELUO_TRIGRAM_ELEMENT.get(prenatal.upper_gua)
        if elem:
            out["heluo_benming_guawuxing"] = elem
            benming_wuxing = elem
        out["heluo_benming_gong"] = prenatal.upper_gua
        out["heluo_benming_guaming"] = getattr(prenatal, "hexagram_name", None)
    # 元堂爻（等同八字日主）
    yuantang = getattr(heluo_result, "yuantang", None)
    if yuantang:
        out["heluo_yuantang"] = getattr(yuantang, "yuantang", None)
        out["heluo_yuantang_index"] = getattr(yuantang, "yuantang_index", None)
    # 后天卦名（人生发展走势）
    postnatal = getattr(heluo_result, "postnatal", None)
    if postnatal:
        out["heluo_houtian_guaming"] = getattr(postnatal, "hexagram_name", None)
    # 地数有余 = 地数 > 30（地数减30或倍数，有余则凶）
    numbers = getattr(heluo_result, "numbers", None)
    if numbers and getattr(numbers, "di_shu", None) is not None:
        out["heluo_dishu_youyu"] = numbers.di_shu > 30
    # 生于不利时节（辰月）
    if bazi and getattr(bazi, "month_pillar", None):
        out["heluo_birth_season_unfavorable"] = (
            bazi.month_pillar.earthly_branch in _HELUO_UNFAVORABLE_BRANCHES
        )
    # 五行失衡：基于八字五行分布判定本命卦五行的过旺/不及
    if benming_wuxing and bazi and getattr(bazi, "five_element_balance", None):
        bazi_key = _HELUO_WUXING_TO_BASI_KEY.get(benming_wuxing)
        if bazi_key and bazi_key in bazi.five_element_balance:
            ratio = bazi.five_element_balance[bazi_key]
            if ratio > _WUXING_OVER_THRESHOLD:
                out["heluo_wuxing_imbalance"] = "over"
            elif ratio < _WUXING_UNDER_THRESHOLD:
                out["heluo_wuxing_imbalance"] = "under"
            else:
                out["heluo_wuxing_imbalance"] = "none"
        else:
            out["heluo_wuxing_imbalance"] = "none"
    else:
        out["heluo_wuxing_imbalance"] = "none"
    return out

SIGNAL_LAYER_ORDER = ("BASELINE", "CYCLE_CONTEXT", "DAILY_ACTIVATION")


@dataclass(frozen=True)
class Signal:
    signal_id: str
    ontology_type: str
    direction: str
    polarity: str
    strength: str
    layer: str
    rule_refs: list
    evidence_refs: list
    domain: str = ""  # 辨证域：WANGSHUAI/GEJU/YONGSHEN/SHISHEN/SHIJIAN

    def __post_init__(self):
        if self.ontology_type not in USO_TYPES:
            raise ValueError(f"Invalid ontology_type: {self.ontology_type}")
        if self.layer not in SIGNAL_LAYERS:
            raise ValueError(f"Invalid layer: {self.layer}")


def _FOUR_BRANCHES(bazi) -> list[str]:
    """命局四支(年月日时)列表,供神煞/通根类规则扫描。"""
    return [
        bazi.year_pillar.earthly_branch,
        bazi.month_pillar.earthly_branch,
        bazi.day_pillar.earthly_branch,
        bazi.hour_pillar.earthly_branch,
    ]


def build_rule_context(bazi, ziwei, huangli, layer=None, theme=None, heluo_result=None) -> RuleContext:
    """Build the RuleContext handed to RuleMatcher for one signal layer."""
    heluo_fields = extract_heluo_context(heluo_result, bazi)
    return RuleContext(
        day_master=bazi.day_master if bazi else None,
        day_master_element=STEM_ELEMENT[bazi.day_master] if bazi else None,
        day_branch=bazi.day_pillar.earthly_branch if bazi else None,
        month_stem=bazi.month_pillar.heavenly_stem if bazi else None,
        month_branch=bazi.month_pillar.earthly_branch if bazi else None,
        year_stem=bazi.year_pillar.heavenly_stem if bazi else None,
        year_branch=bazi.year_pillar.earthly_branch if bazi else None,
        hour_stem=bazi.hour_pillar.heavenly_stem if bazi else None,
        hour_branch=bazi.hour_pillar.earthly_branch if bazi else None,
        season=(
            SEASON_BY_BRANCH.get(bazi.month_pillar.earthly_branch)
            if bazi else None
        ),
        month_hidden_main_ten_god=(
            month_hidden_main_ten_god(bazi.day_master, bazi.month_pillar.earthly_branch)
            if bazi else None
        ),
        month_hidden_main_ten_god_transparent=(
            hidden_main_stem_is_transparent(
                bazi.month_pillar.earthly_branch,
                [
                    bazi.year_pillar.heavenly_stem,
                    bazi.month_pillar.heavenly_stem,
                    bazi.day_pillar.heavenly_stem,
                    bazi.hour_pillar.heavenly_stem,
                ],
            )
            if bazi else None
        ),
        # T501 后接入梯二(2026-08-17):transparent_ten_gods 驱动「非当令十神
        # 透干显性」规则 ZPZ-121~130。渲染层已具备 multi(3-5)/top_k(>5) 容量,
        # golden 6 例信号数从 2 升级到 3-5,已按 Spec Owner 指示重校。注:日主
        # 自身不参与透干(十神相对日主),year/month/hour 三干恒非空 -> 梯二
        # 通常每命局产出 1-3 条 BASELINE 信号(与当令司权结论一致者经 T205 合并)。
        transparent_ten_gods=(
            transparent_ten_gods_list(
                bazi.day_master,
                bazi.year_pillar.heavenly_stem,
                bazi.month_pillar.heavenly_stem,
                bazi.hour_pillar.heavenly_stem,
            )
            if bazi else None
        ),
        # P1-01 新增事实字段(全部从既有四柱派生,不新增事实源;供 DTS/SMTH/
        # YHZP 经典规则条件使用。新规则为 draft,§8.7 治理下不参与生产推理)。
        day_master_stage_month=(
            longhu_stage(bazi.day_master, bazi.month_pillar.earthly_branch)
            if bazi else None
        ),
        day_master_road_month=(
            road_branch(bazi.day_master) == bazi.month_pillar.earthly_branch
            if bazi else None
        ),
        day_master_absolute_month=(
            absolute_branch(bazi.day_master) == bazi.month_pillar.earthly_branch
            if bazi else None
        ),
        day_branch_main_ten_god=(
            ten_god(bazi.day_master, hidden_main_stem(bazi.day_pillar.earthly_branch))
            if bazi else None
        ),
        # P1-01 天乙贵人(神煞):以日干查命局四支;draft 规则 SMTH-104 专用。
        # 通行为「日干查四支」定式,阴贵/阳贵细分不在本轮。
        tianyi_guiren_branches=(
            [b for b in _FOUR_BRANCHES(bazi) if b in tianyi_guiren(bazi.day_master)]
            if bazi else None
        ),
        soul_palace_main_star_key=(
            ziwei.get("soul") if hasattr(ziwei, "get")
            else getattr(ziwei, "soul_palace_main_star", None)
        ) if ziwei else None,
        soul_palace_main_star_zh=(
            (ziwei.palace_data or {}).get("raw_soul_main_star") if ziwei and hasattr(ziwei, 'palace_data') and ziwei.palace_data else None
        ),
        analysis_day_stem=huangli.day_stem if huangli else None,
        analysis_day_branch=huangli.day_branch if huangli else None,
        layer=layer,
        theme=theme,
        **heluo_fields,
    )


def _rule_to_signal(rule: dict, layer: str, index: int, extra_id: str = "") -> Signal | None:
    conclusion = rule["conclusion"]
    template = conclusion.get("produces_layer_output_template")
    semantic_atoms = conclusion.get("produces_semantic_atoms")
    if template is None:
        # M2-B 兼容:规则若仅有 produces_semantic_atoms（无 produces_layer_output_template），
        # 用 atoms 派生 direction/polarity 派生 signal，保证 canonical path 不被 0-signal 阻断。
        if not semantic_atoms:
            return None
        # 派生 direction：BASELINE/CYCLE_CONTEXT 缺 direction 时默认 NEUTRAL；polarity 留空
        template = {"direction": "STABLE", "polarity": "neutral"}
    # 修复 P0: 根据 rule_refs 前缀决定 source_engine (ZW-* → ZI_WEI, 其余 ZI_PING)
    # EngineName enum 限 ZI_PING/ZI_WEI/... 不能用 "BAZI"/"ZIWEI" 字符串。
    sig_rule_refs = rule_refs_of(rule)
    if any(str(r).startswith("ZW-") for r in sig_rule_refs):
        source_engine = "ZI_WEI"
    elif any(str(r).startswith(("H-", "HE-", "HL-")) for r in sig_rule_refs):
        source_engine = "ZI_PING"  # HELUO 当前未独立EngineName，归 ZI_PING
    else:
        source_engine = "ZI_PING"
    sig = Signal(
        signal_id=f"SIG-{layer[:2].upper()}-{extra_id}{index:03d}",
        ontology_type=rule["produces_signal_type"],
        direction=template["direction"],
        polarity=template["polarity"],
        strength="moderate",
        layer=layer,
        rule_refs=sig_rule_refs,
        evidence_refs=rule.get("evidence_refs", []),
        domain=rule.get("domain", ""),
    )
    # FrozenInstance 需要用 object.__setattr__ 绕过
    object.__setattr__(sig, "source_engine", source_engine)
    return sig


def _build_layer_signals(matcher, bazi, ziwei, huangli, layer, gender, theme, heluo_result=None) -> list:
    ctx = build_rule_context(bazi, ziwei, huangli, layer=layer, theme=theme, heluo_result=heluo_result)
    ctx = replace(ctx, gender=gender)
    matched = matcher.match_all(ctx, layer=layer)
    resolved = resolve_conflicts(matched)
    if layer in ("BASELINE", "CYCLE_CONTEXT"):
        extra_id = bazi.day_master if bazi else ""
    else:
        extra_id = huangli.day_stem if huangli else ""
    return [
        s for s in (
            _rule_to_signal(r, layer, i, extra_id)
            for i, r in enumerate(resolved)
        )
        if s is not None
    ]


def build_signals(bazi, ziwei, huangli, matcher, gender, theme=None, heluo_result=None) -> dict:
    """Match rules per layer and emit one Signal per resolved (layer, type).

    gender is REQUIRED per Profile Contract §1.2 (forbidden_default=true).
    """
    assert gender in ("male", "female"), f"gender must be male/female, got {gender!r}"
    signals_by_layer = {
        layer: _build_layer_signals(matcher, bazi, ziwei, huangli, layer, gender, theme, heluo_result=heluo_result)
        for layer in SIGNAL_LAYER_ORDER
    }
    # 修复 P0: 当 ziwei_chart 非空时，合成一条 ZIWEI BASELINE signal,
    # 确保 ZI_WEI by_engine 始终有 evidence → cross_status ALIGNED。
    if ziwei is not None and "BASELINE" in signals_by_layer:
        # 兼容 dict (ziwei_adapter.compute 返回) 和 ZiweiChart 对象 (ziwei_engine.compute 返回)
        if hasattr(ziwei, "get"):
            soul = ziwei.get("soul") or ziwei.get("soul_palace_main_star")
        else:
            soul = getattr(ziwei, "soul", None) or getattr(ziwei, "soul_palace_main_star", None)
        if soul:
            sig = Signal(
                signal_id="SIG-BA-ZW-CHART-001",
                ontology_type="SUPPORT",  # USO_TYPES 限定 8 种 ontology_type 之一
                direction="STABLE",
                polarity="neutral",
                strength="moderate",
                layer="BASELINE",
                rule_refs=["ZW-CHART-SYNTH"],
                evidence_refs=["ZW-CHART-SOUL"],
                domain="",
            )
            object.__setattr__(sig, "source_engine", "ZI_WEI")
            signals_by_layer["BASELINE"].append(sig)
    return signals_by_layer


class SignalEngine:
    def __init__(self, matcher: RuleMatcher):
        self._matcher = matcher

    def build(self, bazi, ziwei, huangli, gender, theme=None, heluo_result=None) -> dict:
        """Build signals. gender is REQUIRED.

        Returns dual-track dict:
          {"signals": legacy, "canonical_signals": canonical}
        """
        legacy = build_signals(bazi, ziwei, huangli, self._matcher, gender=gender, theme=theme, heluo_result=heluo_result)
        canonical = build_canonical_signals(bazi, ziwei, huangli, self._matcher, gender=gender, theme=theme, heluo_result=heluo_result)
        return {"signals": legacy, "canonical_signals": canonical}


# CanonicalSignal direction mapping (legacy rule direction �� canonical)
_DIRECTION_MAP = {
    "INCREASE": "POSITIVE",
    "DECLINE": "NEGATIVE",
    "STABLE": "NEUTRAL",
    "VOLATILE": "CHANGE",
}

_TEMPORAL_SCOPE_BY_LAYER = {
    "BASELINE": SignalTemporalScope(granularity="YEARLY"),
    "CYCLE_CONTEXT": SignalTemporalScope(granularity="YEARLY"),
    "DAILY_ACTIVATION": SignalTemporalScope(granularity="MONTHLY"),
}


def _signal_to_canonical(signal: Signal) -> CanonicalSignal:
    """Map a legacy Signal to a CanonicalSignal."""
    direction = _DIRECTION_MAP.get(signal.direction, "UNKNOWN")
    layer_scope = _TEMPORAL_SCOPE_BY_LAYER.get(signal.layer, SignalTemporalScope(granularity="YEARLY"))
    return CanonicalSignal(
        signal_id=signal.signal_id,
        source_engine=SourceEngine.BAZI,
        ontology_type=signal.ontology_type,
        event_types=[],
        direction=direction,
        confidence=0.5,
        temporal_scope=layer_scope,
        evidence_refs=signal.evidence_refs,
        rule_refs=signal.rule_refs,
        layer=SignalLayer(signal.layer),
        extracted_at=datetime.now(timezone.utc).isoformat(),
        domain=signal.domain,
        system="BAZI",
    )


def build_canonical_signals(
    bazi, ziwei, huangli, matcher, gender, theme=None, heluo_result=None,
) -> dict:
    """Build canonical signal dicts parallel to build_signals."""
    legacy = build_signals(bazi, ziwei, huangli, matcher, gender, theme=theme, heluo_result=heluo_result)
    result = {}
    for layer, signals in legacy.items():
        result[layer] = [_signal_to_canonical(s) for s in signals]
    return result
