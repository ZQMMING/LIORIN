"""批次 E 守卫（2026-10-08）：七项「说了不算 / 收了不用 / 吞了不报」的修复

这一批全是**同一类**缺陷：代码在跑，但有一层是死的。逐项钉死：

═══════���═════════════════════════════════════════════════════════════
项目  缺陷                          守卫思路
═══════���═════════════════════════════════════════════════════════════
E1     to_structured 少三块判词    真实 dict 进去，三块必须原样出来
E2     八个 kuozhan 判法裸 pass    异常不再消失；可执行代码里不许再有裸 pass
E3     numbers 注释与实现不符      注释不得再声称「天数25 走特殊分支」
E4     confidence 伪称原典权威度   字面量集中到 _CONF_BASE，且注释如实
E5     judgment 收下却不用        换一份 judgment，总览文本必须变
E6     opp/risk 收下却不用         换输入，secondary/avoid 必须跟着变
E7     ELEMENT_MODIFIERS 无作废标注 数值权重原典无出处，须显式作废
═══════���═════════════════════════════════════════════════════════════

**E5/E6 的守卫要点**：不能只查「函数体里出现了 judgment 这个名字」——
那正是旧代码已经做到的（旧代码签名里就有 judgment，只是函数体没用）。
必须**换输入看输出变不变**：输入不变则输出不变的，旧缺陷必然复现。
"""
from __future__ import annotations

import ast
import io
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"


def _code_only(path: Path) -> str:
    """只含可执行代码的源码：剥掉三引号文档字符串与 ``#`` 注释。

    判「某缺陷不存在」必须落在这上面——修复注释里大量引用旧串，
    全文 assertNotIn 会被注释里另一份副本遮住，等于没判。
    """
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            b = node.body
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                node.body = b[1:] or [ast.Pass()]
    code = ast.unparse(tree)
    return "\n".join(re.sub(r"\s+#.*$", "", ln) for ln in code.split("\n"))


def _doc_and_comments(path: Path) -> str:
    """文档字符串 + 注释原文（用来判「标注在不在」）。"""
    return io.open(path, encoding="utf-8").read()


class TestE1ToStructuredCarriesEverything(unittest.TestCase):
    """E1：结构化视图不得比原始 dict 少判词。"""

    def test_three_blocks_pass_through(self):
        from tongshu.engines.heluo.guajie import to_structured
        gj = {
            "benming": {"hexagram": "乾", "gua_ci": "元亨利贞"},
            "canping": {"诗": "一字千金"},
            "evidence": ["第一行", "第二行"],
            "kuozhan": {}, "summary": [], "nayin_yuanqi": [],
            "jiehua_gong": [], "si_duan": [], "zhengdui_fandui": [],
            "shu_xiong": None,
        }
        st = to_structured(gj)
        self.assertEqual(st["benming"], gj["benming"])
        self.assertEqual(st["canping"], gj["canping"])
        self.assertEqual(st["evidence"], gj["evidence"])

    def test_missing_keys_become_empty_not_keyerror(self):
        from tongshu.engines.heluo.guajie import to_structured
        st = to_structured({})
        self.assertIsNone(st["benming"])
        self.assertIsNone(st["canping"])
        self.assertEqual(st["evidence"], [])


class TestE2KuozhanNoLongerSwallows(unittest.TestCase):
    """E2：判法失败必须留痕，不得从结果里凭空消失。"""

    def test_kuozhan_errors_exists_and_empty_on_healthy_run(self):
        from tongshu.engines.heluo import guajie as g
        self.assertTrue(hasattr(g, "kuozhan_errors"))
        g.kuozhan_errors()   # 调用方必须能拿到一份拷贝
        self.assertIsInstance(g.kuozhan_errors(), list)

    def test_returns_copy_not_the_live_list(self):
        """返回内部 list 会让调用方一个 clear() 把痕迹全抹掉。"""
        from tongshu.engines.heluo import guajie as g
        first = g.kuozhan_errors()
        self.assertIsNot(first, g._KZ_ERRORS)
        first.append("伪造一条")
        self.assertNotIn("伪造一条", g.kuozhan_errors())

    def test_no_bare_pass_left_in_kuozhan_builder(self):
        """八个判法逐个 try，裸 ``pass`` 一律换成登记。"""
        code = _code_only(_E / "guajie.py")
        tree = ast.parse(_code_only(_E / "guajie.py"))
        bare = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for h in node.handlers:
                    body = [n for n in h.body
                            if not (isinstance(n, ast.Expr)
                                    and isinstance(n.value, ast.Constant))]
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        bare += 1
        self.assertEqual(bare, 0, f"仍有 {bare} 处 except 里是裸 pass——异常被吞")

    def test_error_log_records_name_and_exception(self):
        """留痕要能定位到「哪个判法、什么错」，不是一句「计算失败」。"""
        code = _code_only(_E / "guajie.py")
        self.assertIn("_KZ_ERRORS.append", code)
        self.assertIn("type(_e).__name__", code)


