"""
H7 元气证据层测试（D-022）

原典依据（起例卷上·元气化工有无论）：
「元气化工二者最重，兼有之，若本数又吉，必功名富贵福寿人也。」
—— 元气此前只进 frozen_state，未进 evidence/诊断断言，属覆盖缺口。

验证：
1. 生产证据含 HL_YUAN_QI（state/scope/人元气）；
2. 化工证据带 D-019 三层判据字段（scope/weak/tu_wang）；
3. 诊断规则图把元气断为正/负方向，而非恒 NEUTRAL。
"""
from __future__ import annotations

import unittest

from tongshu.engines.heluo.canonical import heluo_calculate
from tongshu.engines.heluo.diagnosis_rule_graph import (
    HELUO_RULES,
    YUANQI_DIRECTION,
    build_diagnosis_graph,
)
from tongshu.engines.heluo.evidence_producer import HeLuoEvidenceProducer
from tongshu.spec.canonical import (
    AssertionDirection,
    EngineEvidence,
    EngineName,
    TemporalScope,
)

# 壬子 辛亥 壬辰 丙午（案例1，元气正体）
BAZI = ("壬子", "辛亥", "壬辰", "丙午")


class TestYuanQiEvidence(unittest.TestCase):
    def setUp(self) -> None:
        self.result = heluo_calculate(BAZI, "male", "午", "zhong")
        self.evidences = HeLuoEvidenceProducer().produce(self.result)

    def test_evidence_contains_yuan_qi(self) -> None:
        rule_ids = [e.rule_id for e in self.evidences]
        self.assertIn("HL_YUAN_QI", rule_ids)
        ev = next(e for e in self.evidences if e.rule_id == "HL_YUAN_QI")
        self.assertEqual(ev.value, self.result.yuan_qi.state.value)
        self.assertEqual(ev.attributes["scope"], self.result.yuan_qi.scope)
        self.assertEqual(
            ev.attributes["ren_yuan_element"], self.result.yuan_qi.ren_yuan_element
        )
        self.assertEqual(
            list(ev.attributes["ren_yuan_qi"]), list(self.result.yuan_qi.ren_yuan_qi)
        )

    def test_hua_gong_evidence_carries_scope(self) -> None:
        ev = next(e for e in self.evidences if e.rule_id == "HL_HUA_GONG")
        self.assertIn("scope", ev.attributes)
        self.assertEqual(ev.attributes["scope"], self.result.hua_gong.scope)
        self.assertEqual(ev.attributes["weak"], self.result.hua_gong.weak)
        self.assertEqual(ev.attributes["tu_wang"], self.result.hua_gong.tu_wang)

    def test_yuan_qi_rule_authorized(self) -> None:
        node = HELUO_RULES.get("HL_YUAN_QI")
        self.assertIsNotNone(node)
        self.assertTrue(node.is_authorized)
        self.assertIn("元气化工有无论", node.source_ref)

    def test_yuan_qi_assertion_direction(self) -> None:
        res = build_diagnosis_graph(self.evidences, [], subject="t")
        ast = next(
            a for a in res.assertions if a.assertion_id == "HE_LUO_HL_YUAN_QI"
        )
        self.assertEqual(
            ast.direction,
            YUANQI_DIRECTION[self.result.yuan_qi.state.value],
        )
        self.assertEqual(ast.domain, "FAMILY")

    def test_reverse_and_unresolved_directions(self) -> None:
        def _ev(value: str) -> EngineEvidence:
            return EngineEvidence(
                evidence_id=f"TEST-YUANQI-{value}",
                engine=EngineName.HE_LUO,
                rule_id="HL_YUAN_QI",
                value=value,
                temporal_scope=TemporalScope.BIRTH,
                attributes={},
                source_rule_ref="data/rules/heluo_yuan_qi.json",
                source_field="yuan_qi",
                calculation_version="2026.09",
                contract_version="v13.0",
            )

        reverse = build_diagnosis_graph([_ev("REVERSE")], [], subject="t")
        self.assertEqual(reverse.assertions[0].direction, AssertionDirection.CAUTION)
        unresolved = build_diagnosis_graph([_ev("UNRESOLVED")], [], subject="t")
        self.assertEqual(
            unresolved.assertions[0].direction, AssertionDirection.NEUTRAL
        )


if __name__ == "__main__":
    unittest.main()
