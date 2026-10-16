# -*- coding: utf-8 -*-
"""Z14: 同盘异法验收测试。

验证（Z17 两派收敛）：
  - 同一张 FrozenZiweiChart 被两派独立消费（南派 SANHE + 北派 QINTIAN）
  - 各派证据 method_id / rule_id 严格隔离
  - 不同派 rule_id 无交集
  - 每条证据可追溯（method_id + rule_id + facts + trace）
  - 不产生最终判断（无 direction/polarity/strength/confidence）
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine, FrozenZiweiChart
from tongshu.engines.ziwei_method_profile import MethodId
from tongshu.engines.ziwei.z14.evidence_collector import (
    MultiMethodEvidenceCollector,
    IsolationVerifier,
    ZiweiEvidenceRecord,
)


# ── 真实命盘案例 ──────────────────────────────────────────────────────────

REAL_CASES = [
    ((2000, 1, 1), 12, 'male',   '庚辰年男'),
    ((1990, 5, 15), 10, 'female','庚午年女'),
    ((1984, 10, 15), 8, 'female','甲子年闰十月女'),
]


class TestSameChartTwoMethods(unittest.TestCase):
    """Z14-A: 同一张盘 → 两派独立证据收集（Z17 收敛）。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()
        cls.chart = cls.engine.full_chart((2000, 1, 1), 12, 'male')

    def test_all_two_methods_produce_evidence(self):
        """两派均产出证据（QINTIAN 为 PARTIAL，允许空）。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        # FULL/SCAFFOLD 方法必须非空，DRAFT 允许空
        from tongshu.engines.ziwei.z14.evidence_collector import IsolationVerifier
        checks = IsolationVerifier.verify_non_empty_for_implementation(evidence_map)
        failed = [k for k, v in checks.items() if not v]
        self.assertEqual(failed, [],
            f"已实现方法应产出非空证据: {failed}")

    def test_same_chart_used_for_all(self):
        """所有派别使用同一个 FrozenZiweiChart 实例。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        self.assertIs(collector.chart, self.chart)
        self.assertIsInstance(collector.chart, FrozenZiweiChart)

    def test_different_methods_different_rule_ids(self):
        """不同派别的 rule_id 前缀不同，无交集。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        _RULE_PREFIX = {MethodId.SANHE: "SANHE", MethodId.QINTIAN: "QTN"}
        all_ids: dict[str, set[str]] = {}
        for mid, records in evidence_map.items():
            ids = {r.rule_id for r in records}
            all_ids[mid.value] = ids
            # 每条 rule_id 以对应方法前缀开头（QINTIAN → QTN-）
            prefix = _RULE_PREFIX.get(mid, mid.value.upper())
            for rid in ids:
                self.assertTrue(rid.startswith(prefix),
                    f"rule_id '{rid}' 应以 '{prefix}-' 开头")

        # 不同派前缀的 rule_id 集合应无交集
        methods = list(all_ids.keys())
        for i in range(len(methods)):
            for j in range(i + 1, len(methods)):
                intersection = all_ids[methods[i]] & all_ids[methods[j]]
                self.assertEqual(intersection, set(),
                    f"{methods[i]} 与 {methods[j]} rule_id 应有交集")

    def test_evidence_count_differs_by_method(self):
        """不同派别证据数量不同（证明各自独立计算）。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        counts = {mid.value: len(recs)
                  for mid, recs in evidence_map.items()}
        # 至少有两派证据数量不同（证明不是同一套规则）
        unique_counts = set(counts.values())
        self.assertGreaterEqual(len(unique_counts), 2,
            "至少应有两派产生不同数量的证据")


