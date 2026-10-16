# -*- coding: utf-8 -*-
"""紫微未接线资产索引 — Z80-H（原 Z80-G 待裁决项「11 个零引用模块」）。

背景：
    Z80-G 审计发现 11 个模块在 ``src/`` + ``tests/`` + ``scripts/`` 中
    **全部零引用**，处于「灰色地带」。审计给出逐项处置建议，但仅在各模块
    docstring 内做了文字标注，**没有机器可查的索引**——即：无人知道
    「一共有哪些未接线资产、各自内容规模多少、处置去向如何」。

    Z80-H 处置结果：**6 个已接线**（接入 ``classical_detail`` 独立通道）、
    1 个收敛（``palace_relationship``）、4 个证据资产入册。本索引即其
    「唯一事实源 + 可自检清单」。

本模块把这 11 个资产收敛为**显式索引**（machine-checkable inventory）：

  处置分四类（Z80-G 审计结论 + Z80-H 接线结果）：
    - ``WIRED``          已接线：Z80-H 已接入 ``classical_detail`` 独立通道
    - ``WIRE``           应接线：生产缺此细目，尚未接线
    - ``CONVERGE``       收敛：与既有实现重复，去重后保留薄封装
    - ``EVIDENCE_INDEX`` 证据资产：古籍原文录入，暂不接生产匹配，
                         仅登记入册供溯源/后续接线

边界（算→辨→解分层铁律）：
  - 本模块只做「登记 + 清点」，不加载后参与任何匹配/判断。
  - 资产内容不可再生（Z77–Z86 期录入的古籍原文），索引不修改其内容。

Public API:
    AssetDisposition           — 处置类别常量
    UnwiredAsset               — 单条未接线资产登记项
    ZIWEI_UNWIRED_ASSETS       — 11 条登记项
    asset_inventory            — 清点（含各模块内容规模）
    asset_report               — 汇总（按处置类别）
    self_check                 — 索引完整性自检
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class AssetDisposition:
    """处置类别（Z80-G 审计结论 + Z80-H 接线结果）。"""
    WIRE = "WIRE"                    # 应接线（尚未接）
    WIRED = "WIRED"                  # 已接线（Z80-H 接入 classical_detail 通道）
    CONVERGE = "CONVERGE"            # 收敛（去重）
    EVIDENCE_INDEX = "EVIDENCE_INDEX"  # 证据资产（登记入册）


@dataclass(frozen=True)
class UnwiredAsset:
    """单条未接线资产登记项。

    Attributes:
        module: 模块名（不含包路径，如 ``pattern_rules``）
        disposition: 处置类别（AssetDisposition.*）
        classical_source: 古籍出处
        rationale: 处置理由（来自 Z80-G 审计）
        count_attrs: 该模块内需清点的顶层数据属性名（UPPER_CASE 容器）
        wired_to: 接线落点（disposition=WIRED 时填写；如 ``classical_detail``）
    """
    module: str
    disposition: str
    classical_source: str
    rationale: str
    count_attrs: Tuple[str, ...] = field(default_factory=tuple)
    wired_to: str = ""


# 包路径前缀（rules 子包）
_PKG = "tongshu.engines.ziwei.rules."


# 11 条未接线资产（顺序沿用 Z80-G 审计表）
ZIWEI_UNWIRED_ASSETS: Tuple[UnwiredAsset, ...] = (
    UnwiredAsset(
        module="pattern_rules",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·卷一/卷二",
        rationale="富6/贵27/贫8/杂8 + 12宫得地12/失陷9 逐宫诀；生产 PATTERN_DEFS 仅星组，无此细目",
        count_attrs=("WEALTH_PATTERN", "NOBILITY_PATTERN", "POVERTY_PATTERN",
                     "MISC_PATTERN", "PALACE_FORTUNE_RULE", "PALACE_DEPRIVATION_RULE",
                     "ALL_PATTERNS", "ALL_PALACE_RULES"),
        wired_to="classical_detail:palace_jue+classical_patterns",
    ),
    UnwiredAsset(
        module="temporal_rules",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·卷二/卷三",
        rationale="时间层解释（太岁小限/斗君/流曜），production 无时间层规则",
        count_attrs=("TAISUI_XIAOXIAN_RULES", "DOUJUN_RULES", "LIUYAO_RULES",
                     "ALL_TEMPORAL_RULES"),
        wired_to="classical_detail:temporal_rules+temporal_facts",
    ),
    UnwiredAsset(
        module="temporal_facts",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·卷二 安星诀",
        rationale="时间层 Fact（大限/小限/童限安法），production 无",
        count_attrs=("FLOW_STAR_BY_YEAR_GAN",),
        wired_to="classical_detail:temporal_facts + ziwei_engine._compute_doujun",
    ),
    UnwiredAsset(
        module="child_limit_rules",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·安童限诀第五十",
        rationale="童限/小儿命，production 无",
        count_attrs=("CHILD_LIMIT_RULES",),
        wired_to="classical_detail:child_limit",
    ),
    UnwiredAsset(
        module="nvming_rules",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·女命骨髓赋第十/诸星问答论",
        rationale="女命体系（女命骨髓赋），production 无女命专条",
        count_attrs=("NVMING_RULES", "NVMING_ZHUAN", "ALL_NVMING"),
        wired_to="classical_detail:nvming",
    ),
    UnwiredAsset(
        module="limit_advanced_rules",
        disposition=AssetDisposition.WIRED,
        classical_source="紫微斗数全书·论羊陀迭并第九十二 等",
        rationale="限运进阶（羊陀迭并/七杀重逢），与 QTN-059/060 概念近但规则不同",
        count_attrs=("LIMIT_ADVANCED_RULES",),
        wired_to="classical_detail:limit_advanced",
    ),
    UnwiredAsset(
        module="palace_relationship",
        disposition=AssetDisposition.CONVERGE,
        classical_source="（抽象事实层，非古籍）",
        rationale="三方四正事实层，与 ZiweiPalaceResolver.resolve_sanfang_sizheng "
                  "及 combinations._triple_of 重复；Z80-H 已收敛为复用 canonical 地支常量",
        count_attrs=(),
    ),
    UnwiredAsset(
        module="wuxing_rules",
        disposition=AssetDisposition.EVIDENCE_INDEX,
        classical_source="紫微斗数全书·第五十八/五十九",
        rationale="星曜五行 + 生克制化原典录入",
        count_attrs=("STAR_WUXING", "WUXING_RULES"),
    ),
    UnwiredAsset(
        module="palace_general_rules",
        disposition=AssetDisposition.EVIDENCE_INDEX,
        classical_source="紫微斗数全书·论命宫诀~论父母诀",
        rationale="十二宫总论，部分已被 palace_star_verdicts 覆盖",
        count_attrs=("PALACE_GENERAL_RULES",),
    ),
    UnwiredAsset(
        module="aux_star_verdicts",
        disposition=AssetDisposition.EVIDENCE_INDEX,
        classical_source="紫微斗数全书·诸星问答论",
        rationale="辅煞杂曜断语，与 palace_star_verdicts/nihai 重叠",
        count_attrs=("AUX_STAR_VERDICTS", "SHA_STAR_VERDICTS", "MISC_STAR_VERDICTS",
                     "ALL_AUX_STARS", "ALL_SHA_STARS", "ALL_MISC_STARS"),
    ),
    UnwiredAsset(
        module="aux_star_ext",
        disposition=AssetDisposition.EVIDENCE_INDEX,
        classical_source="紫微斗数全书·诸星问答论+安星诀",
        rationale="天伤天使/哭虚/鸾喜补遗，QTN-047~055 部分覆盖",
        count_attrs=("TIANSHANG_TIANSHI", "TIANKU_TIANXU", "HONGLUAN_TIANXI",
                     "ALL_AUX_EXT"),
    ),
)


def _count_module(asset: UnwiredAsset) -> Dict[str, int]:
    """加载模块并清点其顶层 UPPER_CASE 容器属性的条目数。"""
    mod = importlib.import_module(_PKG + asset.module)
    out: Dict[str, int] = {}
    for attr in asset.count_attrs:
        val = getattr(mod, attr, None)
        if isinstance(val, (list, tuple, dict)):
            out[attr] = len(val)
    return out


def asset_inventory() -> List[dict]:
    """清点全部未接线资产（含各模块内容规模）。

    ``total_items`` 只统计**非聚合**属性（排除 ``ALL_*`` 汇总项），
    避免与分项重复计数。
    """
    rows: List[dict] = []
    for a in ZIWEI_UNWIRED_ASSETS:
        counts = _count_module(a)
        total = sum(v for k, v in counts.items() if not k.startswith("ALL_"))
        rows.append({
            "module": a.module,
            "disposition": a.disposition,
            "classical_source": a.classical_source,
            "rationale": a.rationale,
            "wired_to": a.wired_to,
            "counts": counts,
            "total_items": total,
        })
    return rows


def asset_report() -> dict:
    """按处置类别汇总。"""
    rows = asset_inventory()
    by_disp: Dict[str, List[str]] = {}
    for r in rows:
        by_disp.setdefault(r["disposition"], []).append(r["module"])
    return {
        "total_modules": len(rows),
        "by_disposition": {k: sorted(v) for k, v in by_disp.items()},
        "total_items": sum(r["total_items"] for r in rows),
    }


def self_check() -> dict:
    """索引完整性自检：11 条登记项齐备，且各模块可加载。"""
    problems: List[str] = []
    if len(ZIWEI_UNWIRED_ASSETS) != 11:
        problems.append(
            f"expected 11 unwired assets, got {len(ZIWEI_UNWIRED_ASSETS)}"
        )
    seen = set()
    for a in ZIWEI_UNWIRED_ASSETS:
        if a.module in seen:
            problems.append(f"duplicate module in index: {a.module}")
        seen.add(a.module)
        if a.disposition not in (
            AssetDisposition.WIRE,
            AssetDisposition.WIRED,
            AssetDisposition.CONVERGE,
            AssetDisposition.EVIDENCE_INDEX,
        ):
            problems.append(f"{a.module}: unknown disposition {a.disposition!r}")
        try:
            _count_module(a)
        except Exception as e:  # 模块缺失/导入失败
            problems.append(f"{a.module}: load failed {type(e).__name__}: {e}")
    return {"ok": not problems, "problems": problems}


def load_asset(module: str):
    """按模块名加载未接线资产模块（显式入口，替代散落的 import）。

    仅登记在册的 11 个模块可加载；未知模块抛 ValueError（fail-closed）。

    Args:
        module: 模块名（如 ``pattern_rules`` / ``temporal_rules``）

    Returns:
        已导入的模块对象（其 UPPER_CASE 数据属性即资产内容）。
    """
    if module not in {a.module for a in ZIWEI_UNWIRED_ASSETS}:
        raise ValueError(
            f"{module!r} 不在未接线资产索引中；"
            f"已登记: {sorted(a.module for a in ZIWEI_UNWIRED_ASSETS)}"
        )
    return importlib.import_module(_PKG + module)


__all__ = [
    "AssetDisposition",
    "UnwiredAsset",
    "ZIWEI_UNWIRED_ASSETS",
    "asset_inventory",
    "asset_report",
    "self_check",
    "load_asset",
]