class TestE3NumbersCommentMatchesCode(unittest.TestCase):
    """E3：注释不得声称一条走不到的分支。"""

    def test_twenty_five_goes_through_yu_branch(self):
        from tongshu.engines.heluo.numbers import normalize_tian_shu
        self.assertEqual(normalize_tian_shu(25), 5)

    def test_zero_is_the_reachable_tail_case(self):
        from tongshu.engines.heluo.numbers import normalize_tian_shu
        self.assertEqual(normalize_tian_shu(0), 5)

    #: 审计订正块在 docstring 里的起始标记。断言一律按此**切片**，
    #: 不对整段 docstring 做 assertNotIn——订正块本身要引用旧串来解释错在哪，
    #: 全文匹配会被自己写的订正说明打中，等于判了个寂寞。
    _AUDIT = "⚠ 2026-10-08 审计修"

    def _docstring_split(self) -> tuple[str, str]:
        doc = (_E / "numbers.py").read_text(encoding="utf-8")
        i = doc.index("def normalize_tian_shu")
        j = doc.index('"""', i)
        k = doc.index('"""', j + 3) + 3
        whole = doc[j:k]
        return (whole.split(self._AUDIT)[0], self._AUDIT + whole.split(self._AUDIT)[1]
                if self._AUDIT in whole else "")

    def test_rule_block_no_longer_claims_25_is_special(self):
        rule_block, _ = self._docstring_split()
        self.assertNotIn("特殊：天数25", rule_block,
                         "规则块仍称天数25 走特殊分支——实测它走的是余数分支")
        self.assertIn("兜底", rule_block, "规则块应写明末尾兜底的实际条件")

    def test_correction_block_kept_with_reason(self):
        """订正不能只删了旧串就完事——必须留下「为什么是错的」。"""
        _, corr = self._docstring_split()
        self.assertTrue(corr, "订正说明被删了：旧串删了却不说错在哪，下一轮会重犯")
        self.assertIn("这是错的", corr)
        self.assertIn("走 yu 分支", corr, "订正须点明天数25 实际走的是余数分支")
        self.assertIn("normalize_tian_shu(0)==5", corr,
                      "订正须给出末尾兜底的真正可达入参")

    def test_inline_comment_on_tail_return_is_truthful(self):
        """末尾那行 ``return 5`` 的行内注释也不得再称「天数=25 的特殊情况」。"""
        src = (_E / "numbers.py").read_text(encoding="utf-8")
        tail = src.rindex("return 5  #")
        line = src[tail:src.index("\n", tail)]
        self.assertIn("天数25 走不到这里", line,
                      "行内注释未点明天数25 走不到这里，正是本轮修掉的那处误导")


class TestE4ConfidenceNoLongerFakesAuthority(unittest.TestCase):
    """E4：confidence 是引擎自定刻度，不得包装成「原典权威度」。"""

    def test_conf_base_constant_exists(self):
        from tongshu.engines.heluo import guidance as gd
        self.assertEqual(gd._CONF_BASE, 0.85)

    def test_no_hardcoded_confidence_literal_left(self):
        """三处 0.85 集中到一处后，动作项不该再各自写死。"""
        code = _code_only(_E / "guidance.py")
        flat = re.sub(r"\s+", "", code)
        self.assertNotIn("confidence=0.85", flat,
                         "动作项仍直接写死 0.85，未走 _CONF_BASE")

    def test_comment_says_engine_scale_not_original_authority(self):
        src = (_E / "guidance.py").read_text(encoding="utf-8")
        i = src.index("confidence: float")
        line = src[i:src.index("\n", i)]
        self.assertIn("引擎自定标度", line)
        self.assertNotIn("基于原典权威度", line)


class TestE5JudgmentActuallyUsed(unittest.TestCase):
    """E5：judgment 收下就得用。守卫靠**换输入看输出变**。"""

    class _J:
        def __init__(self, n, by=""):
            self.supporting_assertions = ["a%d" % i for i in range(n)]
            self.authorized_by = by

    def _overview(self, judgment):
        from tongshu.engines.heluo.guidance import HeluoGuidanceEngine
        return HeluoGuidanceEngine().generate(
            assertions=[], judgment=judgment,
            source_gua="乾", target_gua="坤", yuan_tang="乾",
            hua_gong_state="NORMAL").overview

    def test_overview_varies_with_judgment(self):
        """旧实现无论 judgment 是什么都吐同一串字 → 换输入输出不变。"""
        a = self._overview(self._J(2, "HELUO_RULES::X"))
        b = self._overview(self._J(7, "HELUO_RULES::Y"))
        self.assertNotEqual(a, b, "换 judgment 总览不变，说明它仍被收下不用")

    def test_overview_reports_support_count(self):
        ov = self._overview(self._J(3, "HELUO_RULES::Z"))
        self.assertIn("3", ov)
        self.assertIn("断言", ov)

    def test_authorized_by_only_printed_when_present(self):
        """没有授权方就不写——不得凭空造一个授权名字。"""
        self.assertNotIn("授权：", self._overview(self._J(1, "")))
        self.assertIn("授权：HELUO_RULES::Z", self._overview(self._J(1, "HELUO_RULES::Z")))

    def test_no_judgment_still_renders_base_tone(self):
        ov = self._overview(None)
        self.assertNotIn("断言支撑", ov)


