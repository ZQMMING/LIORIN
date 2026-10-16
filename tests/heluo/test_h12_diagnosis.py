"""H12: Diagnosis Rule Graph 测试

覆盖：RuleNode注册表、CanonicalAssertion构建、EvidenceCoverage、Judgment授权
原典依据：V13 §三/§四 合约 + 《河洛真数》起例卷
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.frozen_state import build_frozen_state
from tongshu.engines.heluo.evidence_producer import HeLuoEvidenceProducer
from tongshu.engines.heluo.diagnosis_rule_graph import (
    build_diagnosis_graph,
    HELUO_RULES,
    HUAGONG_DIRECTION,
    DiagnosisResult,
)
from tongshu.spec.canonical import AssertionDirection, EvidenceRef
from tongshu.engines.heluo.hua_gong import HuaGongState


class TestRuleNodeRegistry(unittest.TestCase):
    """规则节点注册表验证"""

    def test_rule_count(self):
        self.assertGreaterEqual(len(HELUO_RULES), 8)

    def test_all_authorized(self):
        for rule_id, node in HELUO_RULES.items():
            self.assertTrue(node.is_authorized, f"{rule_id} must be authorized")
            self.assertGreater(node.confidence, 0)

    def test_source_refs_exist(self):
        """所有规则节点有原典出处"""
        for node in HELUO_RULES.values():
            self.assertTrue(len(node.source_ref) > 3, f"{node.rule_id} missing source ref")

    def test_huagong_directions(self):
        """化工状态→方向映射正确"""
        self.assertEqual(HUAGONG_DIRECTION[HuaGongState.NORMAL.value], AssertionDirection.SUPPORTIVE)
        self.assertEqual(HUAGONG_DIRECTION[HuaGongState.RESCUED.value], AssertionDirection.SUPPORTIVE)
        self.assertEqual(HUAGONG_DIRECTION[HuaGongState.REVERSE.value], AssertionDirection.CAUTION)
        self.assertEqual(HUAGONG_DIRECTION[HuaGongState.UNRESOLVED.value], AssertionDirection.NEUTRAL)


class TestDiagnosisGraphIntegration(unittest.TestCase):
    """完整链路集成测试（Golden Case）"""

    def setUp(self):
        self.canonical = HeluoCanonical()
        self.result = self.canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male", birth_hour="午", era="zhong", birth_year=1724,
        )
        self.state = build_frozen_state(self.result)
        self.evidences = HeLuoEvidenceProducer().produce(self.result)
        # 生成少量 EVENT_SIGNAL
        self.signals = [
            {"system": "HELUO", "rule_id": "HL-YN-1725", "direction": "POSITIVE",
             "confidence": 0.7, "hexagram": "雷天大壮", "time_scope": {"year": 1725},
             "evidence": ["卦辞：无妄，元吉"]},
            {"system": "HELUO", "rule_id": "HL-YN-1726", "direction": "NEGATIVE",
             "confidence": 0.5, "hexagram": "天风姤", "time_scope": {"year": 1726},
             "evidence": ["卦辞：有夷于左膝"]},
        ]

    def test_graph_builds_assertions(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        self.assertIsInstance(result, DiagnosisResult)
        self.assertGreater(len(result.assertions), 0)

    def test_assertions_have_required_fields(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        for a in result.assertions:
            self.assertIsInstance(a.assertion_id, str)
            self.assertIn(a.domain, {"FAMILY", "CAREER", "DAILY", "LIFE_EVENT"})
            self.assertIsInstance(a.direction, AssertionDirection)
            self.assertIsInstance(a.evidence, EvidenceRef)

    def test_huagong_assertion_present(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        huagong_assertions = [a for a in result.assertions if "HUA_GONG" in a.assertion_id]
        self.assertGreaterEqual(len(huagong_assertions), 1)
        # 至少有一个化工断言，方向正确
        for a in huagong_assertions:
            self.assertEqual(a.direction, AssertionDirection.NEUTRAL)

    def test_signal_assertions_present(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        signal_assertions = [a for a in result.assertions if "HL-YN" in a.assertion_id]
        self.assertEqual(len(signal_assertions), 2)
        # POSITIVE → SUPPORTIVE
        pos_assertions = [a for a in signal_assertions if a.direction == AssertionDirection.SUPPORTIVE]
        neg_assertions = [a for a in signal_assertions if a.direction == AssertionDirection.CAUTION]
        self.assertEqual(len(pos_assertions), 1)
        self.assertEqual(len(neg_assertions), 1)

    def test_coverage_structure(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        self.assertIsNotNone(result.coverage)
        self.assertGreater(result.coverage.evidence_count, 0)
        self.assertIn("HELUO", result.coverage.source_engines)

    def test_judgment_authorized(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        self.assertIsNotNone(result.judgment)
        self.assertEqual(result.judgment.authorized_by, "V13_河洛诊断规则集")
        self.assertGreater(len(result.judgment.supporting_assertions), 0)

    def test_to_dict_serializable(self):
        result = build_diagnosis_graph(self.evidences, self.signals, self.state)
        d = result.to_dict()
        self.assertIn("assertions", d)
        self.assertIn("coverage", d)
        self.assertIn("judgment", d)
        self.assertIsInstance(d["assertions"], list)


class TestDiagnosisGraphNoSignals(unittest.TestCase):
    """无 EVENT_SIGNAL 时的降级行为"""

    def test_graceful_degradation(self):
        canonical = HeluoCanonical()
        result = canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male", birth_hour="午", era="zhong", birth_year=1724,
        )
        evidences = HeLuoEvidenceProducer().produce(result)
        graph_result = build_diagnosis_graph(evidences, [], result)
        # 至少有基础证据断言，不崩溃
        self.assertGreater(len(graph_result.assertions), 0)
        self.assertIsNotNone(graph_result.coverage)


if __name__ == "__main__":
    unittest.main()
