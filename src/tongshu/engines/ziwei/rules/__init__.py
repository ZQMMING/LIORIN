# -*- coding: utf-8 -*-
"""紫微规则库统一入口 — Z17 两派收敛（SANHE 南派 / QINTIAN 北派）。

设计约束：
1. 懒加载：本包被 `import tongshu.engines.ziwei.rules` 时不得触发任何规则
   子模块导入（method_graphs / qintian / multi_method 之间存在相对导入链，
   急切导入会在部分调用路径上引入循环导入风险）。子模块一律经
   ``__getattr__`` 或注册表工厂在首次使用时导入。
2. 注册表是流派可发现性的唯一事实源：get_available_methods() 的返回值
   与 ziwei_method_profile.MethodId 一一对应；新增/删除流派必须同时改两处。
3. 本模块只做"获取/实例化规则图"，不做匹配、评分、断事——那是各
   RuleGraph 与解层的职责（算→辨→解分层铁律）。
"""
from __future__ import annotations

import importlib
from typing import Any, Callable

__all__ = [
    "RULE_REGISTRY",
    "get_available_methods",
    "make_rule_graph",
    "describe_methods",
]

# method_id -> (相对模块路径, 工厂属性名, 流派档案标签)
# 工厂属性既可以是类（SanheRuleGraph），也可以是工厂函数
# （make_qintian_rule_graph），调用方式一致：factory()。
RULE_REGISTRY: dict[str, tuple[str, str, str]] = {
    "sanhe": (".method_graphs", "SanheRuleGraph", "SANHE-NIHAI"),
    "qintian": (".qintian", "make_qintian_rule_graph", "QINTIAN-XUANTIAN"),
}


def get_available_methods() -> list[str]:
    """返回已注册流派标识列表（与 MethodId 枚举值一致）。"""
    return list(RULE_REGISTRY)


def make_rule_graph(method_id: str) -> Any:
    """按流派实例化对应 RuleGraph（延迟导入，避免循环依赖）。

    Args:
        method_id: "sanhe" / "qintian"（见 get_available_methods）

    Returns:
        对应流派的 RuleGraph 实例（提供 match_all(chart) / rule_count）。

    Raises:
        ValueError: 未知流派标识。
    """
    entry = RULE_REGISTRY.get(method_id)
    if entry is None:
        raise ValueError(
            f"未知紫微流派: {method_id!r}；可用: {get_available_methods()}"
        )
    rel_module, factory_name, _profile = entry
    module = importlib.import_module(rel_module, __name__)
    factory: Callable[[], Any] = getattr(module, factory_name)
    return factory()


def describe_methods() -> dict[str, dict[str, str]]:
    """各流派的注册元信息（供审计/调试，不触发规则模块导入）。"""
    return {
        mid: {"module": mod, "factory": fac, "profile": prof}
        for mid, (mod, fac, prof) in RULE_REGISTRY.items()
    }


# ── 向后兼容的懒导出 ──────────────────────────────────────────────
# 允许 `from tongshu.engines.ziwei.rules import SanheRuleGraph` 等旧式
# 直接引用；首次访问时才真正导入对应子模块。
_LAZY_EXPORTS: dict[str, str] = {
    # method_graphs
    "SanheRuleGraph": ".method_graphs",
    "BaseZiweiRuleGraph": ".method_graphs",
    # multi_method（集成器与其数据模型）
    "MultiMethodSignal": ".multi_method",
    "MethodBundle": ".multi_method",
    "MethodMatch": ".multi_method",
    "compute_multi_method_signals": ".multi_method",
    # evidence_registry（ZW-* 证据链回查表，Z80-H）
    "ZWEvidenceRecord": ".evidence_registry",
    "ZW_EVIDENCE_REGISTRY": ".evidence_registry",
    "resolve_zw_evidence_ref": ".evidence_registry",
    "registry_ids": ".evidence_registry",
    "template_generated_ids": ".evidence_registry",
    "completeness_report": ".evidence_registry",
    # asset_index（11 未接线资产索引，Z80-H）
    "AssetDisposition": ".asset_index",
    "UnwiredAsset": ".asset_index",
    "ZIWEI_UNWIRED_ASSETS": ".asset_index",
    "asset_inventory": ".asset_index",
    "asset_report": ".asset_index",
    "load_asset": ".asset_index",
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        # 兜底：允许穿透访问子模块本身（如 rules.qintian）
        try:
            return importlib.import_module(name, __name__)
        except ImportError:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from None
    module = importlib.import_module(target, __name__)
    value = getattr(module, name)
    globals()[name] = value  # 缓存，避免重复导入
    return value


def __dir__() -> list[str]:
    return sorted(set(list(globals()) + list(_LAZY_EXPORTS) + ["RULE_REGISTRY"]))
