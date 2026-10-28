# -*- coding: utf-8 -*-
"""河洛四个 P0 守卫（2026-10-22 全面体检补齐）。

体检发现的四处「有功能、但没有能抓住退化的守卫」，本文件补上：

1. ``judge_ye_buye`` —— 叶/不叶判据**零单测**。它是贵命十体⑤「有援」
   与 guajie 输出的直接来源，改坏了没人知道。
2. ``HeLuoEvidenceProducer`` —— 此前只验结构（有几条 evidence），
   **不验值**。证据层的价值全在值上：天数地数、先天卦、元堂、后天卦、
   化工状态，每一条都必须与 ``HeluoResult`` 对得上。
3. **fast-path 的 frozen_state** —— 冻结态此前只在全量路径下验过；
   fast path 是生产路径，其 ``dayun_summary`` 是定稿要求的大运元数据，
   必须单独钉死。
4. ``metrics_v2`` —— 零单测。且它有三处「占位分当实测分」：
   无参考输出 → 稳定性直接 1.0 满分；无 classical_source → 0.5；
   无 evidence_chain → 0.5。这三项会**静默抬高总分**。
   本文件钉死：占位分必须在 warnings 里留痕。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo import metrics_v2
from heluo_engine.engines.heluo.canonical import HeluoCanonical
from heluo_engine.engines.heluo.evidence_producer import HeLuoEvidenceProducer
from heluo_engine.engines.heluo.frozen_state import build_frozen_state
from heluo_engine.engines.heluo.guajie import judge_ye_buye, load_guajie_data

_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_TARGET_YEAR = 2026
_TARGET_MONTH = 7
_TARGET_DAY = 15


def _calc(**kw):
    """fast path（生产路径）。"""
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午", era="zhong",
        birth_year=1983, birth_date="1983-11-03",
        target_year=_TARGET_YEAR, target_month=_TARGET_MONTH,
        target_day=_TARGET_DAY, **kw,
    )


def _calc_full():
    """全量路径（不传 target_year → 退回旧契约）。"""
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午", era="zhong",
        birth_year=1983, birth_date="1983-11-03",
    )


class TestJudgeYeBuye(unittest.TestCase):
    """叶/不叶判据（原典：卦气月 + 纳甲本命 + 旺时区间）。"""

    def test_qian_in_guaqi_month_and_najia_is_ye(self):
        """乾卦：卦气属四月、纳甲含甲子 → 四月生且甲子年 → 叶（吉象）。"""
        r = judge_ye_buye("乾", 4, "甲子")
        self.assertIsNotNone(r, "乾卦应有叶/不叶判定")
        self.assertTrue(r.ye, "生月=卦气月且纳甲本命 → 应判叶")
        self.assertFalse(r.buye)
        self.assertTrue(r.najia_hit)
        self.assertEqual(r.gua_qi_month, 4)
        self.assertEqual(r.birth_month, 4)
        self.assertTrue(any("叶" in e for e in r.evidence),
                        "evidence 必须说明判定依据")

    def test_not_in_guaqi_month_and_not_najia_is_buye(self):
        """乾卦：一月生（≠卦气四月）且干支不在纳甲 → 不叶（凶象）。"""
        r = judge_ye_buye("乾", 1, "庚午")
        self.assertIsNotNone(r)
        self.assertFalse(r.ye, "生月≠卦气月且不在纳甲 → 不应判叶")
        self.assertTrue(r.buye, "应判不叶")
        self.assertFalse(r.najia_hit)

    def test_guaqi_month_only_is_half_ye(self):
        """得时但不在纳甲 → 半叶（吉中带损），不得判成不叶。"""
        r = judge_ye_buye("乾", 4, "庚午")
        self.assertIsNotNone(r)
        self.assertTrue(r.ye, "生月=卦气月 → 得时")
        self.assertFalse(r.buye, "得时即非不叶")
        self.assertFalse(r.najia_hit)

    def test_unknown_hexagram_returns_none(self):
        """卦不在数据里 → 返回 None（不判），不得凭空给个凶。"""
        self.assertIsNone(judge_ye_buye("不存在的卦xyz", 4, "甲子"))

    def test_evidence_records_both_inputs(self):
        """evidence 必须同时写出生月与年干支的核对过程。"""
        r = judge_ye_buye("乾", 4, "甲子")
        self.assertTrue(any("卦气" in e for e in r.evidence))
        self.assertTrue(any("纳甲" in e for e in r.evidence))


class TestEvidenceProducerValues(unittest.TestCase):
    """证据层：**值**必须与 HeluoResult 对得上（此前只验结构）。"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.evs = HeLuoEvidenceProducer().produce(cls.res)
        cls.by_rule = {e.rule_id: e for e in cls.evs}

    def test_produces_the_expected_rule_set(self):
        """六条事实证据一条都不能少。"""
        for rid in ("HL_TIAN_DI_SHU", "HL_PRENATAL_HEXAGRAM", "HL_YUANTANG",
                    "HL_POSTNATAL_HEXAGRAM", "HL_HEXAGRAM_STRUCTURE",
                    "HL_HUA_GONG"):
            self.assertIn(rid, self.by_rule, f"缺少证据 {rid}")

    def test_tian_di_shu_values_match_result(self):
        v = self.by_rule["HL_TIAN_DI_SHU"].value
        self.assertEqual(v["tian_shu"], self.res.numbers.tian_shu)
        self.assertEqual(v["di_shu"], self.res.numbers.di_shu)
        self.assertEqual(v["tian_reduced"], self.res.numbers.tian_reduced)
        self.assertEqual(v["di_reduced"], self.res.numbers.di_reduced)

    def test_hexagram_values_match_result(self):
        self.assertEqual(self.by_rule["HL_PRENATAL_HEXAGRAM"].value,
                         self.res.prenatal.hexagram_name)
        self.assertEqual(self.by_rule["HL_POSTNATAL_HEXAGRAM"].value,
                         self.res.postnatal.hexagram_name)

    def test_yuantang_value_matches_result(self):
        """元堂证据的值就是元堂名（如「初六」），必须逐字相等。"""
        self.assertEqual(self.by_rule["HL_YUANTANG"].value,
                         self.res.yuantang.yuantang)

    def test_hua_gong_value_matches_result(self):
        """化工证据的值就是化工状态，必须与 result 一致。"""
        self.assertEqual(self.by_rule["HL_HUA_GONG"].value,
                         self.res.hua_gong.state)

    def test_every_evidence_declares_a_real_source(self):
        """每条证据都要有 source_rule_ref，且不是空串/占位符。"""
        for e in self.evs:
            self.assertTrue(e.source_rule_ref, f"{e.rule_id} 缺出处")
            self.assertNotIn("heluo_", e.source_rule_ref,
                             f"{e.rule_id} 的出处指向了不存在的 data/rules/heluo_*.json")

    def test_no_direction_or_confidence_in_evidence(self):
        """证据层只放事实，不放吉凶/强度（V13 §五硬约束）。"""
        for e in self.evs:
            for banned in ("direction", "polarity", "strength", "confidence"):
                self.assertNotIn(banned, e.attributes,
                                 f"{e.rule_id} 的 attributes 不得含 {banned}")


