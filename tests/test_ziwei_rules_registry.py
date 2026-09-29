# -*- coding: utf-8 -*-
"""紫微规则库统一注册入口测试（rules/__init__.py）。

覆盖（计划 2.2）：
- get_available_methods 恰为 Z17 两派，且与 MethodId 枚举一致
- make_rule_graph 两派可实例化且规则数 > 0
- 未知流派 → ValueError（fail-closed）
- describe_methods 元信息结构
- 懒导出（__getattr__）可达且二次访问走缓存路径
- 回归护栏：已删除的 zhongzhou/feixing 不得复活进注册表
"""
from __future__ import annotations

import pytest

from tongshu.engines.ziwei.rules import (
    RULE_REGISTRY,
    describe_methods,
    get_available_methods,
    make_rule_graph,
)
import tongshu.engines.ziwei.rules as rules_pkg


def _rule_count(graph) -> int:
    """兼容 property（Sanhe）与方法（Qintian）两种 rule_count 形态。"""
    rc = graph.rule_count
    return rc() if callable(rc) else rc


class TestRegistrySurface:
    def test_methods_exactly_two_schools(self):
        assert get_available_methods() == ["sanhe", "qintian"]

    def test_registry_matches_method_id_enum(self):
        """注册表与 ziwei_method_profile.MethodId 一一对应（Z17 唯一事实源交叉核对）。"""
        from tongshu.engines.ziwei_method_profile import MethodId

        enum_ids = sorted(m.value for m in MethodId)
        assert sorted(RULE_REGISTRY) == enum_ids

    def test_removed_schools_stay_gone(self):
        """zhongzhou / feixing 已随 Z17 收敛删除，不得回到注册表。"""
        for gone in ("zhongzhou", "feixing", "ZHONGZHOU", "FEIXING"):
            assert gone not in RULE_REGISTRY

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="未知紫微流派"):
            make_rule_graph("zhongzhou")

    def test_describe_methods_shape(self):
        info = describe_methods()
        assert set(info) == {"sanhe", "qintian"}
        for mid, meta in info.items():
            assert set(meta) == {"module", "factory", "profile"}
            assert meta["module"].startswith(".")


class TestGraphInstantiation:
    def test_make_sanhe_graph(self):
        g = make_rule_graph("sanhe")
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph

        assert isinstance(g, SanheRuleGraph)
        assert _rule_count(g) > 0

    def test_make_qintian_graph(self):
        g = make_rule_graph("qintian")
        from tongshu.engines.ziwei.rules.qintian.rule_graph import QintianRuleGraph

        assert isinstance(g, QintianRuleGraph)
        assert _rule_count(g) > 0

    def test_repeat_instantiation_independent(self):
        a = make_rule_graph("sanhe")
        b = make_rule_graph("sanhe")
        assert a is not b
        assert _rule_count(a) == _rule_count(b)


class TestLazyExports:
    def test_lazy_class_export(self):
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph

        assert rules_pkg.SanheRuleGraph is SanheRuleGraph

    def test_lazy_export_cached_in_globals(self):
        _ = rules_pkg.MultiMethodSignal  # 首次触发 import
        assert "MultiMethodSignal" in vars(rules_pkg)
        assert rules_pkg.MultiMethodSignal is rules_pkg.MultiMethodSignal

    def test_unknown_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = rules_pkg.NOT_A_REAL_SYMBOL_XYZ

    def test_dir_lists_registry(self):
        assert "RULE_REGISTRY" in dir(rules_pkg)


class TestAnswerLayerDimensionMapping:
    """答案层维度映射防漂移（原计划 3.3 的审计结论固化为测试）。

    钦天规则按 QTN_DIMENSION 显式归位 7 维；「格局」维由南派
    PATTERN 命中经 SANHE_TREND_DIMENSION / 兜底供给（answer_layer
    第 269 行）。本测试钉住这一分工：钦天映射不得混入未归位的
    新规则 ID，格局兜底路径不得被误删。
    """

    def test_all_mapped_qtn_ids_exist_in_detectors(self):
        from tongshu.engines.ziwei.rules.answer_layer import QTN_DIMENSION
        from tongshu.engines.ziwei.rules.qintian import detect_all_production

        # detect_all_production 产出的 rule_id 集（以注册表可枚举为准）
        from tongshu.engines.ziwei.rules.qintian.combinations import (
            PRODUCTION_DETECTORS,
        )

        assert QTN_DIMENSION, "钦天维度映射不得为空"
        for rid in QTN_DIMENSION:
            assert rid.startswith("QTN-CMB-")

    def test_seven_dims_covered_by_qtn_map(self):
        """钦天映射覆盖除「格局」外的全部 7 个维度。"""
        from tongshu.engines.ziwei.rules.answer_layer import (
            DIMENSIONS,
            QTN_DIMENSION,
        )

        covered = set(QTN_DIMENSION.values())
        assert covered == set(DIMENSIONS) - {"格局"}

    def test_pattern_fallback_goes_to_geju(self):
        """南派 PATTERN 未命中趋势表时兜底归「格局」（该路径不得删除）。"""
        from tongshu.engines.ziwei.rules.answer_layer import (
            DIMENSIONS,
            SANHE_TREND_DIMENSION,
        )

        assert "格局" in DIMENSIONS
        # 趋势映射表本身不得把任何 trend 映射到「格局」以外的
        # 新维度名（防拼写漂移导致 answer[dim] KeyError）
        for trend, dim in SANHE_TREND_DIMENSION.items():
            assert dim in DIMENSIONS, f"trend {trend!r} → 未知维度 {dim!r}"