class TestIsolation(unittest.TestCase):
    """Z14-B: 派别隔离验证。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()
        cls.chart = cls.engine.full_chart((2000, 1, 1), 12, 'male')

    def test_no_cross_method_evidence_reading(self):
        """南派不读取北派（Qintian）的证据。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        # 检查 Sanhe 证据不含 QTN- 前缀
        sanhe_ids = {r.rule_id for r in evidence_map[MethodId.SANHE]}
        for rid in sanhe_ids:
            self.assertFalse(rid.startswith('QTN-'),
                f"Sanhe 证据不应含 QTN- 前缀: {rid}")

        # 检查 Qintian 证据不含 SANHE- 前缀
        qtn_ids = {r.rule_id for r in evidence_map[MethodId.QINTIAN]}
        for rid in qtn_ids:
            self.assertFalse(rid.startswith('SANHE-'),
                f"Qintian 证据不应含 SANHE- 前缀: {rid}")

    def test_isolation_verifier_passes(self):
        """IsolationVerifier 全部检查通过。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()
        checks = IsolationVerifier.verify_no_cross_contamination(evidence_map)

        failed = [k for k, v in checks.items() if not v]
        self.assertEqual(failed, [],
            f"隔离检查失败: {failed}")

    def test_traceability_verifier_passes(self):
        """IsolationVerifier 可追溯性检查全部通过。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()
        checks = IsolationVerifier.verify_traceability(evidence_map)

        failed = [k for k, v in checks.items() if not v]
        self.assertEqual(failed, [],
            f"可追溯性检查失败: {failed}")

    def test_implementation_identity(self):
        """F3: 每条证据的 implementation 状态与派别一致。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()
        checks = IsolationVerifier.verify_implementation_identity(evidence_map)

        failed = [k for k, v in checks.items() if not v]
        self.assertEqual(failed, [],
            f"implementation 身份检查失败: {failed}")

    def test_non_empty_for_implementation(self):
        """F3b: 已实现方法（FULL/SCAFFOLD）必须产生非空证据。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()
        checks = IsolationVerifier.verify_non_empty_for_implementation(evidence_map)

        failed = [k for k, v in checks.items() if not v]
        self.assertEqual(failed, [],
            f"非空证据检查失败: {failed}")


class TestEvidenceQuality(unittest.TestCase):
    """Z14-C: 证据质量检查。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()
        cls.chart = cls.engine.full_chart((2000, 1, 1), 12, 'male')

    def test_no_diagnostic_fields_in_evidence(self):
        """证据中不含诊断语义值（INCREASE/DECLINE/STABLE/POSITIVE/NEGATIVE/NEUTRAL）。

        注意：飞化 facts 中的 'direction' 是结构性描述（'in'/'out'/'self'），
        不是 Signal 层诊断方向（'INCREASE'/'DECLINE'/'STABLE'），不算违规。
        """
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        DIAGNOSTIC_VALUES = {'INCREASE', 'DECLINE', 'STABLE',
                             'POSITIVE', 'NEGATIVE', 'NEUTRAL'}
        for mid, records in evidence_map.items():
            for r in records:
                for v in r.facts.values():
                    if isinstance(v, str) and v in DIAGNOSTIC_VALUES:
                        self.fail(
                            f"{mid.value} 证据含诊断值 '{v}': {r.facts}"
                        )

    def test_all_evidence_have_verification_status(self):
        """每条证据都有 verification 状态。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        VALID_STATUSES = {'canonical', 'candidate', 'unverified'}
        for mid, records in evidence_map.items():
            for r in records:
                self.assertIn(r.verification, VALID_STATUSES,
                    f"{mid.value} 证据 verification 状态非法: {r.verification}")

    def test_all_evidence_have_trace(self):
        """每条证据都有 trace 路径。"""
        collector = MultiMethodEvidenceCollector(self.chart)
        evidence_map = collector.collect()

        for mid, records in evidence_map.items():
            for r in records:
                self.assertGreaterEqual(len(r.trace), 1,
                    f"{mid.value} 证据 trace 不应为空")

    def test_evidence_record_is_immutable(self):
        """ZiweiEvidenceRecord 是不可变的（frozen dataclass）。"""
        from tongshu.engines.ziwei.z14.evidence_collector import ZiweiEvidenceRecord
        import dataclasses

        self.assertTrue(dataclasses.is_dataclass(ZiweiEvidenceRecord))
        self.assertTrue(ZiweiEvidenceRecord.__dataclass_params__.frozen)


