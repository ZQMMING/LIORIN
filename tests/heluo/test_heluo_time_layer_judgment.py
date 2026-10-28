# -*- coding: utf-8 -*-
"""时间层判据守卫（2026-10-25 新增）。

背景
----
``time_layer_judgment`` 补上了「诊断图注册了四条时间层规则、却从不产出证据」
这个空授权。判据来源是原典爻辞判据（起例卷之上 L212「三辞吉」）。

本守卫钉死**三条硬纪律**（与解读层接线同一口径），防止将来被"优化"掉：

1. **只给吉 / 不判，绝不给 0–1 分数** —— 分数是自拟的，无原典依据；
2. **不复活已作废的自拟分数**（``get_base_factors`` / ``calculate_element_modifier``
   / ``_hexagram_base_score`` / ``_year_cycle_factor``）；
3. **每条判定都必须可回查原典**（``source_ref`` 非空且指向原典条目）。

另钉死**两条结构事实**（防止接线回退）：
4. 四条时间层规则在**生产链路径**（带 target_date）必须产出证据；
5. 判据**不得判凶** —— 原典 L222「三辞凶」只给名目未给门槛，
   L257 明言「若拘拘于爻辞吉凶，则失之矣」⇒ 凶须有正向门槛，
   本包无此门槛 ⇒ 恒不判凶。
"""
from __future__ import annotations

import ast
import inspect
import re
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter                     # noqa: E402
from heluo_engine.engines.heluo import time_layer_judgment as tlj  # noqa: E402
from heluo_engine.engines.heluo.evidence_producer import (          # noqa: E402
    HeLuoEvidenceProducer,
)
from heluo_engine.engines.heluo.diagnosis_rule_graph import (        # noqa: E402
    HELUO_RULES, build_diagnosis_graph, dropped_rules,
)

TIME_RULE_IDS = ("HL_DAYUN", "HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA")

#: 已作废、**不得复活**的自拟分数函数
FORBIDDEN_CALLS = (
    "calculate_hexagram_state(",
    "get_base_factors(",
    "calculate_element_modifier(",
    "_hexagram_base_score(",
    "_year_cycle_factor(",
)


def _adapter_result():
    return HeluoAdapter().compute(
        (1983, 11, 3, 12), gender="male", target_date="2026-10-23")


class TestNoFabricatedScore(unittest.TestCase):
    """纪律①：只给三态，不给 0–1 分数。"""

    def test_judgment_has_no_numeric_score_field(self):
        """TimeLayerJudgment 不得携带任何数值分数字段。"""
        fields = {f for f in dir(tlj.TimeLayerJudgment) if not f.startswith("_")}
        banned = {"score", "confidence", "strength", "weight", "ratio",
                  "probability", "value", "points", "grade"}
        self.assertEqual(fields & banned, set(),
                         f"判定对象出现数值分数字段：{sorted(fields & banned)}")

    def test_to_dict_has_no_numeric_score(self):
        d = tlj.judge_time_layer_by_ci(
            "HL_LIUNIAN_GUA", hexagram="益", yao="初九", ci="利用为大作，元吉，无咎。")
        for k, v in d.to_dict().items():
            self.assertNotIsInstance(v, float,
                                     f"to_dict 出现浮点分数：{k}={v!r}")

    def test_passed_is_tri_state(self):
        """``passed`` 只能是 True / False / None。"""
        for ci in ("元吉在兹", "亨利之孚", "困于葛藟", ""):
            r = tlj.judge_time_layer_by_ci("HL_RIGUA", ci=ci)
            self.assertIn(r.passed, (True, False, None), r.passed)

    def test_evidence_attributes_carry_no_numeric_score(self):
        """证据的 attributes 里不得出现浮点分数。"""
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        for ev in evs:
            if ev.rule_id in TIME_RULE_IDS:
                for k, v in (ev.attributes or {}).items():
                    self.assertNotIsInstance(v, float,
                                             f"{ev.rule_id}.{k} 是浮点分数：{v!r}")


class TestNeverResurrectDeprecatedScores(unittest.TestCase):
    """纪律②：不复活已作废的自拟分数。"""

    def test_module_source_does_not_call_forbidden(self):
        src = inspect.getsource(tlj)
        for bad in FORBIDDEN_CALLS:
            self.assertNotIn(bad, src,
                             f"time_layer_judgment 源码出现已作废调用：{bad}")

    def test_package_wide_no_forbidden_call(self):
        """全包扫描：任何 .py 都不得**调用**已作废函数。

        ⚠ 用 **AST** 而非文本搜索 —— 文本搜索会把「函数定义」与
        「docstring 里提及」一并命中 ⇒ 假阳性。
        """
        pkg = _REPO / "src" / "heluo_engine"
        offenders = []
        for p in pkg.rglob("*.py"):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                f = node.func
                if isinstance(f, ast.Name):
                    name = f.id
                elif isinstance(f, ast.Attribute):
                    name = f.attr
                else:
                    continue
                if name in ("get_base_factors", "calculate_element_modifier",
                            "calculate_hexagram_state", "_hexagram_base_score",
                            "_year_cycle_factor"):
                    offenders.append(f"{p.relative_to(pkg)}:{node.lineno} {name}")
        self.assertEqual(offenders, [],
                         "出现已作废自拟分数的调用：%r" % offenders)


