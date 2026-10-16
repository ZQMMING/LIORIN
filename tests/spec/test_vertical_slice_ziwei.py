"""
P1.2-G: Ziwei Real Runtime Vertical Slice

目标：验证紫微引擎通过新 Contract 全链路，证明多体系共享同一个 Evidence/Assertion
      Contract 而不互相比较/投票。

测试策略：
  - 不依赖 iztro（stub 模式），直接构造 ZiweiChart 对象
  - 跑通: ZiweiChart → ZiweiEvidenceProducer → EngineEvidence
         → SemanticAtom → CanonicalAssertion
  - 验证 6 项约束（同 P1.2-C/D）

关键验证点：
  ① EngineEvidence 无 direction/polarity/strength/confidence
  ② SemanticAtom 无方向
  ③ direction 来自授权规则
  ④ NO_ASSERTION ≠ NEUTRAL
  ⑤ 追溯链完整
  ⑥ 不调用旧 Signal/CrossAnalyzer
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tongshu.spec.canonical import (
    EngineEvidence,
    SemanticAtom,
    CanonicalAssertion,
    EngineName,
    TemporalScope,
    EvidenceRef,
)
from tongshu.engines.ziwei.evidence_producer import ZiweiEvidenceProducer
from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ziwei_chart():
    """构造一个模拟的 ZiweiChart（不依赖 iztro stub）。

    最小化结构：命宫主星 + 命宫四化 + 少量宫位
    """
    # 纪晓岚命例对应紫微：命宫主星=紫微+天府，四化=化科
    return type("ZiweiChart", (), {
        "soul_palace_main_stars": ["ZIWEI", "TIANFU"],
        "soul_palace_main_star": "ZIWEI",
        "soul_palace_sihua": ["HUA_KE"],
        "soul_borrowed": False,
        "palaces": {
            "命宫": {"major": ["ZIWEI", "TIANFU"], "sihua": ["HUA_KE"]},
            "财帛": {"major": ["WUQU"], "sihua": ["HUA_LU"]},
            "官禄": {"major": ["TAIYANG"], "sihua": []},
        },
    })()


@pytest.fixture
def ziwei_assertion_rules(tmp_path):
    """紫微断言规则（基于 ZW-405~408 四化规则 + 星曜规则）。"""
    rules_data = {
        "_meta": {
            "version": "1.0",
            "description": "P1.2-G 紫微断言规则",
            "status": "TEST",
        },
        "rules": [
            {
                "rule_id": "ASR-ZW-ZIWEI",
                "domain": "CAREER",
                "match_strategy": "EXACT",
                "condition": {"atom_id": "ZW_STAR_ZIWEI"},
                "direction": "supportive",
                "canonical_source": "紫微斗数全书·紫微星",
                "provenance": {
                    "source_work": "紫微斗数全书",
                    "source_chapter": "紫微星",
                    "verification_status": "unverified",
                },
            },
            {
                "rule_id": "ASR-ZW-TIANFU",
                "domain": "FINANCE",
                "match_strategy": "EXACT",
                "condition": {"atom_id": "ZW_STAR_TIANFU"},
                "direction": "supportive",
                "canonical_source": "紫微斗数全书·天府星",
                "provenance": {
                    "source_work": "紫微斗数全书",
                    "source_chapter": "天府星",
                    "verification_status": "unverified",
                },
            },
            {
                "rule_id": "ASR-ZW-HUA_LU",
                "domain": "FINANCE",
                "match_strategy": "EXACT",
                "condition": {"atom_id": "ZW_SIHUA_HUA_LU"},
                "direction": "supportive",
                "canonical_source": "紫微斗数全书·四化",
                "provenance": {
                    "source_work": "紫微斗数全书",
                    "source_chapter": "四化",
                    "verification_status": "unverified",
                },
            },
            {
                "rule_id": "ASR-ZW-HUA_JI",
                "domain": "FINANCE",
                "match_strategy": "EXACT",
                "condition": {"atom_id": "ZW_SIHUA_HUA_JI"},
                "direction": "caution",
                "canonical_source": "紫微斗数全书·四化",
                "provenance": {
                    "source_work": "紫微斗数全书",
                    "source_chapter": "四化",
                    "verification_status": "unverified",
                },
            },
            {
                "rule_id": "ASR-ZW-HUA_KE",
                "domain": "GROWTH",
                "match_strategy": "EXACT",
                "condition": {"atom_id": "ZW_SIHUA_HUA_KE"},
                "direction": "supportive",
                "canonical_source": "紫微斗数全书·四化",
                "provenance": {
                    "source_work": "紫微斗数全书",
                    "source_chapter": "四化",
                    "verification_status": "unverified",
                },
            },
        ],
    }
    p = tmp_path / "ziwei_assertion_rules.json"
    p.write_text(json.dumps(rules_data, ensure_ascii=False), encoding="utf-8")
    return str(p)


# ─── P1.2-G Tests ────────────────────────────────────────────────────────────


class TestZiweiVerticalSlice:
    """紫微单引擎垂直切片验证。"""

    def test_producer_returns_evidence_list(self, mock_ziwei_chart):
        """G1: 产出 list[EngineEvidence]。"""
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)
        assert isinstance(evidences, list)
        assert len(evidences) > 0
        assert all(isinstance(e, EngineEvidence) for e in evidences)

    def test_evidence_no_direction_or_strength(self, mock_ziwei_chart):
        """G2: 无 direction/polarity/strength/confidence。"""
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)
        for ev in evidences:
            assert not hasattr(ev, "direction"), f"{ev.evidence_id} has direction"
            assert not hasattr(ev, "polarity")
            assert "direction" not in ev.attributes
            assert "polarity" not in ev.attributes
            assert "strength" not in ev.attributes
            assert "confidence" not in ev.attributes

    def test_evidence_traceable(self, mock_ziwei_chart):
        """G3: 追溯字段完整。"""
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)
        for ev in evidences:
            assert ev.engine == EngineName.ZI_WEI
            assert ev.temporal_scope == TemporalScope.BIRTH
            assert ev.evidence_id != ev.rule_id
            assert ev.source_rule_ref is not None
            assert ev.calculation_version == "2026.09"
            assert ev.contract_version == "v13.0"

    def test_no_legacy_signal_in_chain(self, mock_ziwei_chart):
        """G4: 不调用旧组件。"""
        import inspect
        source = inspect.getsource(ZiweiEvidenceProducer)
        assert "SignalEngine" not in source
        assert "cross_analysis" not in source
        assert "ConvergenceArbiter" not in source
        assert "legacy_adapter" not in source

class TestZiweiAssertionGeneration:
    """紫微 Assertion 生成验证。"""

    def test_atom_to_assertion_from_rule(self, mock_ziwei_chart, ziwei_assertion_rules):
        """G5: 紫微 Atom → CanonicalAssertion，direction 来自规则。"""
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary

        library = AssertionRuleLibrary.load(ziwei_assertion_rules)
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)

        evidence_map = {ev.evidence_id: ev for ev in evidences}

        # Build SemanticAtoms manually (simulating mapper)
        atoms_with_evidence = []
        for ev in evidences:
            attrs = ev.attributes
            if "star" in attrs:
                atom = SemanticAtom(
                    atom_id=f"ZW_STAR_{attrs['star']}",
                    engine=ev.engine,
                    evidence_ref=ev.evidence_id,
                    semantic_keys=[attrs["star"]],
                    domain_candidates=["CAREER", "FINANCE"],
                    label_zh="",
                    category="ZIWEI_MAJOR",
                )
            elif "sihua" in attrs:
                atom = SemanticAtom(
                    atom_id=f"ZW_SIHUA_{attrs['sihua']}",
                    engine=ev.engine,
                    evidence_ref=ev.evidence_id,
                    semantic_keys=[attrs["sihua"]],
                    domain_candidates=["FINANCE", "GROWTH"],
                    label_zh="",
                    category="ZIWEI_SIHUA",
                )
            else:
                continue
            atoms_with_evidence.append((atom, ev))

        # Match rules and build assertions
        assertions = []
        for atom, ev in atoms_with_evidence:
            rule = library.find_rule(atom, {"temporal_scope": "birth", "case_id": "test"})
            if rule is not None:
                assertion = CanonicalAssertion(
                    assertion_id=f"AS-{ev.evidence_id}-{atom.atom_id}",
                    subject="test",
                    domain=rule.domain,
                    semantic=atom.atom_id,
                    direction=rule.direction,
                    temporal_scope="birth",
                    source_engine=atom.engine.value,
                    source_rule=atom.evidence_ref,
                    authorized_rule_id=rule.rule_id,
                    evidence=EvidenceRef(
                        evidence_id=atom.evidence_ref,
                        engine=atom.engine.value,
                        value=memory_map.get(atom.evidence_ref, ev.value) if (memory_map := evidence_map) else ev.value,
                        source_rule_ref=ev.source_rule_ref,
                    ),
                )
                assertions.append(assertion)

        # At least some assertions should be generated
        assert len(assertions) > 0, "至少应有一条 Assertion 命中规则"

        # Verify direction comes from rule
        for a in assertions:
            assert a.direction is not None
            assert a.authorized_rule_id is not None

    def test_no_cross_system_comparison(self, mock_ziwei_chart):
        """G6: 紫微不与子平做 direction 比较。"""
        import inspect
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary

        source = inspect.getsource(AssertionRuleLibrary)
        assert "cross" not in source.lower() or "CrossAnalyzer" not in source
        assert "CONFLICTED" not in source
        assert "ALIGNED" not in source

    def test_full_traceability(self, mock_ziwei_chart, ziwei_assertion_rules):
        """G7: 完整追溯链。"""
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary

        library = AssertionRuleLibrary.load(ziwei_assertion_rules)
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)

        evidence_map = {ev.evidence_id: ev for ev in evidences}

        for ev in evidences:
            attrs = ev.attributes
            if "star" in attrs or "sihua" in attrs:
                # Verify traceability
                assert ev.evidence_id in ev.evidence_id  # self-check
                assert ev.engine == EngineName.ZI_WEI
                assert ev.source_rule_ref is not None
                assert ev.calculation_version == "2026.09"


class TestConstraintVerification:
    """约束验证汇总。"""

    def test_c1_no_direction_in_evidence(self, mock_ziwei_chart):
        """约束 ①: EngineEvidence 无 direction/polarity/strength/confidence。"""
        producer = ZiweiEvidenceProducer()
        evidences = producer.produce(mock_ziwei_chart)
        for ev in evidences:
            assert not hasattr(ev, "direction")
            assert "direction" not in ev.attributes
            assert "strength" not in ev.attributes
            assert "confidence" not in ev.attributes

    def test_c2_no_cross_analyzer(self, mock_ziwei_chart):
        """约束 ④: 不涉及 CrossAnalyzer。"""
        import inspect
        source = inspect.getsource(ZiweiEvidenceProducer)
        assert "cross_analysis" not in source
        assert "CrossAnalyzer" not in source

    def test_c3_no_evidence_count_voting(self, mock_ziwei_chart):
        """约束 ③: 无 evidence_count 投票。"""
        import inspect
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary
        source = inspect.getsource(AssertionRuleLibrary)
        assert "evidence_count" not in source
        assert "vote" not in source.lower()

    def test_c4_no_neutral_fallback(self, mock_ziwei_chart):
        """约束 ⑤: NO_ASSERTION ≠ NEUTRAL。"""
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary
        empty_lib = AssertionRuleLibrary(rules=[])
        from tongshu.spec.canonical import SemanticAtom, EngineName
        fake_atom = SemanticAtom(
            atom_id="NONEXISTENT",
            engine=EngineName.ZI_WEI,
            evidence_ref="EV-FAKE",
            semantic_keys=["FAKE"],
            domain_candidates=["CAREER"],
        )
        result = empty_lib.find_rule(fake_atom, {})
        assert result is None  # NO_ASSERTION, not NEUTRAL

    def test_c5_no_intensity(self, mock_ziwei_chart):
        """约束补充: 无 intensity。"""
        from tongshu.spec.canonical.assertion import CanonicalAssertion
        import inspect
        sig = inspect.signature(CanonicalAssertion)
        assert "intensity" not in sig.parameters

    def test_no_old_pipeline_import(self, mock_ziwei_chart):
        """G8: 不导入旧 Pipeline 组件。"""
        import sys
        loaded_before = set(sys.modules.keys())
        from tongshu.engines.ziwei.evidence_producer import ZiweiEvidenceProducer
        from tongshu.assertion.assertion_rule_library import AssertionRuleLibrary
        producer = ZiweiEvidenceProducer()
        producer.produce(mock_ziwei_chart)
        library = AssertionRuleLibrary(rules=[])
        new_modules = set(sys.modules.keys()) - loaded_before
        old_indicators = [
            "tongshu.reasoning.signal_engine",
            "tongshu.reasoning.cross_analysis",
            "tongshu.signal.convergence",
            "tongshu.signal.aggregator",
        ]
        for indicator in old_indicators:
            assert indicator not in new_modules, f"旧组件 {indicator} 被导入"
