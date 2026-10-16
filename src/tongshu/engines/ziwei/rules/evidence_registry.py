# -*- coding: utf-8 -*-
"""紫微证据引用注册表 — ZW-* 证据链回查表（Z80-H）。

背景（Z80-G 待裁决项 3）：
    ``method_graphs.py`` 的 ``RuleSpec.evidence_refs`` 以 f-string 模板生成
    4 族证据引用，但全项目**无注册表定义**（仅模板字符串）：

        ZW-SIHUA-{stem}      四化表证据（10 天干）
        ZW-STAR-{star}       主星断语证据（14 主星）
        ZW-PATTERN-{name}    格局定义证据（PATTERN_DEFS 全部）
        ZW-PALACE-{palace}   十二宫主题证据（12 宫）

    由于没有「ref_id → 出处元信息」的显式登记，证据链在审计 G1 gate
    （``audit_validation/gates/g1_evidence.py``）中**无法回查**——只能看到
    一个模板串，既不知出自哪部典籍、哪一章，也无从校验完整性。

本模块为这 4 族建立**显式注册表**，并保证「模板可生成的全部 ref_id」
一一在册（``completeness_report`` 可自校验）。

边界（沿用算→辨→解分层铁律）：
  - 本模块只登记「引用元信息」（ref_id / 出处 / 章节 / 校验状态），
    不产生任何判断、评分或断语；不含方向/吉凶。
  - 数据源均为已存在的权威定义（PATTERN_DEFS / GAN_SIHUA /
    STAR_JUDGMENTS / 十二宫序），不新增命理内容。

Public API:
    ZWEvidenceRecord           — 单条引用元信息
    ZW_EVIDENCE_REGISTRY       — {ref_id: ZWEvidenceRecord}
    resolve_zw_evidence_ref    — 按 ref_id 回查
    registry_ids               — 全部已登记 ref_id 集合
    template_generated_ids     — 模板可生成的全部 ref_id（校验用）
    completeness_report        — 覆盖度自检（缺失/多余）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Set

# 十二宫序（与 rule_graph.ZW_PALACES_ORDER / 引擎盘面一致；第 8 宫为「仆役」）
_PALACES_12 = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
]


@dataclass(frozen=True)
class ZWEvidenceRecord:
    """单条 ZW-* 证据引用元信息。"""
    ref_id: str
    family: Literal["SIHUA", "STAR", "PATTERN", "PALACE"]
    source_work: str
    source_chapter: str
    verification_status: Literal["canonical", "candidate", "unverified"]

    def to_dict(self) -> dict:
        return {
            "ref_id": self.ref_id,
            "family": self.family,
            "source_work": self.source_work,
            "source_chapter": self.source_chapter,
            "verification_status": self.verification_status,
        }


def _build_sihua_refs() -> Dict[str, ZWEvidenceRecord]:
    """ZW-SIHUA-{stem}：十干四化表证据（《紫微斗数全书》四化篇）。"""
    from ...ziwei_engine import GAN_SIHUA
    out: Dict[str, ZWEvidenceRecord] = {}
    for stem in GAN_SIHUA:
        rid = f"ZW-SIHUA-{stem}"
        out[rid] = ZWEvidenceRecord(
            ref_id=rid,
            family="SIHUA",
            source_work="紫微斗数全书",
            source_chapter="四化篇",
            verification_status="canonical",
        )
    return out


def _build_star_refs() -> Dict[str, ZWEvidenceRecord]:
    """ZW-STAR-{star}：14 主星断语证据（《紫微斗数全书》星曜论）。"""
    from .sanhe_judgments import STAR_JUDGMENTS
    out: Dict[str, ZWEvidenceRecord] = {}
    for star in STAR_JUDGMENTS:
        rid = f"ZW-STAR-{star}"
        out[rid] = ZWEvidenceRecord(
            ref_id=rid,
            family="STAR",
            source_work="紫微斗数全书",
            source_chapter=f"星曜论·{star}所主若何",
            verification_status="canonical",
        )
    return out


def _build_pattern_refs() -> Dict[str, ZWEvidenceRecord]:
    """ZW-PATTERN-{name}：格局定义证据（《紫微斗数全书》格局篇）。"""
    from .rule_graph import PATTERN_DEFS
    out: Dict[str, ZWEvidenceRecord] = {}
    for name, _stars, _desc in PATTERN_DEFS:
        rid = f"ZW-PATTERN-{name}"
        out[rid] = ZWEvidenceRecord(
            ref_id=rid,
            family="PATTERN",
            source_work="紫微斗数全书",
            source_chapter="格局篇",
            verification_status="candidate",
        )
    return out


def _build_palace_refs() -> Dict[str, ZWEvidenceRecord]:
    """ZW-PALACE-{palace}：十二宫主题证据（《紫微斗数全书》十二宫）。"""
    out: Dict[str, ZWEvidenceRecord] = {}
    for palace in _PALACES_12:
        rid = f"ZW-PALACE-{palace}"
        out[rid] = ZWEvidenceRecord(
            ref_id=rid,
            family="PALACE",
            source_work="紫微斗数全书",
            source_chapter="十二宫",
            verification_status="canonical",
        )
    return out


def _build_registry() -> Dict[str, ZWEvidenceRecord]:
    reg: Dict[str, ZWEvidenceRecord] = {}
    for builder in (_build_sihua_refs, _build_star_refs,
                    _build_pattern_refs, _build_palace_refs):
        reg.update(builder())
    return reg


# 懒加载缓存（避免在 rules 包 import 期触发 method_graphs/qintian 导入链）
_REGISTRY_CACHE: Dict[str, ZWEvidenceRecord] = {}


def _registry() -> Dict[str, ZWEvidenceRecord]:
    if not _REGISTRY_CACHE:
        _REGISTRY_CACHE.update(_build_registry())
    return _REGISTRY_CACHE


# ── Public API ──────────────────────────────────────────────────────────

def resolve_zw_evidence_ref(ref_id: str) -> "ZWEvidenceRecord | None":
    """按 ZW-* ref_id 回查证据元信息；未登记返回 None（fail-closed）。"""
    return _registry().get(ref_id)


def registry_ids() -> Set[str]:
    """全部已登记 ref_id 集合。"""
    return set(_registry().keys())


def template_generated_ids() -> Set[str]:
    """method_graphs 模板**可生成**的全部 ref_id（4 族全集，用于覆盖度校验）。"""
    from ...ziwei_engine import GAN_SIHUA
    from .sanhe_judgments import STAR_JUDGMENTS
    from .rule_graph import PATTERN_DEFS

    ids: Set[str] = set()
    ids |= {f"ZW-SIHUA-{s}" for s in GAN_SIHUA}
    ids |= {f"ZW-STAR-{s}" for s in STAR_JUDGMENTS}
    ids |= {f"ZW-PATTERN-{name}" for name, _s, _d in PATTERN_DEFS}
    ids |= {f"ZW-PALACE-{p}" for p in _PALACES_12}
    return ids


def completeness_report() -> dict:
    """覆盖度自检：模板可生成的 ref_id 是否全部在册（缺失/多余）。"""
    expected = template_generated_ids()
    registered = registry_ids()
    missing: List[str] = sorted(expected - registered)
    extra: List[str] = sorted(registered - expected)
    return {
        "expected_count": len(expected),
        "registered_count": len(registered),
        "missing": missing,
        "extra": extra,
        "complete": not missing and not extra,
    }


__all__ = [
    "ZWEvidenceRecord",
    "ZW_EVIDENCE_REGISTRY",
    "resolve_zw_evidence_ref",
    "registry_ids",
    "template_generated_ids",
    "completeness_report",
]


def __getattr__(name: str):
    """惰性暴露 ZW_EVIDENCE_REGISTRY（首次访问才构建）。"""
    if name == "ZW_EVIDENCE_REGISTRY":
        reg = _registry()
        globals()[name] = reg
        return reg
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