class TestTraceableToSource(unittest.TestCase):
    """纪律③：每条判定都必须可回查原典。"""

    def test_every_judgment_has_source_ref(self):
        res = _adapter_result()
        js = tlj.collect_time_layer_judgments(res)
        js.append(tlj.collect_dayun_judgment(res))
        self.assertTrue(js)
        for j in js:
            with self.subTest(rule=j.rule_id):
                self.assertTrue(j.source_ref.strip(),
                                "判定缺原典出处（source_ref 为空）")
                self.assertTrue(j.basis.strip(), "判定缺判据依据（basis 为空）")
                self.assertTrue(j.detail.strip(), "判定缺过程说明（detail 为空）")

    def test_source_ref_mentions_original_text(self):
        """出处须指向原典条目（含「起例卷」/「日卦」/行号等可回查线索）。"""
        for rid, ref in tlj.SOURCE_REFS.items():
            with self.subTest(rule=rid):
                self.assertTrue(
                    re.search(r"起例卷|日卦|L\d+", ref),
                    f"{rid} 的出处不可回查：{ref!r}")

    def test_evidence_keeps_source_ref(self):
        """证据里须保留原典出处（下游要能回查）。"""
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        for ev in evs:
            if ev.rule_id in TIME_RULE_IDS:
                with self.subTest(rule=ev.rule_id):
                    self.assertTrue((ev.source_rule_ref or "").strip())
                    self.assertTrue(
                        (ev.attributes or {}).get("source_ref", "").strip())


class TestNeverJudgeInauspicious(unittest.TestCase):
    """纪律④：不得判凶（原典无凶门槛 ⇒ 恒不判）。"""

    def test_judge_never_returns_false(self):
        for ci in ("困于葛藟", "厉终有悔", "勿恤，吝", "羝羊触藩，不能退",
                   "需于血，出自穴。", "悔亡，厥宗噬肤，往何咎？"):
            r = tlj.judge_time_layer_by_ci("HL_LIUNIAN_GUA", ci=ci)
            with self.subTest(ci=ci):
                self.assertIsNot(r.passed, False,
                                 "本包原典无「三辞凶」门槛 ⇒ 不得判凶")

    def test_good_word_is_narrow(self):
        """吉的门槛**极窄**：只认「元吉」「亨利」两个词组。"""
        self.assertTrue(tlj.judge_time_layer_by_ci(
            "HL_LIUNIAN_GUA", ci="利用为大作，元吉，无咎。").passed)
        # 单字「吉」不算（原文明举的是「元吉亨利」）
        self.assertIsNone(tlj.judge_time_layer_by_ci(
            "HL_LIUNIAN_GUA", ci="艰则吉。").passed)


class TestWiringIntact(unittest.TestCase):
    """接线不回退：四条规则产出证据、进入诊断图、不被丢弃。"""

    def test_four_rules_produce_evidence(self):
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        produced = {e.rule_id for e in evs}
        for rid in TIME_RULE_IDS:
            with self.subTest(rule=rid):
                self.assertIn(rid, produced)

    def test_evidence_enters_diagnosis_graph(self):
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        g = build_diagnosis_graph(evs, [], None, subject="guard")
        rules = {a.source_rule for a in g.assertions}
        for rid in TIME_RULE_IDS:
            with self.subTest(rule=rid):
                self.assertIn(rid, rules, "该规则未进入诊断图")

    def test_no_rule_dropped(self):
        """不得有「产出却被丢弃」的规则（此前 HL_HEXAGRAM_STRUCTURE 即如此）。"""
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        build_diagnosis_graph(evs, [], None, subject="guard")
        self.assertEqual(dropped_rules(), [],
                         "有规则被丢弃（产出却未注册/未授权）")

    def test_direction_comes_from_evidence(self):
        """方向取自证据的 ``passed``（三态），不来自信号层臆造。"""
        evs = HeLuoEvidenceProducer().produce(_adapter_result())
        g = build_diagnosis_graph(evs, [], None, subject="guard")
        for a in g.assertions:
            if a.source_rule in TIME_RULE_IDS:
                with self.subTest(rule=a.source_rule):
                    self.assertIn(a.direction.value,
                                  ("supportive", "caution", "neutral"))


if __name__ == "__main__":
    unittest.main()
