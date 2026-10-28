"""
P1.2-A — HeLuoEvidenceProducer（河洛理数证据生产者）

职责：
  - 从 heluo_result（canonical.py 输出）提取纯事实
  - 输出 list[EngineEvidence]
  - 不产生 direction/polarity/strength/confidence

V13 §五硬约束：EngineEvidence 只保留事实/数值/结构/位置/时间
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from ...spec.canonical import EngineEvidence, EngineName, TemporalScope

if TYPE_CHECKING:                     # pragma: no cover
    # ⚠ 只用于**类型标注**：运行时 import canonical 会造成循环依赖
    #   （canonical → … → 本模块）。``from __future__ import annotations``
    #   使注解不求值 ⇒ 运行期无影响，mypy/IDE 仍能拿到真类型。
    from .canonical import HeluoResult


class HeLuoEvidenceProducer:
    """河洛理数证据生产者。

    从 HeluoResult 提取纯事实证据，输出 EngineEvidence 列表。
    """

    RULE_PREFIX = "HL"
    CALC_VERSION = "2026.09"
    CONTRACT_VERSION = "v13.0"

    def produce(
        self,
        heluo_result: "HeluoResult",
        birth_year: Optional[int] = None,
    ) -> List[EngineEvidence]:
        """从 HeluoResult 提取纯事实证据。

        Args:
            heluo_result: HeluoResult 对象（来自 heluo/canonical.py）
            birth_year: 出生年份（可选，用于流年证据）

        Returns:
            list[EngineEvidence]
        """
        # ⚠ 2026-10-07 审计修：下列七处 source_rule_ref 原写作
        #   data/rules/heluo_*.json——data/rules/ 下**没有任何这种文件**
        #   （实际是 HL-101…HL-121 二十一个「五行过旺→健康风险」类诊断规则，
        #   与此处的计算事实不同类），属「声称有出处而出处不存在」。
        #   这七个值实际不会流到输出：diagnosis_rule_graph.py 会用注册规则表的
        #   source_ref 覆盖，未注册的则被 continue 丢弃——是源码里的死字符串。
        #   但死字符串仍是伪引：后人照着去 data/rules/ 找必然落空。
        #   现一律改为可核对的原典出处。
        evidences: List[EngineEvidence] = []

        # 1. 天数地数事实
        evidences.append(
            EngineEvidence(
                evidence_id=f"{self.RULE_PREFIX}-NUMBERS-{uuid.uuid4().hex[:8]}",
                engine=EngineName.HE_LUO,
                rule_id=f"{self.RULE_PREFIX}_TIAN_DI_SHU",
                value={
                    "tian_shu": heluo_result.numbers.tian_shu,
                    "di_shu": heluo_result.numbers.di_shu,
                    "tian_reduced": heluo_result.numbers.tian_reduced,
                    "di_reduced": heluo_result.numbers.di_reduced,
                },
                temporal_scope=TemporalScope.BIRTH,
                attributes={
                    "tian_shu": heluo_result.numbers.tian_shu,
                    "di_shu": heluo_result.numbers.di_shu,
                },
                source_rule_ref="起例卷之上·天干取数定局（天数地数）",
                source_field="numbers",
                calculation_version=self.CALC_VERSION,
                contract_version=self.CONTRACT_VERSION,
            )
        )

        # 2. 先天卦事实
        evidences.append(
            EngineEvidence(
                evidence_id=f"{self.RULE_PREFIX}-PRENATAL-{uuid.uuid4().hex[:8]}",
                engine=EngineName.HE_LUO,
                rule_id=f"{self.RULE_PREFIX}_PRENATAL_HEXAGRAM",
                value=heluo_result.prenatal.hexagram_name,
                temporal_scope=TemporalScope.BIRTH,
                attributes={
                    "hexagram_name": heluo_result.prenatal.hexagram_name,
                    "upper_gua": heluo_result.prenatal.upper_gua,
                    "lower_gua": heluo_result.prenatal.lower_gua,
                    "stage": "prenatal",
                },
                source_rule_ref="起例卷之上·八字内天数地数例（先天卦）",
                source_field="prenatal_hexagram",
                calculation_version=self.CALC_VERSION,
                contract_version=self.CONTRACT_VERSION,
            )
        )

        # 3. 元堂事实
        evidences.append(
            EngineEvidence(
                evidence_id=f"{self.RULE_PREFIX}-YUANTANG-{uuid.uuid4().hex[:8]}",
                engine=EngineName.HE_LUO,
                rule_id=f"{self.RULE_PREFIX}_YUANTANG",
                value=heluo_result.yuantang.yuantang,
                temporal_scope=TemporalScope.BIRTH,
                attributes={
                    "yuantang": heluo_result.yuantang.yuantang,
                    "yuantang_index": heluo_result.yuantang.yuantang_index,
                    "yao_nature": heluo_result.yuantang.yao_nature,
                },
                source_rule_ref="三才发秘·详元堂爻位式",
                source_field="yuantang",
                calculation_version=self.CALC_VERSION,
                contract_version=self.CONTRACT_VERSION,
            )
        )

        # 4. 后天卦事实
        evidences.append(
            EngineEvidence(
                evidence_id=f"{self.RULE_PREFIX}-POSTNATAL-{uuid.uuid4().hex[:8]}",
                engine=EngineName.HE_LUO,
                rule_id=f"{self.RULE_PREFIX}_POSTNATAL_HEXAGRAM",
                value=heluo_result.postnatal.hexagram_name,
                temporal_scope=TemporalScope.BIRTH,
                attributes={
                    "hexagram_name": heluo_result.postnatal.hexagram_name,
                    "upper_gua": heluo_result.postnatal.upper_gua,
                    "lower_gua": heluo_result.postnatal.lower_gua,
                    "stage": "postnatal",
                },
                source_rule_ref="起例卷之上·换后天卦例",
                source_field="postnatal_hexagram",
                calculation_version=self.CALC_VERSION,
                contract_version=self.CONTRACT_VERSION,
            )
        )

        # 5. 卦象结构事实
        if heluo_result.structure:
            struct = heluo_result.structure
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-STRUCT-{uuid.uuid4().hex[:8]}",
                    engine=EngineName.HE_LUO,
                    rule_id=f"{self.RULE_PREFIX}_HEXAGRAM_STRUCTURE",
                    value=struct.to_dict() if hasattr(struct, "to_dict") else str(struct),
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "upper": struct.upper,
                        "lower": struct.lower,
                        "name": struct.name if hasattr(struct, "name") else "",
                    },
                    source_rule_ref="起例卷之上·卦体（上下卦合成，非独立断法规则）",
                    source_field="structure",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        # 6. H6 化工事实
        if hasattr(heluo_result, 'hua_gong') and heluo_result.hua_gong:
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-HUAGONG-{uuid.uuid4().hex[:8]}",
                    engine=EngineName.HE_LUO,
                    rule_id=f"{self.RULE_PREFIX}_HUA_GONG",
                    value=heluo_result.hua_gong.state.value,
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "state": heluo_result.hua_gong.state.value,
                        "huagong_trigram": heluo_result.hua_gong.huagong_trigram,
                        "birth_month_branch": heluo_result.hua_gong.birth_month_branch,
                        "has_huagong": heluo_result.hua_gong.has_huagong,
                        "has_opposite": heluo_result.hua_gong.has_opposite,
                        # 2026-10-07 审计修：L576 三级回退的层位与减半标志
                        # 原先不进 attributes，下游只看到 state=WEAK 却无从
                        # 判断是「只得纳音浅薄化工」还是别的原因。
                        "level": getattr(heluo_result.hua_gong, "level", None),
                        "reduced": getattr(heluo_result.hua_gong, "reduced", None),
                    },
                    source_rule_ref="起例卷之下·论化工（L573/L576/L582）",
                    source_field="hua_gong",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        # 7. H11 节候卦事实
        if hasattr(heluo_result, 'seasonal_hexagram') and heluo_result.seasonal_hexagram:
            sh = heluo_result.seasonal_hexagram
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-JIEHOU-{uuid.uuid4().hex[:8]}",
                    engine=EngineName.HE_LUO,
                    rule_id=f"{self.RULE_PREFIX}_JIEHOU_GUA",
                    value=sh.get('main_gua', ''),
                    temporal_scope=TemporalScope.BIRTH,
                    attributes={
                        "jq_name": sh.get('jq_name', ''),
                        "jq_index": sh.get('jq_index'),
                        "main_gua": sh.get('main_gua', ''),
                        "moving_line": sh.get('moving_line'),
                        "result_gua": sh.get('result_gua', ''),
                    },
                    source_rule_ref="起例卷之下·定节候卦说（L1492）",
                    source_field="seasonal_hexagram",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        # 8. 时间层证据（2026-10-25 新增）
        #
        # ⚠ 此前 ``HL_DAYUN`` / ``HL_LIUNIAN_GUA`` / ``HL_YUEGUA`` / ``HL_RIGUA``
        #   四条诊断规则**注册了却从不产出证据** —— 「注册了却不存在」的空授权
        #   （见 diagnosis_rule_graph.HELUO_RULES 的 TODO 注释）。
        #   引擎侧数据本已齐备（timeline 的流年/流月/流日 + 判词层的动爻爻辞），
        #   缺的只是「把时间层数据接到证据环」这一环。
        #
        # 方向来自**原典爻辞判据**（起例卷之上 L212「三辞吉：卦爻中有元吉亨利是也」），
        #   判不出时给 ``passed=None``（**不判**），绝不给 0–1 分数。
        try:
            from .time_layer_judgment import (
                collect_dayun_judgment, collect_time_layer_judgments,
            )
            # ⚠ 判词层可能**未挂载**：``HeluoCanonical.calculate()`` 只算卦，
            #   判词层是由 adapter（或调用方）另行挂上的 ``result.guajie``。
            #   实测：直调 canonical（生产链之外的常见用法，如守卫直调）时
            #   guajie 为 None ⇒ 流年/流月/流日取不到爻辞 ⇒ 判不出。
            #   故此处**自行兜底构建**判词层（只在本层需要时构建，
            #   已有则直接用，避免重复计算）。
            _gj = getattr(heluo_result, "guajie", None)
            if not _gj:
                try:
                    from .guajie import build_guajie_from_result
                    _gj = build_guajie_from_result(heluo_result)
                except Exception:
                    _gj = None
            _judgments = collect_time_layer_judgments(heluo_result, _gj)
            _judgments.append(collect_dayun_judgment(heluo_result))
        except Exception as exc:                     # pragma: no cover
            _judgments = []
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-TIME-ERR-{uuid.uuid4().hex[:8]}",
                    engine=EngineName.HE_LUO,
                    rule_id=f"{self.RULE_PREFIX}_TIME_LAYER_ERROR",
                    value={"error": f"{type(exc).__name__}: {exc}"},
                    temporal_scope=TemporalScope.DAY,
                    attributes={"error": True},
                    source_rule_ref="（时间层证据构建失败，非原典判据）",
                    source_field="time_layer_judgment",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        for _j in _judgments:
            # 只在「该层确实有卦」时产出（无卦的层不硬造证据）
            if not _j.hexagram and _j.rule_id != "HL_DAYUN":
                continue
            evidences.append(
                EngineEvidence(
                    evidence_id=f"{self.RULE_PREFIX}-{_j.rule_id}-{uuid.uuid4().hex[:8]}",
                    engine=EngineName.HE_LUO,
                    rule_id=_j.rule_id,
                    # value 只放**事实**（卦名/爻位/爻辞），方向另存 attributes
                    value={
                        "hexagram": _j.hexagram,
                        "yao": _j.yao,
                        "ci": _j.ci,
                    },
                    temporal_scope=TemporalScope.DAY,
                    attributes={
                        "hexagram": _j.hexagram,
                        "yao": _j.yao,
                        # ⚠ direction 用三态字符串表示，不给数值分数
                        "judgment": ("吉" if _j.passed is True
                                     else "凶" if _j.passed is False
                                     else "不判"),
                        "passed": _j.passed,
                        "basis": _j.basis,
                        "detail": _j.detail,
                        "source_ref": _j.source_ref,
                    },
                    source_rule_ref=_j.source_ref or "（时间层）",
                    source_field="time_layer",
                    calculation_version=self.CALC_VERSION,
                    contract_version=self.CONTRACT_VERSION,
                )
            )

        return evidences
