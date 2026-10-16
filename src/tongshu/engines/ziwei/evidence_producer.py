"""
P1.2-A — ZiweiEvidenceProducer（紫微斗数证据生产者）

职责：
  - 从 ziwei_engine 输出提取纯事实
  - 输出 list[EngineEvidence]
  - 不产生 direction/polarity/strength/confidence

V13 §五硬约束：EngineEvidence 只保留事实/数值/结构/位置/时间

Z91: 加 produce_from_full_chart() 消费 full_chart() 完整Fact
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any

from ...spec.canonical import EngineEvidence, EngineName, TemporalScope
from ..ziwei_engine import ZiweiChart


class ZiweiEvidenceProducer:
    """紫微斗数证据生产者。

    从 ZiweiChart 提取纯事实证据，输出 EngineEvidence 列表。
    """

    RULE_PREFIX = "ZW"
    CALC_VERSION = "2026.09"
    CONTRACT_VERSION = "v13.0"

    def produce(
        self,
        chart: ZiweiChart,
        birth_year: Optional[int] = None,
    ) -> List[EngineEvidence]:
        """从 ZiweiChart 提取纯事实证据。

        Args:
            chart: ZiweiChart 对象
            birth_year: 出生年份（可选）

        Returns:
            list[EngineEvidence]
        """
        evidences: List[EngineEvidence] = []

        # 1. 命宫主星事实
        for idx, star in enumerate(chart.soul_palace_main_stars):
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-STAR-{star}-{uuid.uuid4().hex[:6]}",
                    engine=EngineName.ZI_WEI,
                    rule_id=f"{self.RULE_PREFIX}_MAIN_STAR_{star.upper()}",
                    value=star,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "star": star,
                        "palace": "命宫",
                        "position": "soul",
                        "star_index": idx,
                    },
                    source_rule_ref="data/rules_index/ziwei_stars.json",
                    source_field="soul_palace_main_stars",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        # 2. 命宫四化事实
        for sihua in chart.soul_palace_sihua:
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-SIHUA-{sihua}-{uuid.uuid4().hex[:6]}",
                    engine=EngineName.ZI_WEI,
                    rule_id=f"{self.RULE_PREFIX}_SIHUA_{sihua}",
                    value=sihua,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "sihua": sihua,
                        "palace": "命宫",
                        "type": "natal",
                    },
                    source_rule_ref="data/rules_index/ziwei_stars.json",
                    source_field="soul_palace_sihua",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        # 3. 各宫位主星事实（消费 ZiweiChart.palaces 字典）
        for palace_name, palace_info in chart.palaces.items():
            if not isinstance(palace_info, dict):
                continue
            stars = palace_info.get("major", [])
            for star in stars:
                evidences.append(
                    EngineEvidence(
                        evidence_id=f"{self.RULE_PREFIX}-PALACE-{palace_name}-{star}-{uuid.uuid4().hex[:6]}",
                        engine=EngineName.ZI_WEI,
                        rule_id=f"{self.RULE_PREFIX}_PALACE_STAR",
                        value=star,
                        temporal_scope=TemporalScope.BIRTH,
                        attributes={
                            "star": star,
                            "palace": palace_name,
                        },
                        source_rule_ref="data/rules_index/ziwei_stars.json",
                        source_field="palace_stars",
                        calculation_version=self.CALC_VERSION,
                        contract_version=self.CONTRACT_VERSION,
                    )
                )

        return evidences

    def produce_from_full_chart(
        self,
        full_chart: Dict[str, Any],
        yearly_mutagen: Optional[List[str]] = None,
        birth_year: Optional[int] = None,
    ) -> List[EngineEvidence]:
        """Z91: 从 full_chart() 完整 Fact 提取 Evidence。

        覆盖：
        - 五行局/命宫/身宫 Fact
        - 12宫宫支/宫干 Fact
        - 12宫主星 Fact
        - 12宫辅煞 Fact
        - 生年四化 Fact（禄/权/科/忌对应具体星曜）

        不判断格局，不生成断言，只提取纯事实。
        """
        evidences: List[EngineEvidence] = []
        palaces = full_chart.get("palaces", {})

        # 1. 基本事实：五行局/命宫/身宫
        five_elements = full_chart.get("fiveElementsClass", "")
        soul_branch = full_chart.get("soulPalaceBranch", "")
        body_branch = full_chart.get("bodyPalaceBranch", "")

        evidences.append(EngineEvidence(
            evidence_id=f"{self.RULE_PREFIX}-BASE-WUXING-{uuid.uuid4().hex[:6]}",
            engine=EngineName.ZI_WEI,
            rule_id=f"{self.RULE_PREFIX}_BASE_FIVE_ELEMENTS",
            value=five_elements,
            temporal_scope=TemporalScope.BIRTH,
            attributes={"type": "five_elements", "value": five_elements},
            source_rule_ref="ziwei_engine.full_chart",
            source_field="fiveElementsClass",
            calculation_version=self.CALC_VERSION,
            contract_version=self.CONTRACT_VERSION,
        ))

        evidences.append(EngineEvidence(
            evidence_id=f"{self.RULE_PREFIX}-BASE-SOUL-{uuid.uuid4().hex[:6]}",
            engine=EngineName.ZI_WEI,
            rule_id=f"{self.RULE_PREFIX}_BASE_SOUL_PALACE",
            value=soul_branch,
            temporal_scope=TemporalScope.BIRTH,
            attributes={"type": "soul_palace", "branch": soul_branch},
            source_rule_ref="ziwei_engine.full_chart",
            source_field="soulPalaceBranch",
            calculation_version=self.CALC_VERSION,
            contract_version=self.CONTRACT_VERSION,
        ))

        evidences.append(EngineEvidence(
            evidence_id=f"{self.RULE_PREFIX}-BASE-BODY-{uuid.uuid4().hex[:6]}",
            engine=EngineName.ZI_WEI,
            rule_id=f"{self.RULE_PREFIX}_BASE_BODY_PALACE",
            value=body_branch,
            temporal_scope=TemporalScope.BIRTH,
            attributes={"type": "body_palace", "branch": body_branch},
            source_rule_ref="ziwei_engine.full_chart",
            source_field="bodyPalaceBranch",
            calculation_version=self.CALC_VERSION,
            contract_version=self.CONTRACT_VERSION,
        ))

        # 2. 12宫事实：每宫宫干/宫支/主星/辅星
        for pname, pdata in palaces.items():
            stem = pdata.get("stem", "")
            branch = pdata.get("branch", "")
            major = pdata.get("major", [])
            minor = pdata.get("minor", [])
            dr = pdata.get("decadalRange", [])

            # 宫位基本Fact
            evidences.append(EngineEvidence(
                evidence_id=f"{self.RULE_PREFIX}-PALACE-{pname}-{uuid.uuid4().hex[:6]}",
                engine=EngineName.ZI_WEI,
                rule_id=f"{self.RULE_PREFIX}_PALACE_BASIC",
                value=f"{pname}({stem}{branch})",
                temporal_scope=TemporalScope.BIRTH,
                attributes={
                    "palace": pname,
                    "stem": stem,
                    "branch": branch,
                    "decadal_range": dr,
                },
                source_rule_ref="ziwei_engine.full_chart",
                source_field=f"palaces.{pname}",
                calculation_version=self.CALC_VERSION,
                contract_version=self.CONTRACT_VERSION,
            ))

            # 主星Fact
            for star in major:
                evidences.append(EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-PALACE-{pname}-{star}-{uuid.uuid4().hex[:6]}",
                    engine=EngineName.ZI_WEI,
                    rule_id=f"{self.RULE_PREFIX}_PALACE_MAIN_STAR",
                    value=star,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "palace": pname,
                        "star": star,
                        "type": "main",
                    },
                    source_rule_ref="ziwei_engine.full_chart",
                    source_field=f"palaces.{pname}.major",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                ))

            # 辅煞Fact
            for star in minor:
                evidences.append(EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-PALACE-{pname}-{star}-{uuid.uuid4().hex[:6]}",
                    engine=EngineName.ZI_WEI,
                    rule_id=f"{self.RULE_PREFIX}_PALACE_AUX_STAR",
                    value=star,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "palace": pname,
                        "star": star,
                        "type": "minor",
                    },
                    source_rule_ref="ziwei_engine.full_chart",
                    source_field=f"palaces.{pname}.minor",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                ))

        # 3. 生年四化Fact：禄/权/科/忌对应具体星曜
        if yearly_mutagen and len(yearly_mutagen) == 4:
            sihua_labels = ["禄", "权", "科", "忌"]
            for label, star in zip(sihua_labels, yearly_mutagen):
                if star:
                    evidences.append(EngineEvidence(
                        evidence_id=f"{self.RULE_PREFIX}-SIHUA-{label}-{star}-{uuid.uuid4().hex[:6]}",
                        engine=EngineName.ZI_WEI,
                        rule_id=f"{self.RULE_PREFIX}_YEARLY_SIHUA_{label}",
                        value=star,
                        temporal_scope=TemporalScope.BIRTH,
                        attributes={
                            "sihua_type": label,
                            "star": star,
                            "layer": "natal",
                        },
                        source_rule_ref="ziwei_engine.compute",
                        source_field="palace_data.yearly_mutagen",
                        calculation_version=self.CALC_VERSION,
                        contract_version=self.CONTRACT_VERSION,
                    ))

        return evidences
