"""批次 H 守卫：诊断图 signals 类型契约 + 建议层伪引（2026-10-08）

两处都是**单元测试全绿、只有真跑管线才会炸**的缺陷：

H1  `build_diagnosis_graph` 的 signals 形参原先**只认 dict**（直接 `sig.get(...)`），
    而管线实际产出的是 `CanonicalSignal` 数据类 → AttributeError。
    更糟的是同一处缺陷在文件里有**两份拷贝**（`_signal_direction_for_evidence`
    与流年/流月断言那段），只修一处仍会炸。
    为什么此前没发现：单测喂的是自造 dict，类型碰巧对得上。

H2  `guidance._build_actions` 的 source_ref 写着 `V13_河洛诊断规则集`——
    该规则集**不存在**，是伪引。批次 C 改了 diagnosis_rule_graph 的 authorized_by，
    **漏了这里**，同一处伪引两处不一致。

H3  顺带钉住「匹配不上信号」必须登记：8 条断言里 6 条方向是 neutral，
    因为管线当前只产出 1 条**八字**信号、河洛信号为 0。
    若不登记，「没有信号」与「有信号但方向未知」在输出上完全一样，没人能发现。
"""
from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"


@dataclass
class _FakeSignal:
    """模拟管线实产的 CanonicalSignal：**没有 rule_id，只有 rule_refs 列表**。"""
    signal_id: str = "SIG-XX"
    direction: str = "NEUTRAL"
    rule_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5


class _FakeEnumDir:
    value = "POSITIVE"


@dataclass
class _FakeEnumSignal:
    """direction 是**枚举**的情形 —— 直接拿去跟字符串比会永假。"""
    signal_id: str = "SIG-YY"
    direction: object = field(default_factory=_FakeEnumDir)
    rule_refs: List[str] = field(default_factory=list)


class TestSignalsContractAcceptsBothShapes(unittest.TestCase):
    def setUp(self):
        from tongshu.engines.heluo import diagnosis_rule_graph as dg
        self.dg = dg

    def test_sig_field_handles_dict_and_object(self):
        self.assertEqual(self.dg._sig_field({"a": 1}, "a"), 1)
        self.assertEqual(self.dg._sig_field(_FakeSignal(), "direction"),
                         "NEUTRAL")
        self.assertEqual(self.dg._sig_field(_FakeSignal(), "nope", "默认"),
                         "默认")

    def test_sig_rule_ids_from_rule_refs_list(self):
        """CanonicalSignal 没有 rule_id，规则 id 在 rule_refs 列表里。"""
        got = self.dg._sig_rule_ids(_FakeSignal(rule_refs=["HL_TIAN_DI_SHU"]))
        self.assertEqual(got, ["HL_TIAN_DI_SHU"])

    def test_sig_rule_ids_still_accepts_legacy_dict(self):
        self.assertEqual(
            self.dg._sig_rule_ids({"rule_id": "HL_YUANTANG"}), ["HL_YUANTANG"])

    def test_sig_direction_unwraps_enum(self):
        """枚举 direction 直接跟字符串比会永假 → 每条证据静默落 neutral。"""
        self.assertEqual(self.dg._sig_direction_str(_FakeEnumSignal()),
                         "POSITIVE")

    def test_build_graph_runs_on_dataclass_signals(self):
        """本条是核心：**真实链路形态**（数据类 + rule_refs 列表）必须能跑通。

        判据不是「不抛异常」——而是**方向真的被读到了**：
        数据类信号的 direction="POSITIVE" 经 rule_refs 匹配后必须产出 SUPPORTIVE 断言。
        若只断言「不抛异常」，那把 direction 恒读成 NEUTRAL 也照样能过，
        等于没测（本模块上一版的 _sig_direction_str 就是这么悄悄退化的）。
        """
        sigs = [_FakeSignal(rule_refs=["HL_TIAN_DI_SHU"], direction="POSITIVE")]
        g = self.dg.build_diagnosis_graph(evidences=[], signals=sigs,
                                           subject="H")
        self.assertTrue(g.assertions, "数据类信号没有产出任何断言")
        self.assertEqual(g.assertions[0].direction.value, "supportive",
                         "数据类信号的 direction 没被读到 —— 静默落成了 neutral")
        self.assertEqual(g.assertions[0].source_rule, "HL_TIAN_DI_SHU")

    def test_enum_direction_also_readable(self):
        """direction 是枚举时也必须读出 POSITIVE。"""
        sigs = [_FakeEnumSignal(rule_refs=["HL_TIAN_DI_SHU"])]
        g = self.dg.build_diagnosis_graph(evidences=[], signals=sigs,
                                           subject="H")
        self.assertTrue(g.assertions)
        self.assertEqual(g.assertions[0].direction.value, "supportive")

    def test_both_get_copies_are_fixed(self):
        """同一处缺陷曾有**两份拷贝**（`_signal_direction_for_evidence` 与
        流年/流月断言那段），只修一处仍会炸。

        这里不能简单禁掉 `sig.get` —— 合法的 dict 取值就在 ``_sig_field`` 里。
        故改为：这两段**具体代码位置**上不得再出现 `sig.get`，
        判据按源码文本切片，避开全文字符串匹配。
        """
        import io
        src = io.open(_E / "diagnosis_rule_graph.py",
                       encoding="utf-8").read()
        for marker in ("def _signal_direction_for_evidence(",
                       "# ── 从 EVENT_SIGNAL 提取流年/流月断言"):
            self.assertIn(marker, src, "锚点 %r 不存在，守卫可能已失效" % marker)
        # ⚠ 判据不能是「切片里没有 sig.get」—— 修复说明本身就要引旧串来交代
        #   错在哪（seg2 开头那句「此处原先也是纯 `sig.get(...)`」就会被命中）。
        #   改为断言**修好的写法确实在位**：那才是「已修」的正向证据。
        i1 = src.index("def _signal_direction_for_evidence(")
        seg1 = src[i1:src.index("def ", i1 + 10)]
        self.assertIn("for sig_rule in _sig_rule_ids(sig):", seg1,
                     "方向匹配那段没走 _sig_rule_ids —— 又退回只认 dict 的 rule_id 了")
        self.assertIn('d = _sig_direction_str(sig)', seg1,
                     "方向匹配那段没走 _sig_direction_str —— 枚举会静默落 neutral")

        i2 = src.index("# ── 从 EVENT_SIGNAL 提取流年/流月断言")
        seg2 = src[i2:src.index("\ndef ", i2 + 10)]
        self.assertIn("direction_str = _sig_direction_str(sig)", seg2,
                      "流年/流月那段又退回 sig.get —— 第二份拷贝没修")
        self.assertIn('_sig_field(sig, "hexagram", "")', seg2,
                      "流年/流月那段还在直接取字段")

    def test_public_helper_exists(self):
        self.assertTrue(callable(self.dg.unmatched_evidence))