class TestMultipleCharts(unittest.TestCase):
    """Z14-D: 多盘验证 — 不同命盘产生不同证据。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_different_charts_different_evidence(self):
        """三张不同命盘，同一流派证据内容不同。"""
        charts = [
            self.engine.full_chart((2000, 1, 1), 12, 'male'),
            self.engine.full_chart((1990, 5, 15), 10, 'female'),
            self.engine.full_chart((1984, 10, 15), 8, 'female'),
        ]
        collector = MultiMethodEvidenceCollector(charts[0])
        evidence_map = collector.collect()

        # 用 rule_id 集合 + facts 内容作为指纹
        fingerprints = []
        for chart in charts:
            c = MultiMethodEvidenceCollector(chart)
            em = c.collect()
            # 取 Sanhe 的 rule_id 集合 + 证据总数
            fp = (
                frozenset(r.rule_id for r in em[MethodId.SANHE]),
                len(em[MethodId.SANHE]),
                len(em[MethodId.QINTIAN]),
            )
            fingerprints.append(fp)

        self.assertNotEqual(fingerprints[0], fingerprints[1])
        self.assertNotEqual(fingerprints[1], fingerprints[2])
        self.assertNotEqual(fingerprints[0], fingerprints[2])

    def test_same_chart_same_evidence_deterministic(self):
        """同一张盘，两次收集结果相同（确定性）。"""
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')

        c1 = MultiMethodEvidenceCollector(chart)
        em1 = c1.collect()

        c2 = MultiMethodEvidenceCollector(chart)
        em2 = c2.collect()

        for mid in MethodId:
            ids1 = {r.rule_id for r in em1[mid]}
            ids2 = {r.rule_id for r in em2[mid]}
            self.assertEqual(ids1, ids2,
                f"{mid.value} 证据 rule_id 应确定")




class TestSanheIntegrity(unittest.TestCase):
    """S14-SANHE-INTEGRITY: SanheRuleGraph 真实匹配验证。"""

    @classmethod
    def setUpClass(cls):
        cls.engine = ZiweiEngine()

    def test_sanhe_patterns_actually_match(self):
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        graph = SanheRuleGraph()
        result = graph.match_all(chart)
        patterns = [r for r in result.matched_rules
                    if r.rule_spec.rule_type.value == "pattern"]
        self.assertGreater(len(patterns), 0,
            "Sanhe pattern matcher 应产出非空证据（三方四正）")

    def test_sanhe_natal_sihua_from_birth_year(self):
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph
        from tongshu.engines.ziwei_engine import GAN_SIHUA
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        graph = SanheRuleGraph()
        result = graph.match_all(chart)
        sihua_records = [r for r in result.matched_rules
                         if r.rule_spec.rule_type.value == "sihua"
                         and "SIHUA" in r.rule_spec.rule_id]
        self.assertGreater(len(sihua_records), 0)
        for r in sihua_records:
            facts = r.facts
            self.assertEqual(facts["stem"], "庚")
            expected = GAN_SIHUA['庚']
            self.assertEqual(facts["lu_star"], expected[0])
            self.assertEqual(facts["quan_star"], expected[1])
            self.assertEqual(facts["ke_star"], expected[2])
            self.assertEqual(facts["ji_star"], expected[3])

    def test_sanhe_sihua_differs_from_ming_stem(self):
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        ming_stem = chart.palaces["命宫"]["stem"]
        self.assertNotEqual(ming_stem, "庚")
        graph = SanheRuleGraph()
        result = graph.match_all(chart)
        sihua_records = [r for r in result.matched_rules
                         if r.rule_spec.rule_type.value == "sihua"]
        self.assertGreater(len(sihua_records), 0)
        first = sihua_records[0]
        sihua_stars = {first.facts.get("lu_star"), first.facts.get("quan_star"),
                       first.facts.get("ke_star"), first.facts.get("ji_star")}
        jia_sihua = {"廉贞", "破军", "武曲", "太阳"}
        geng_sihua = {"太阳", "武曲", "太阴", "天同"}
        self.assertNotEqual(sihua_stars, jia_sihua,
            "sihua 不应使用命宫宫干(甲)")
        self.assertEqual(sihua_stars, geng_sihua,
            f"sihua 应使用庚年四化 {geng_sihua}")

    def test_sanhe_full_impl_consistent(self):
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph
        chart = self.engine.full_chart((2000, 1, 1), 12, 'male')
        graph = SanheRuleGraph()
        self.assertEqual(graph.implementation_status, "FULL")
        result = graph.match_all(chart)
        self.assertGreater(len(result.matched_rules), 0)

if __name__ == "__main__":
    unittest.main()
