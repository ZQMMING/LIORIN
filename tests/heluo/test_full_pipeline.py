"""H0-H14 河洛理数完整链路测试

覆盖所有冻结模块的端到端验证：
  八字输入 → 天数地数 → 先天卦 → 元堂 → 后天卦 → 大运/流年/流月/流日
  → 化工 → 节候卦 → FrozenHeluoState → EngineEvidence → DiagnosisRuleGraph

原典依据：《河洛真数》续修四库全书本 + 三才发秘 + 中华典籍网
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.canonical import HeluoCanonical
from heluo_engine.engines.heluo.frozen_state import build_frozen_state, FrozenHeluoState
from heluo_engine.engines.heluo.evidence_producer import HeLuoEvidenceProducer
from heluo_engine.engines.heluo.diagnosis_rule_graph import build_diagnosis_graph
from heluo_engine.engines.heluo.jiehhou import (
    JIEHOU_GUA_NAME,
    SOLAR_TERMS, JIEHOU_GUA, get_seasonal_hexagram, get_qi_phase,
)
from heluo_engine.engines.heluo.hua_gong import compute_huagong, HuaGongState
from heluo_engine.engines.heluo.numbers import (
    STEM_VALUES, BRANCH_VALUES, normalize_tian_shu, normalize_di_shu,
    TRIGRAM_LINES, SIXTY_FOUR_HEXAGRAMS,
)
from heluo_engine.spec.canonical import EngineEvidence, AssertionDirection


# ═══════════════════════════════════════════════════════════════
# Golden Cases（原典可验证案例）
# ═══════════════════════════════════════════════════════════════

JIXIAOLAN_BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]
JIXIAOLAN_HOURLY = "午"
JIXIAOLAN_GENDER = "male"
JIXIAOLAN_ERA = "zhong"
JIXIAOLAN_YEAR = 1724

CASE2_BAZI = [("癸", "巳"), ("壬", "戌"), ("己", "巳"), ("甲", "戌")]
CASE2_HOURLY = "戌"
CASE2_GENDER = "male"
CASE2_ERA = "zhong"
CASE2_YEAR = 2013


class TestFullPipelineGoldenCases(unittest.TestCase):
    """完整链路：八字 → FrozenHeluoState → Evidence → Diagnosis"""

    def _run_full_pipeline(self, bazi, gender, hour, era, year):
        c = HeluoCanonical()
        result = c.calculate(
            bazi=bazi, gender=gender, birth_hour=hour,
            era=era, birth_year=year,
        )
        state = build_frozen_state(result)
        evidences = HeLuoEvidenceProducer().produce(result)
        return result, state, evidences

    def test_jixiaolan_full_chain(self):
        """纪晓岚：八字 → 先天 → 元堂 → 后天 → State → Evidence"""
        result, state, evidences = self._run_full_pipeline(
            JIXIAOLAN_BAZI, JIXIAOLAN_GENDER, JIXIAOLAN_HOURLY,
            JIXIAOLAN_ERA, JIXIAOLAN_YEAR,
        )
        # 先天卦
        self.assertEqual(result.prenatal.hexagram_name, "地天泰")
        # 元堂
        self.assertEqual(result.yuantang.yuantang, "六四")
        self.assertEqual(result.yuantang.yuantang_index, 3)
        # 后天卦
        self.assertEqual(result.postnatal.hexagram_name, "天雷无妄")
        # FrozenState
        self.assertEqual(state.prenatal_name, "地天泰")
        self.assertEqual(state.postnatal_name, "天雷无妄")
        self.assertEqual(state.yuan_tang, "六四")
        self.assertEqual(state.yuan_tang_index, 3)
        # Evidence 完整性
        rule_ids = [e.rule_id for e in evidences]
        self.assertIn("HL_TIAN_DI_SHU", rule_ids)
        self.assertIn("HL_PRENATAL_HEXAGRAM", rule_ids)
        self.assertIn("HL_YUANTANG", rule_ids)
        self.assertIn("HL_POSTNATAL_HEXAGRAM", rule_ids)
        self.assertIn("HL_HUA_GONG", rule_ids)
        # 所有证据是纯事实（无 direction/confidence）
        for e in evidences:
            val_str = str(e.value)
            self.assertNotIn("POSITIVE", val_str)
            self.assertNotIn("NEGATIVE", val_str)
            self.assertNotIn("confidence", val_str.lower())

    def test_case2_full_chain(self):
        """案例二（权威SO玄奥）：癸巳年壬戌月己巳日甲戌时戌时男"""
        result, state, evidences = self._run_full_pipeline(
            CASE2_BAZI, CASE2_GENDER, CASE2_HOURLY,
            CASE2_ERA, CASE2_YEAR,
        )
        # 先天地
        self.assertIsNotNone(result.prenatal.hexagram_name)
        self.assertIsNotNone(result.postnatal.hexagram_name)
        # 元堂
        self.assertIsInstance(state.yuan_tang_index, int)
        self.assertIn(state.yuan_tang_index, range(6))
        # 大运段数
        self.assertGreaterEqual(len(state.dayun_summary), 10)

    def test_frozen_state_is_immutable(self):
        """FrozenHeluoState 不可变验证"""
        result, state, _ = self._run_full_pipeline(
            JIXIAOLAN_BAZI, JIXIAOLAN_GENDER, JIXIAOLAN_HOURLY,
            JIXIAOLAN_ERA, JIXIAOLAN_YEAR,
        )
        self.assertIsInstance(state, FrozenHeluoState)
        with self.assertRaises(Exception):
            state.prenatal_name = "修改失败"

    def test_to_dict_serializable(self):
        """FrozenState 可序列化为 JSON"""
        result, state, _ = self._run_full_pipeline(
            JIXIAOLAN_BAZI, JIXIAOLAN_GENDER, JIXIAOLAN_HOURLY,
            JIXIAOLAN_ERA, JIXIAOLAN_YEAR,
        )
        d = state.to_dict()
        self.assertIn("version", d)
        self.assertIn("numbers", d)
        self.assertIn("prenatal", d)
        self.assertIn("yuan_tang", d)
        self.assertIn("postnatal", d)
        self.assertIn("hua_gong", d)
        self.assertIn("timeline", d)
        # 所有字段有值
        self.assertIsNotNone(d["numbers"]["tian_shu"])
        self.assertIsNotNone(d["prenatal"]["name"])
        self.assertIsNotNone(d["yuan_tang"]["name"])

    def test_diagnosis_graph_builds(self):
        """诊断规则图构建完整"""
        result, state, evidences = self._run_full_pipeline(
            JIXIAOLAN_BAZI, JIXIAOLAN_GENDER, JIXIAOLAN_HOURLY,
            JIXIAOLAN_ERA, JIXIAOLAN_YEAR,
        )
        graph_result = build_diagnosis_graph(evidences, [], state)
        self.assertGreater(len(graph_result.assertions), 0)
        self.assertIsNotNone(graph_result.coverage)
        # 至少应有基础断言
        domains = {a.domain for a in graph_result.assertions}
        self.assertGreaterEqual(len(domains), 2)


class TestEndToEndDeterminism(unittest.TestCase):
    """确定性验证：相同输入必须产生相同输出"""

    def test_same_input_same_output(self):
        c = HeluoCanonical()
        r1 = c.calculate(JIXIAOLAN_BAZI, "male", "午", "zhong", 1724)
        r2 = c.calculate(JIXIAOLAN_BAZI, "male", "午", "zhong", 1724)
        self.assertEqual(r1.prenatal.hexagram_name, r2.prenatal.hexagram_name)
        self.assertEqual(r1.yuantang.yuantang, r2.yuantang.yuantang)
        self.assertEqual(r1.postnatal.hexagram_name, r2.postnatal.hexagram_name)
        self.assertEqual(r1.numbers.tian_shu, r2.numbers.tian_shu)
        self.assertEqual(r1.numbers.di_shu, r2.numbers.di_shu)

    def test_different_gender_different_result(self):
        c = HeluoCanonical()
        male = c.calculate(JIXIAOLAN_BAZI, "male", "午", "zhong", 1724)
        female = c.calculate(JIXIAOLAN_BAZI, "female", "午", "zhong", 1724)
        # 先天卦不同（阳年男天数在上，阳年女地数在上）
        self.assertNotEqual(male.prenatal.hexagram_name, female.prenatal.hexagram_name)


class TestEdgeCases(unittest.TestCase):
    """边界条件测试"""

    def test_invalid_bazi_length_raises(self):
        c = HeluoCanonical()
        with self.assertRaises(ValueError):
            c.calculate([("甲", "辰"), ("辛", "未")], "male", "子", "zhong", 1990)

    def test_invalid_gender_raises(self):
        c = HeluoCanonical()
        with self.assertRaises(ValueError):
            c.calculate(JIXIAOLAN_BAZI, "unknown", "午", "zhong", 1724)

    def test_invalid_hour_raises(self):
        c = HeluoCanonical()
        with self.assertRaises(ValueError):
            c.calculate(JIXIAOLAN_BAZI, "male", "丑时", "zhong", 1724)

    def test_zero_tian_di_returns_five(self):
        """天数=0 或 地数=0 归一化结果合理"""
        self.assertEqual(normalize_tian_shu(0), 5)  # 原 Bug 修复
        self.assertEqual(normalize_di_shu(0), 3)

    def test_all_stems_have_values(self):
        for s in "甲乙丙丁戊己庚辛壬癸":
            self.assertIn(s, STEM_VALUES)
            v = STEM_VALUES[s]
            self.assertTrue(1 <= v <= 9, f"{s}={v} 超出 1-9")

    def test_all_branches_have_values(self):
        for b in "子丑寅卯辰巳午未申酉戌亥":
            self.assertIn(b, BRANCH_VALUES)
            vals = BRANCH_VALUES[b]
            self.assertEqual(len(vals), 2)
            # 河图生成数：(奇, 偶) 或 (偶, 奇)，和为 7/13/15
            self.assertEqual(vals[0] + vals[1], {
                "子": 7, "丑": 15, "寅": 11, "卯": 11,
                "辰": 15, "巳": 9, "午": 9, "未": 15,
                "申": 13, "酉": 13, "戌": 15, "亥": 7,
            }[b])

    def test_64_hexagram_names_all_resolvable(self):
        """全部64卦可通过上下卦名查找"""
        from heluo_engine.engines.heluo.numbers import get_hexagram_name
        trigrams = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        for upper in trigrams:
            for lower in trigrams:
                name = get_hexagram_name(upper, lower)
                self.assertIn(name, SIXTY_FOUR_HEXAGRAMS.values())

    def test_six_lines_all_hexagrams_valid(self):
        """所有六爻表示有效（全为 1 或 -1）"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        trigrams = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        for upper in trigrams[:4]:  # 抽查
            for lower in trigrams[:4]:
                lines = build_six_lines(upper, lower)
                self.assertEqual(len(lines), 6)
                self.assertTrue(all(l in (1, -1) for l in lines))