class TestUnmatchedIsDisclosed(unittest.TestCase):
    def test_unmatched_records_when_no_signal_matches(self):
        from tongshu.engines.heluo import diagnosis_rule_graph as dg

        class _Ev:
            rule_id = "HL_TIAN_DI_SHU"
            engine = type("E", (), {"value": "HE_LUO"})()
            evidence_id = "e1"
            value = {}
            source_field = "f"
            temporal_scope = type("T", (), {"value": "birth"})()
            calculation_version = "v"
            contract_version = "c"

        class _Node:
            is_authorized = True
            rule_name = "取数"
            source_ref = "x"
            rule_id = "HL_TIAN_DI_SHU"

        saved = dg.HELUO_RULES.get("HL_TIAN_DI_SHU")
        dg.HELUO_RULES["HL_TIAN_DI_SHU"] = _Node()
        try:
            dg.build_diagnosis_graph(
                evidences=[_Ev()],
                signals=[_FakeSignal(rule_refs=["ZPZ-001"])],
                subject="H")
            self.assertIn("HL_TIAN_DI_SHU", dg.unmatched_evidence(),
                          "没匹配到信号却未登记 —— 「无信号」会与「方向未知」混同")
        finally:
            if saved is None:
                dg.HELUO_RULES.pop("HL_TIAN_DI_SHU", None)
            else:
                dg.HELUO_RULES["HL_TIAN_DI_SHU"] = saved


class TestGuidanceNoFabricatedRuleSet(unittest.TestCase):
    #: ⚠ 判「伪引不存在」必须扫**可执行代码**，不能全文匹配：
    #: diagnosis_rule_graph.py:327 的修复说明里就引了旧串
    #: 「V13_河洛诊断规则集」来交代错在哪，全文匹配会被自己写的说明打中——
    #: 这个坑本项目已经踩过两次（E3 注释订正、此处）。
    @staticmethod
    def _code_only(path):
        import ast
        import io
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
        return "\n".join(ast.unparse(tree).split("\n"))

    def test_fabricated_rule_set_name_gone(self):
        code = self._code_only(_E / "guidance.py")
        self.assertNotIn("V13_河洛诊断规则集", code,
                         "批次 C 改了 authorized_by 却漏了 source_ref —— 伪引仍在")

    def test_no_fabricated_name_anywhere_in_heluo(self):
        """全 heluo 扫一遍可执行代码，别处也别留着同一个假规则集名。"""
        hits = [f.name for f in _E.glob("*.py")
                if "V13_河洛诊断规则集" in self._code_only(f)]
        self.assertEqual(hits, [], "河洛引擎里还有可执行代码引用不存在的规则集")

    def test_source_ref_lists_real_rule_ids(self):
        from tongshu.engines.heluo.guidance import HeluoGuidanceEngine
        from tongshu.engines.heluo.diagnosis_rule_graph import AssertionDirection

        class _A:
            direction = AssertionDirection.SUPPORTIVE
            authorized_rule_id = "HELUO_AUTH_HL_HUA_GONG"
            source_rule = "HL_HUA_GONG"

        items = HeluoGuidanceEngine()._build_actions([_A()], "NORMAL")
        trend = [i for i in items if i.title == "把握当前趋势"]
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0].source_ref,
                         "HELUO_RULES::HELUO_AUTH_HL_HUA_GONG")


if __name__ == "__main__":
    unittest.main()