class TestFastPathFrozenState(unittest.TestCase):
    """fast-path 的冻结态（生产路径）。"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.fs = build_frozen_state(cls.res)

    def test_dayun_summary_is_pure_metadata(self):
        """定稿：大运只生成元数据 {start_age, end_age, ganzhi}。"""
        self.assertTrue(self.fs.dayun_summary, "dayun_summary 不得为空")
        for i, d in enumerate(self.fs.dayun_summary):
            self.assertEqual(set(d.keys()), {"start_age", "end_age", "ganzhi"},
                             f"第{i + 1}条大运元数据字段不符")
            self.assertIsInstance(d["ganzhi"], str)
            self.assertEqual(len(d["ganzhi"]), 2, "干支应为两字")
            self.assertLessEqual(d["start_age"], d["end_age"])

    def test_dayun_summary_ages_are_contiguous(self):
        """大运年龄区间必须首尾相接、不重叠、不留空。"""
        segs = self.fs.dayun_summary
        for a, b in zip(segs, segs[1:]):
            self.assertEqual(b["start_age"], a["end_age"] + 1,
                             "大运年龄区间必须连续")
        self.assertEqual(segs[0]["start_age"], 1, "首运自 1 岁起")

    def test_core_frozen_fields_match_result(self):
        """冻结态的先天/后天/元堂必须与 result 一致。"""
        self.assertEqual(self.fs.prenatal_name, self.res.prenatal.hexagram_name)
        self.assertEqual(self.fs.postnatal_name, self.res.postnatal.hexagram_name)
        self.assertEqual(self.fs.tian_shu, self.res.numbers.tian_shu)
        self.assertEqual(self.fs.di_shu, self.res.numbers.di_shu)
        self.assertEqual(self.fs.hua_gong_state, self.res.hua_gong.state)

    def test_frozen_state_is_identical_in_both_paths(self):
        """fast path 与全量路径的冻结态**必须一致**（算力裁剪不得改结果）。"""
        full = build_frozen_state(_calc_full())
        self.assertEqual(self.fs.prenatal_name, full.prenatal_name)
        self.assertEqual(self.fs.postnatal_name, full.postnatal_name)
        self.assertEqual(self.fs.yuan_qi_state, full.yuan_qi_state)
        self.assertEqual(self.fs.hua_gong_state, full.hua_gong_state)
        self.assertEqual(self.fs.dayun_summary, full.dayun_summary,
                         "大运元数据不得因路径不同而不同")


class TestMetricsV2Minimal(unittest.TestCase):
    """metrics_v2 的最小单测 + 占位分必须留痕。"""

    def _interp(self, **extra):
        d = {
            "current_state": "测试状态",
            "opportunity": "机会",
            "risk": "风险",
            "recommended_action": "这是一条足够长的建议行动文本",
        }
        d.update(extra)
        return d

    def test_empty_interpretation_gives_empty_score(self):
        s = metrics_v2.evaluate_interpretation({})
        self.assertEqual(s.overall_score, 0.0)
        self.assertEqual(s.required_fields_total,
                         len(metrics_v2.REQUIRED_INTERPRETATION_FIELDS))

    def test_missing_required_field_lowers_logic_completeness(self):
        """缺必需字段 → 逻辑完整性下降。"""
        full = metrics_v2.evaluate_interpretation(self._interp())
        part = metrics_v2.evaluate_interpretation(
            self._interp(current_state="", risk=""))
        self.assertLess(part.logic_completeness, full.logic_completeness)
        self.assertLess(part.required_fields_present, full.required_fields_present)

    def test_placeholder_scores_are_flagged_as_unmeasured(self):
        """⚠ 核心：无参考/无古籍源/无证据链时，三项是**占位分**，必须留痕。

        修前这三项静默抬高总分（稳定性直接给 1.0「满分」），
        使用者无从分辨「实测很好」与「根本没测」。
        """
        s = metrics_v2.evaluate_interpretation(self._interp())
        joined = " ".join(s.warnings)
        self.assertIn("稳定性未实测", joined)
        self.assertIn("古籍一致性未实测", joined)
        self.assertIn("证据闭合度未实测", joined)

    def test_measured_stability_has_no_placeholder_warning(self):
        """给了参考输出 → 稳定性是实测的，不应再出现「未实测」留痕。

        ``reference_outputs`` 是**解释输出字典**的列表（与
        ``_calculate_similarity`` 的读法一致），不是 score 对象。
        """
        ref = [self._interp()]
        s = metrics_v2.evaluate_interpretation(
            self._interp(), reference_outputs=ref)
        joined = " ".join(s.warnings)
        self.assertNotIn("稳定性未实测", joined)

    def test_classical_alignment_reflects_actual_reference(self):
        """给了匹配的 classical_source → 古籍一致性应高于占位分 0.5。"""
        src = {
            "book_name": "河洛真数",
            "volume": "起例卷之中",
            "original_text": "一卦名吉",
            "normalized_rule": "贵命六项判据",
        }
        ref = {
            "book": "河洛真数",
            "volume": "起例卷之中",
            "paragraph": "一卦名吉",
            "rule": "贵命六项判据",
        }
        s = metrics_v2.evaluate_interpretation(
            self._interp(classical_reference=ref), classical_source=src)
        self.assertGreater(s.classical_alignment, 0.5,
                           "古籍引用齐备时一致性分应高于占位分")

    def test_interpretation_output_carries_classical_reference(self):
        """解释层必须输出 classical_reference —— metrics_v2 把它列为必需字段。

        修前解释层**从不带**该键，质量分接上即恒缺一项（上限 4/5）。
        """
        from heluo_engine.engines.heluo.interpretation import (
            HeluoInput, RelationalInterpretationEngine,
        )
        inp = HeluoInput(
            prenatal_hexagram="天水讼", yuan_tang="初六",
            postnatal_hexagram="泽天夬", day_hexagram="屯上蒙下",
            year_cycle="乙巳", month_cycle="甲申", day_cycle="丙午",
            element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
            line_position={"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
            time_state={"solar_term": "立秋", "hour": 14},
        )
        out = RelationalInterpretationEngine(inp).compute()
        self.assertTrue(out.classical_reference,
                        "解释输出必须带 classical_reference")
        self.assertEqual(out.classical_reference.get("book"), "河洛真数")
        self.assertTrue(out.classical_reference.get("items"),
                        "classical_reference 应逐条登记六项判据出处")
        for it in out.classical_reference["items"]:
            self.assertIn("line", it)
            self.assertIn("basis", it)


if __name__ == "__main__":
    unittest.main()