class TestHuaGongEndToEnd(unittest.TestCase):
    """化工端到端验证"""

    def test_normal_state_detection(self):
        """化工得位 → NORMAL"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertEqual(r.state, HuaGongState.NORMAL)
        self.assertTrue(r.has_huagong)
        self.assertFalse(r.has_opposite)

    def test_rescued_state_detection(self):
        """化工有反卦 → 按 L585–594 五行关系实算，不得一律判吉。

        原典 L582「却又有相生者，则吉。但忌克制，尤凶。」
        2026-10-07 两轮修：旧实现无条件判 RESCUED（下游映射为吉），
        且反卦表用的是先天对宫（震↔巽/兑↔艮），与原典「化工相反图」
        L585–594 的四季对宫（震↔兑）不符。两轮一并改回后，
        四组相反两两互为克制，本轴判 KEZHI。
        """
        from heluo_engine.engines.heluo.hua_gong import HUAGONG_FAN_GUA
        r = compute_huagong("乾", "兑", HUAGONG_FAN_GUA["兑"], "乾", "申")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)

    def test_kezhi_when_opposite_keeps_huagong(self):
        """化工有反卦但五行**相克** → KEZHI（原典 L582「忌克制，尤凶」）。"""
        r = compute_huagong("乾", "离", "坎", "兑", "午")
        self.assertEqual(r.state, HuaGongState.KEZHI)
        self.assertEqual(r.wu_relation, "克制")

    def test_reverse_state_detection(self):
        """无反卦无化工卦 → REVERSE（或 UNRESOLVED）"""
        r = compute_huagong("乾", "乾", "坤", "坤", "子")
        self.assertIn(r.state, (HuaGongState.UNRESOLVED, HuaGongState.REVERSE))

    def test_evidence_chain_contains_facts(self):
        """化工证据链为纯事实"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        for e in r.evidence:
            self.assertNotIn("POSITIVE", e)
            self.assertNotIn("direction", e.lower())


class TestJiehhouEndToEnd(unittest.TestCase):
    """节候卦端到端验证"""

    def test_all_24_solar_terms(self):
        for i in range(24):
            info = get_seasonal_hexagram(i)
            self.assertEqual(info.jq_name, SOLAR_TERMS[i])
            self.assertIn(info.main_gua, JIEHOU_GUA_NAME.values())
            self.assertIn(info.moving_line, range(6))

    def test_dongzhi_yi_fu(self):
        """原典 L1492：节卦坎初六起冬至。"""
        info = get_seasonal_hexagram(0)
        self.assertEqual(info.jq_name, "冬至")
        self.assertEqual(info.main_gua, "坎")
        self.assertEqual(info.result_gua, "初六")
        self.assertEqual(info.moving_line, 0)

    def test_invalid_index_raises(self):
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(-1)
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(24)

    def test_evidence_has_source_ref(self):
        info = get_seasonal_hexagram(0)
        self.assertTrue(any("河洛真数" in e or "易冒" in e for e in info.evidence))


if __name__ == "__main__":
    unittest.main()
