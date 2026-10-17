"""P6-C-3C-1 盲派Feature Adapter - 基于BlindChart实际字段."""
from __future__ import annotations
from typing import Any
from tongshu.feature_registry.contract import (
    FeatureRegistry, FeatureDefinition, Feature, FeatureMapResult, BaseFeatureAdapter,
)


class BlindSchoolFeatureAdapter(BaseFeatureAdapter):
    def __init__(self, registry: FeatureRegistry):
        super().__init__(registry)
        self._register_default_features()

    def _register_default_features(self) -> None:
        # BZ-BLIND-001 接入修正：source_field 对齐 BlindBaziResult.to_dict() 真实字段。
        # 原设计期字段 body/use/guest/host/doing_work/palace_data/ten_god_palace/
        # grave/timing 与引擎实际输出不一致（实测全部缺失，adapt() resolved=0 死适配）；
        # 现映射到 ti_branches/yong_branches/guest_branches/main_branches/
        # zuo_gong_methods/space_palace/transparent_ten_gods。
        # GRAVE/TIMING 在 BlindBaziResult 无顶层对应字段（墓库嵌套于
        # marriage_event_structure.spouse_star_into_muku，应期分散于 signals），
        # 保留 feature 定义（registry 契约）但不参与 field_map 映射，避免假接通。
        defaults = [
            ("BLIND.BODY", "BODY_USE", "LIST", "NATAL", "BLIND-BODY", "ti_branches", "体"),
            ("BLIND.USE", "BODY_USE", "LIST", "NATAL", "BLIND-USE", "yong_branches", "用"),
            ("BLIND.GUEST", "GUEST_HOST", "LIST", "NATAL", "BLIND-GUEST", "guest_branches", "宾"),
            ("BLIND.HOST", "GUEST_HOST", "LIST", "NATAL", "BLIND-HOST", "main_branches", "主"),
            ("BLIND.DOING_WORK", "DOING_WORK", "LIST", "NATAL", "BLIND-DOING-WORK", "zuo_gong_methods", "做功链"),
            ("BLIND.PALACE_DATA", "PALACE", "STRING", "NATAL", "BLIND-PALACE-DATA", "space_palace", "宫位数据"),
            ("BLIND.TEN_GOD_PALACE", "TEN_GOD_PALACE", "DICT", "NATAL", "BLIND-TEN-GOD-PALACE", "transparent_ten_gods", "十神落宫"),
            ("BLIND.GRAVE", "GRAVE", "DICT", "NATAL", "BLIND-GRAVE", "grave", "墓库"),
            ("BLIND.TIMING", "TIMING", "DICT", "NATAL", "BLIND-TIMING", "timing", "应期"),
        ]
        for fid, cat, vtype, scope, rule_id, field, desc in defaults:
            if not self.registry.has(fid):
                self.registry.register(FeatureDefinition(
                    feature_id=fid, engine="BLIND_SCHOOL", namespace="BLIND", category=cat,
                    value_type=vtype, scope=scope, source_rule_id=rule_id,
                    source_field=field, description=desc,
                ))

    def adapt(self, chart: Any) -> FeatureMapResult:
        resolved = []
        unmapped = []
        chart_dict = chart.to_dict() if hasattr(chart, 'to_dict') else (chart if isinstance(chart, dict) else {})
        field_map = {
            "BLIND.BODY": "ti_branches",
            "BLIND.USE": "yong_branches",
            "BLIND.GUEST": "guest_branches",
            "BLIND.HOST": "main_branches",
            "BLIND.DOING_WORK": "zuo_gong_methods",
            "BLIND.PALACE_DATA": "space_palace",
            "BLIND.TEN_GOD_PALACE": "transparent_ten_gods",
            # GRAVE / TIMING：BlindBaziResult 无顶层对应字段（见 _register_default_features 注释），
            # 保留 feature 定义但不映射，避免假接通。
        }
        for fid, field_name in field_map.items():
            value = chart_dict.get(field_name)
            if value is not None and self.registry.has(fid):
                defn = self.registry.get(fid)
                resolved.append(Feature(
                    feature_id=fid, value=value, engine="BLIND_SCHOOL", namespace="BLIND",
                    category=defn.category, value_type=defn.value_type, scope=defn.scope,
                    source_rule_id=defn.source_rule_id, source_field=defn.source_field,
                    source_evidence_ref=f"BLIND-{field_name.upper()}",
                ))
            elif value is not None:
                unmapped.append({"rule_id": fid, "value": str(value)[:100]})
        return FeatureMapResult(
            engine="BLIND_SCHOOL", total_evidence=len(field_map),
            resolved=len(resolved), unmapped=len(unmapped),
            resolved_features=resolved, unmapped_evidence=unmapped,
        )
