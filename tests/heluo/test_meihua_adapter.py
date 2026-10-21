# -*- coding: utf-8 -*-
"""梅花易数 MeihuaAdapter 测试."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from tongshu.feature_registry.contract import FeatureRegistry
from tongshu.feature_registry.adapters.mei_hua_adapter import MeiHuaFeatureAdapter
from tongshu.engines.meihua import cast_by_time, cast_by_numbers


class TestMeiHuaAdapterFactory:
    """Adapter注册和初始化测试."""

    def test_adapter_creates_registry(self):
        """适配器能创建registry并注册features."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        assert adapter is not None
        # 检查关键feature已注册
        assert registry.has("MH.BEN_GUA")
        assert registry.has("MH.DONG_YAO")
        assert registry.has("MH.TI")
        assert registry.has("MH.YONG")

    def test_all_15_features_registered(self):
        """所有15个feature应被注册."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        expected = [
            "MH.BEN_GUA", "MH.UPPER", "MH.LOWER", "MH.BIAN_GUA",
            "MH.HU_GUA", "MH.CUO_GUA", "MH.ZONG_GUA", "MH.DONG_YAO",
            "MH.TI", "MH.YONG", "MH.TI_ELEMENT", "MH.YONG_ELEMENT",
            "MH.TI_YONG_RELATION", "MH.METHOD", "MH.QUESTION",
        ]
        for fid in expected:
            assert registry.has(fid), f"Missing: {fid}"


class TestMeiHuaAdapterAdaptTime:
    """Mode A: 时间起卦 adapter测试."""

    def test_adapt_time_cast_result(self):
        """时间起卦结果应正确适配为Feature."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_time(2021, 1, 1, 17)
        features = adapter.adapt(result)

        assert features.engine == "MEIHUA"
        assert features.resolved > 0
        # 检查关键字段
        ben_gua_feat = next((f for f in features.resolved_features if f.feature_id == "MH.BEN_GUA"), None)
        assert ben_gua_feat is not None
        assert ben_gua_feat.value == "雷水解"

    def test_dong_yao_preserved(self):
        """动爻值应正确传递."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_time(2021, 1, 1, 1)  # dong_yao=6
        features = adapter.adapt(result)

        dy_feat = next((f for f in features.resolved_features if f.feature_id == "MH.DONG_YAO"), None)
        assert dy_feat is not None
        assert dy_feat.value == 6

    def test_ti_yong_preserved(self):
        """体用关系应正确传递."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_time(2021, 1, 1, 17)
        features = adapter.adapt(result)

        ti_feat = next((f for f in features.resolved_features if f.feature_id == "MH.TI"), None)
        yong_feat = next((f for f in features.resolved_features if f.feature_id == "MH.YONG"), None)
        rel_feat = next((f for f in features.resolved_features if f.feature_id == "MH.TI_YONG_RELATION"), None)

        assert ti_feat.value == "震"
        assert yong_feat.value == "坎"
        assert "用生体" in rel_feat.value

    def test_method_preserved(self):
        """起卦方法应标记为'时间起卦'."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_time(2021, 1, 1, 17)
        features = adapter.adapt(result)

        method_feat = next((f for f in features.resolved_features if f.feature_id == "MH.METHOD"), None)
        assert method_feat.value == "时间起卦"


class TestMeiHuaAdapterAdaptNumber:
    """Mode B: 数字起卦 adapter测试."""

    def test_adapt_number_cast_result(self):
        """数字起卦结果应正确适配."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_numbers(3, 5)
        features = adapter.adapt(result)

        assert features.engine == "MEIHUA"
        ben_gua_feat = next((f for f in features.resolved_features if f.feature_id == "MH.BEN_GUA"), None)
        assert ben_gua_feat.value == "火风鼎"

    def test_dong_yao_preserved_number(self):
        """数字起卦动爻应正确传递."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_numbers(3, 3)  # dong_yao=6
        features = adapter.adapt(result)

        dy_feat = next((f for f in features.resolved_features if f.feature_id == "MH.DONG_YAO"), None)
        assert dy_feat.value == 6

    def test_method_preserved_number(self):
        """数字起卦方法应标记."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_numbers(3, 5)
        features = adapter.adapt(result)

        method_feat = next((f for f in features.resolved_features if f.feature_id == "MH.METHOD"), None)
        assert method_feat.value == "数字起卦"


class TestMeiHuaAdapterFailClosed:
    """Fail-closed测试."""

    def test_adapt_none_input(self):
        """None输入不应崩溃."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        features = adapter.adapt(None)
        assert features.engine == "MEIHUA"
        assert features.resolved == 0

    def test_adapt_dict_input(self):
        """字典输入应正常处理."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        features = adapter.adapt({"ben_gua": "乾为天", "dong_yao_1based": 2})
        assert features.resolved > 0

    def test_adapt_empty_dict(self):
        """空字典输入不应崩溃."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        features = adapter.adapt({})
        assert features.engine == "MEIHUA"
        assert features.resolved == 0


class TestMeiHuaAdapterCompleteness:
    """完整性测试."""

    def test_all_fields_mapped(self):
        """所有MeihuaResult字段应被映射."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_numbers(1, 1)
        features = adapter.adapt(result)

        # 检查所有15个feature都被解析
        feature_ids = {f.feature_id for f in features.resolved_features}
        expected = {
            "MH.BEN_GUA", "MH.UPPER", "MH.LOWER", "MH.BIAN_GUA",
            "MH.HU_GUA", "MH.CUO_GUA", "MH.ZONG_GUA", "MH.DONG_YAO",
            "MH.TI", "MH.YONG", "MH.TI_ELEMENT", "MH.YONG_ELEMENT",
            "MH.TI_YONG_RELATION", "MH.METHOD", "MH.QUESTION",
        }
        assert expected.issubset(feature_ids), f"Missing: {expected - feature_ids}"

    def test_feature_metadata_correct(self):
        """Feature元数据应正确."""
        registry = FeatureRegistry()
        adapter = MeiHuaFeatureAdapter(registry)
        result = cast_by_numbers(1, 1)
        features = adapter.adapt(result)

        for feat in features.resolved_features:
            assert feat.engine == "MEIHUA"
            assert feat.namespace == "MH"
            assert feat.source_evidence_ref.startswith("MH-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
