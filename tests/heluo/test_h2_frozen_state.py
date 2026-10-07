"""H2: FrozenHeluoState 集成测试

覆盖：FrozenHeluoState 构建、序列化、纪晓岚 Golden Case 全字段验证
原典依据：《河洛真数》起例卷（全部14条规则）
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.frozen_state import build_frozen_state, FrozenHeluoState
from tongshu.engines.heluo.evidence_producer import HeLuoEvidenceProducer


class TestFrozenStateGoldenCase(unittest.TestCase):
    """纪晓岚 Golden Case → FrozenHeluoState 全字段验证"""

    def setUp(self):
        self.canonical = HeluoCanonical()
        self.result = self.canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="zhong",
            birth_year=1724,
        )
        self.state = build_frozen_state(self.result)

    def test_numbers(self):
        self.assertEqual(self.state.tian_shu, 22)
        self.assertEqual(self.state.di_shu, 56)
        self.assertEqual(self.state.tian_reduced, 2)   # 坤
        self.assertEqual(self.state.di_reduced, 6)     # 乾

    def test_prenatal(self):
        self.assertEqual(self.state.prenatal_name, "地天泰")
        self.assertEqual(self.state.prenatal_upper, "坤")
        self.assertEqual(self.state.prenatal_lower, "乾")
        # 泰卦六爻：下乾(1,1,1) + 上坤(-1,-1,-1)
        self.assertEqual(self.state.prenatal_lines, (1, 1, 1, -1, -1, -1))

    def test_yuantang(self):
        self.assertEqual(self.state.yuan_tang, "六四")
        self.assertEqual(self.state.yuan_tang_index, 3)
        self.assertEqual(self.state.yuan_tang_nature, "阴")

    def test_postnatal(self):
        self.assertEqual(self.state.postnatal_name, "天雷无妄")
        self.assertEqual(self.state.postnatal_upper, "乾")
        self.assertEqual(self.state.postnatal_lower, "震")
        # 无妄：下震(1,-1,-1) + 上乾(1,1,1) = 元堂四爻变后互换
        self.assertEqual(self.state.postnatal_lines, (1, 1, 1, 1, -1, -1))

    def test_huagong(self):
        """纪晓岚 甲辰辛未丙戌甲午，月柱**辛未** → 月支「未」→ 化工卦离(火)。

        2026-10-07 三轮更正：本断言原写「生于丑月」，那是 `canonical` 拿
        **公历月份**硬凑月支的产物。月令以节气为界，本就该取月柱地支；
        甲辰辛未的月支是「未」不是「丑」。公历月近似映射已从源码删除。

        正体互体皆无离 → 纳音回退：甲辰纳音火，与离同气 → level=纳音，
        按 L576「终是浅薄，福寿减半」标 reduced；但四卦中既无离亦无坎，
        无化工相反。state 为 **WEAK**（浅薄·减半），非 NORMAL 亦非 UNRESOLVED——
        减半的化工若报 NORMAL（得位·有机气）即为高报，L576 明言「终是浅薄」。
        """
        self.assertEqual(self.state.hua_gong_state, "WEAK")
        self.assertIsNotNone(self.state.hua_gong_evidence)
        joined = chr(10).join(self.state.hua_gong_evidence)
        self.assertTrue(any("未" in e for e in self.state.hua_gong_evidence), joined)
        self.assertIn("纳音", joined)

    def test_dayun_count(self):
        """先天6爻 + 后天6爻 = 12段大运"""
        self.assertEqual(len(self.state.dayun_summary), 12)

    def test_liunian_count(self):
        """流年卦应覆盖多数年份（93-100间，取决于大运段边界）"""
        self.assertGreaterEqual(self.state.liunian_count, 90)
        self.assertLessEqual(self.state.liunian_count, 100)

    def test_to_dict_serializable(self):
        d = self.state.to_dict()
        self.assertIn("version", d)
        self.assertIn("numbers", d)
        self.assertIn("prenatal", d)
        self.assertIn("yuan_tang", d)
        self.assertIn("postnatal", d)
        self.assertIn("hua_gong", d)
        self.assertIn("timeline", d)


class TestEvidenceProducerH6H11(unittest.TestCase):
    """证据生产者包含 H6/H11 事实证据"""

    def setUp(self):
        self.producer = HeLuoEvidenceProducer()
        self.result = HeluoCanonical().calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male", birth_hour="午", era="zhong", birth_year=1724,
        )

    def test_evidence_count_includes_huagong(self):
        evidences = self.producer.produce(self.result)
        rule_ids = [e.rule_id for e in evidences]
        self.assertIn("HL_HUA_GONG", rule_ids)

    def test_evidence_no_value_judgment(self):
        """证据不含 direction/strength/confidence（V13 硬约束）"""
        for e in self.producer.produce(self.result):
            self.assertNotIn("direction", str(e.value))
            self.assertNotIn("confidence", str(e.value))

    def test_evidence_rule_ids_stable(self):
        """rule_id 稳定不变"""
        rule_ids = {e.rule_id for e in self.producer.produce(self.result)}
        expected = {
            "HL_TIAN_DI_SHU", "HL_PRENATAL_HEXAGRAM", "HL_YUANTANG",
            "HL_POSTNATAL_HEXAGRAM", "HL_HEXAGRAM_STRUCTURE", "HL_HUA_GONG",
        }
        self.assertTrue(expected.issubset(rule_ids))


class TestFrozenStateImmutability(unittest.TestCase):
    """FrozenHeluoState 不可变性验证"""

    def test_frozen_is_frozen(self):
        state = FrozenHeluoState(
            version="v2.0",
            calculation_policy={},
            tian_shu=22, di_shu=56,
            tian_reduced=2, di_reduced=6,
            prenatal_name="地天泰",
            prenatal_upper="坤", prenatal_lower="乾",
            prenatal_lines=(1, 1, 1, -1, -1, -1),
            yuan_tang="六四", yuan_tang_index=3, yuan_tang_nature="阴",
            postnatal_name="天雷无妄",
            postnatal_upper="乾", postnatal_lower="震",
            postnatal_lines=(1, 1, 1, 1, -1, -1),
            seasonal_hexagram=None,
            qi_phase=None,
            hua_gong_state=None,
            hua_gong_evidence=None,
            dayun_summary=[],
            liunian_count=100,
            birth_year=1724,
            gender="male",
            birth_hour="午",
            birth_date="1724-01-01",
        )
        with self.assertRaises(Exception):
            state.prenatal_name = "修改失败"  # frozen=True 应抛出


if __name__ == "__main__":
    unittest.main()
