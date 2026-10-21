"""批次 G 守卫：全库不再有自造副本表、不再有同名不同义的符号

用户口径：「如果八字排盘有的就不要再自造表了，容易出问题和重复计算导致引擎计算增大」。

═══════════════════════════════════════════════════════════════════════
本批消掉的实据（scan_dup.py 逐项比对值，不是靠印象）
═══════════════════════════════════════════════════════════════════════

  A. 错卦（先天方位对宫）**抄了 4 份**，内容完全相同：
     guajie / yuan_qi / hexagram._OPPOSITE_TRIGRAM / hua_gong.QIANXI_DUKONG
  B. ⚠ hua_gong.OPPOSITE_TRIGRAM 与上面**同名不同义**（化工相反·四季对宫，
     仅 4 项）。对乾/坤/艮/巽 取 .get() 直接返回 None。
     → 谁 `from … import OPPOSITE_TRIGRAM` 拿错了就是**静默判错**。
  C. 二十四节气抄了 3 份（jiegua.JIEQI_24 / jiehhou.SOLAR_TERMS /
     yue_ling_shu_ge.JIE_QI_ORDER）。
  D. 五行生克抄了 2 份（hexagram_state.ELEMENT_* / hua_gong._WU_*）。

**守卫思路**：绝大多数是「同一性」断言（`assertIs`），不是内容断言。
内容断言只能证明此刻相等，证明不了「它们是同一份、不会各改各的」——
而各改各的正是这类副本表的真正危害。
"""
from __future__ import annotations

import ast
import io
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"
_MODS = ("guajie", "yuan_qi", "hexagram", "hexagram_state", "hua_gong",
         "jiegua", "jiehhou", "yue_ling_shu_ge")


class TestSingleSourceTables(unittest.TestCase):
    """A / C / D：三组副本表已归一。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo import (guajie, hua_gong, hexagram,
                                           hexagram_state, jiegua, jiehhou,
                                           yuan_qi, yue_ling_shu_ge)
        cls.m = dict(guajie=guajie, yuan_qi=yuan_qi, hexagram=hexagram,
                     hexagram_state=hexagram_state, hua_gong=hua_gong,
                     jiegua=jiegua, jiehhou=jiehhou,
                     yue_ling=yue_ling_shu_ge)

    # ── A. 错卦 ─────────────────────────────────────────────
    def test_qianxi_dukong_single_object_everywhere(self):
        src = self.m["hexagram_state"].QIANXI_DUKONG
        self.assertIs(self.m["guajie"].QIANXI_DUKONG, src)
        self.assertIs(self.m["yuan_qi"].QIANXI_DUKONG, src)
        self.assertIs(self.m["hua_gong"].QIANXI_DUKONG, src)
        self.assertIs(self.m["hexagram"]._QIANXI_DUKONG, src)

    def test_no_module_still_defines_a_dukong_dict_literally(self):
        """任何模块都不该再出现「错卦字面量」——那是重新分叉的开始。

        注意用的是 ast.unparse 后的代码：那一步会把引号统一成单引、
        并规整空格，故此处按单引比对；断言的是「代码里还有没有字面量」，
        与注释文案无关（_strip 已剥掉注释与文档字符串）。
        """
        pairs = ("'乾': '坤'", "'坤': '乾'", "'震': '巽'", "'艮': '兑'")
        for mod in ("guajie", "yuan_qi", "hexagram", "hua_gong"):
            code = _strip(io.open(self.m[mod].__file__, encoding="utf-8").read())
            for lit in pairs:
                self.assertNotIn(lit, code,
                                 "%s.py 里又出现了错卦字面量 %s —— 副本又分叉了"
                                 % (mod, lit))

    def test_no_module_still_defines_jieqi_24_literally(self):
        """二十四节气序全库只许有一处字面量（jiegua）。

        ⚠ 不能只查某一个节气名：`JIE_GUA_QUOTE`（原典节卦段引文）和
        `is_bi_gua` 的二分日名单里出现「小寒」等是**合法**的。
        故此处只认「连续两个节气名构成的序列字面量」——那才是抄了一遍表。
        """
        seq = "'冬至', '小寒'"
        for mod in ("jiehhou", "yue_ling_shu_ge", "hua_gong"):
            import importlib
            m = importlib.import_module(
                "tongshu.engines.heluo.%s" % mod)
            code = _strip(io.open(m.__file__, encoding="utf-8").read())
            self.assertNotIn(seq, code,
                             "%s 里又抄了一份二十四节气序列字面量" % mod)

    def test_solar_terms_three_names_are_one_object(self):
        src = self.m["jiegua"].JIEQI_24
        self.assertIs(self.m["jiehhou"].SOLAR_TERMS, src)
        self.assertIs(self.m["yue_ling"].JIE_QI_ORDER, src)
        self.assertIs(self.m["hua_gong"]._JQ_ORDER, src)

    def test_wuxing_sheng_ke_single_object(self):
        hs = self.m["hexagram_state"]
        self.assertIs(self.m["hua_gong"]._WU_SHENG, hs.ELEMENT_GENERATES)
        self.assertIs(self.m["hua_gong"]._WU_KE, hs.ELEMENT_OVERCOMES)


class TestNoSameNameDifferentMeaning(unittest.TestCase):
    """B：同名不同义是本批最危险的一条。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo import hua_gong
        cls.HG = hua_gong

    def test_opposite_trigram_symbol_is_gone_from_the_whole_engine(self):
        """改完之后，全库不得再有任何模块导出 OPPOSITE_TRIGRAM。"""
        import importlib
        for name in _MODS:
            mod = importlib.import_module(
                "tongshu.engines.heluo.%s" % name)
            self.assertFalse(hasattr(mod, "OPPOSITE_TRIGRAM"),
                             "%s 仍导出 OPPOSITE_TRIGRAM —— 歧义名没消干净" % name)

    def test_the_two_tables_are_distinct_and_correctly_named(self):
        self.assertEqual(self.HG.HUAGONG_FAN_GUA,
                         {"坎": "离", "离": "坎", "兑": "震", "震": "兑"})
        self.assertEqual(len(self.HG.QIANXI_DUKONG), 8)
        self.assertNotIn("乾", self.HG.HUAGONG_FAN_GUA,
                         "化工相反表只收四季四卦，混入乾即错")

    def test_get_on_huagong_fan_never_silently_returns_none(self):
        """旧表（四季对宫）对乾/坤/艮/巽 取 .get() 返回 None → 静默判错。
        现在这两个概念各有各的表，且**不该**再从一个表里取另一个概念的值。
        """
        from tongshu.engines.heluo import guajie
        self.assertEqual(guajie.QIANXI_DUKONG.get("乾"), "坤")
        # 化工相反本就不含乾：调用方必须先判存在，而不是默默拿到 None
        self.assertNotIn("乾", self.HG.HUAGONG_FAN_GUA)

    def test_hua_gong_self_check_still_validates_the_fan_table(self):
        """改名后导入期自校验必须仍在、且校验的是新名那张表。"""
        code = _strip(io.open(self.HG.__file__, encoding="utf-8").read())
        flat = re.sub(r"\s+", "", code)
        self.assertIn("HUAGONG_FAN_GUA.get(gua)==fan", flat)
        self.assertIn("set(names)==set(HUAGONG_FAN_GUA)", flat)


def _strip(text: str) -> str:
    """只留可执行代码：剥三引号文档字符串与 ``#`` 注释。"""
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            b = node.body
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                node.body = b[1:] or [ast.Pass()]
    return "\n".join(ast.unparse(tree).split("\n"))


if __name__ == "__main__":
    unittest.main()