class TestE6OpportunityAndRiskActuallyUsed(unittest.TestCase):
    """E6：opp/risk 收下就得用。守卫同样靠换输入看输出变。"""

    def _run(self, strengths, severities, score):
        from tongshu.engines.heluo.interpretation import (
            OpportunityFactor, RiskFactor, RelationalInterpretationEngine)
        eng = RelationalInterpretationEngine({})
        eng._opportunities = [
            OpportunityFactor(type=t, strength=s, time_window="birth",
                              classical_basis="")
            for t, s, _d in strengths]
        eng._risks = [
            RiskFactor(type=t, severity=s, trigger_condition="birth",
                       classical_basis="")
            for t, s, _d in severities]
        return eng._generate_recommended_action(
            eng._opportunities[0], eng._risks[0], score)

    def test_secondary_follows_opportunity_types(self):
        a = self._run([("贵人", 0.8, "d")], [("小人", 0.5, "d")], 0.6)
        b = self._run([("财源", 0.8, "d")], [("小人", 0.5, "d")], 0.6)
        self.assertNotEqual(a.secondary, b.secondary,
                            "换机会类型而 secondary 不变，说明仍写死")
        self.assertEqual(a.secondary, ["贵人"])
        self.assertEqual(b.secondary, ["财源"])

    def test_avoid_follows_risk_types(self):
        a = self._run([("贵人", 0.8, "d")], [("口舌", 0.5, "d")], 0.6)
        b = self._run([("贵人", 0.8, "d")], [("官非", 0.5, "d")], 0.6)
        self.assertEqual(a.avoid, ["口舌"])
        self.assertEqual(b.avoid, ["官非"])

    def test_stronger_item_sorts_first(self):
        r = self._run([("弱机", 0.2, "d"), ("强机", 0.9, "d")],
                      [("轻患", 0.2, "d"), ("重患", 0.9, "d")], 0.6)
        self.assertEqual(r.secondary[0], "强机")
        self.assertEqual(r.avoid[0], "重患")

    def test_confidence_modulated_by_net(self):
        good = self._run([("大机", 0.9, "d")], [("小患", 0.1, "d")], 0.6)
        bad = self._run([("小机", 0.1, "d")], [("大患", 0.9, "d")], 0.6)
        self.assertNotEqual(good.confidence, bad.confidence,
                            "净差不同却同置信度，说明仍只看 score")
        self.assertGreater(good.confidence, bad.confidence)

    def test_confidence_stays_in_unit_interval(self):
        hi = self._run([("大机", 1.0, "d")], [("无患", 0.0, "d")], 0.99)
        lo = self._run([("无", 0.0, "d")], [("大患", 1.0, "d")], -0.99)
        for r in (hi, lo):
            self.assertGreaterEqual(r.confidence, 0.0)
            self.assertLessEqual(r.confidence, 1.0)


class TestE7ElementModifiersMarkedVoid(unittest.TestCase):
    """E7：无出处的数值权重必须显式作废。"""

    def test_void_marker_present(self):
        src = (_E / "interpretation.py").read_text(encoding="utf-8")
        i = src.index("ELEMENT_MODIFIERS = {")
        head = src[max(0, i - 900):i]
        self.assertIn("已作废", head, "ELEMENT_MODIFIERS 头顶缺作废标注")
        self.assertIn("hexagram_state", head, "须指向判定其全书无出处的那一处")

    def test_marker_says_numbers_are_self_authored(self):
        src = (_E / "interpretation.py").read_text(encoding="utf-8")
        head = src[:src.index("ELEMENT_MODIFIERS = {")]
        self.assertIn("数值系自拟", head,
                      "只写「作废」不说数值是自拟的，仍会被当成待接续的原典权重")

    def test_constant_itself_retained_for_continuation(self):
        """作废 ≠ 删除：留常量但不得投入判定。"""
        from tongshu.engines.heluo.interpretation import ELEMENT_MODIFIERS
        self.assertEqual(ELEMENT_MODIFIERS["当令"], 0.15)
        code = _code_only(_E / "interpretation.py")
        flat = re.sub(r"\s+", "", code)
        # 允许裸常量存在，但不得出现在 score 累加链里
        for banned in ("ELEMENT_MODIFIERS.get", "ELEMENT_MODIFIERS[type",
                       "MODIFIERS[type]", "+ELEMENT_MODIFIERS"):
            self.assertNotIn(banned, flat,
                             f"作废常量仍被投入判定：{banned}")


if __name__ == "__main__":
    unittest.main()