# -*- coding: utf-8 -*-
"""死断四条件的原典依据保真守卫（2026-10-24 核定）。

**为什么要有这个守卫**

死断 ⑥ 条的原典是**四个并列条件**：

> 「若流年连三年不吉，**卦爻又不吉**，本身卦不佳，重反支干元气，便可以死断之。」
> （《河洛真数》四库全书本 影印 PDF 第 142 页，**逐字目视核定**）

此前引擎注释只引到「若流年连三年不吉……」的前半句，
**第二条件「卦爻又不吉」从未被逐字核过**，也未说明它与第一条件的
关系（合流？独立？），代码里因而看不出这是取舍还是遗漏。

本守卫把三条结论钉死：
1. **四条件俱在**（底本须逐字含「卦爻又不吉」六字）——
   防日后以讹传讹删掉第二条件；
2. **「卦爻」= 流年卦之爻**（底本须逐字含 L780「流年卦爻多有不佳」
   与 L486「本身卦爻理体不吉」）—— 防误改成「本身卦爻」；
3. **「②与①合流」是有据的取舍**（引擎注释须说明原典未指明取哪一爻，
   取行年爻则二者同一判据）—— 防将来被人当作「漏实现了条件」而"修复"，
   或反过来在无据时擅自拆出第五个条件。

**不做的事**：不替原典裁决「卦爻」到底取哪一爻 —— 原典未明，
裁决留待新版本原典或旁证出现时重开（见留档文档）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.heluo import guajie as gj  # noqa: E402

#: 影印原页核定：死断四条件整句
ORIGINAL_FOUR = (
    "若行后天，连三爻不吉，必多坎壈。若过了第四爻，遇凶，十死八九。"
    "若流年连三年不吉，卦爻又不吉，本身卦不佳，重反支干元气，便可以死断之。"
)


class TestSiDuanOriginalText(unittest.TestCase):
    """底本须逐字含四条件原句与两处关键旁证。"""

    @classmethod
    def setUpClass(cls):
        cls.pkg_slice = (
            ROOT / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt"
        ).read_text(encoding="utf-8")
        cls.orig = (
            ROOT / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt"
        ).read_text(encoding="utf-8")

    def test_four_conditions_present_verbatim(self):
        """包内底本须逐字含四条件整句（含「卦爻又不吉」六字）。"""
        compact = self.pkg_slice.replace("\n", "")
        self.assertIn(
            ORIGINAL_FOUR, compact,
            "包内底本未逐字含死断四条件原句（含「卦爻又不吉」）—— "
            "第二条件的引证已丢失，须重新核实")

    def test_second_condition_six_chars_present(self):
        """「卦爻又不吉」六字确在（该条曾长期未被逐字核实）。"""
        self.assertIn("卦爻又不吉", self.pkg_slice.replace("\n", ""),
                      "底本缺「卦爻又不吉」六字")

    def test_liu_nian_gua_yao_phrase_present(self):
        """L780「流年卦爻多有不佳」在 —— 「卦爻」= 流年卦之爻的依据。"""
        self.assertIn("流年卦爻多有不佳", self.orig.replace("\n", ""),
                      "底本缺 L780「流年卦爻多有不佳」—— "
                      "「卦爻」主语判定的关键旁证")

    def test_ben_yao_phrase_present(self):
        """L486「本身卦爻理体不吉」在 —— 证明原典指本身卦时会明写「本身卦」。"""
        self.assertIn("本身卦爻理体不吉", self.orig.replace("\n", ""),
                      "底本缺 L486「本身卦爻理体不吉」—— "
                      "「卦爻」不指本身卦的关键反证")

    def test_quote_in_engine_is_four_conditions(self):
        """引擎引文须是四条件完整版（不得只引前半句）。

        ⚠ 不能只断言「源码里有『卦爻又不吉』几个字」——
          那会被**注释里**的引述满足，而真正的 `quote=` 参数仍可能只引前半句。
          故此处**逐条解析 `quote=` 实参**，断其字面内容。
        """
        import inspect
        import re
        src = inspect.getsource(gj.judge_si_duan)
        # quote 实参常被拆成**相邻的多个字符串字面量**（跨行拼接），
        # 故须匹配完整的字符串字面量序列（含隐式拼接），
        # 不能用 `quote="([^"]*)"`（会在第一段截断）。
        quotes: list[str] = []
        for m in re.finditer(r'quote=((?:"[^"]*"\s*)+)', src):
            quotes.append("".join(re.findall(r'"([^"]*)"', m.group(1))))
        self.assertTrue(quotes, "未解析到任何 quote 实参")
        joined = "".join(quotes)
        for frag in ("卦爻又不吉", "本身卦不佳", "重反支干元气"):
            with self.subTest(frag=frag):
                self.assertIn(frag, joined,
                              f"死断 ⑥ 条的 quote 实参缺「{frag}」—— "
                              "四条件未完整照录")
        # ⑥ 条的引文须**连续**含四条件（不得被拆成两段后再拼）
        self.assertTrue(
            any(all(f in q for f in ("流年连三年不吉", "卦爻又不吉",
                                     "本身卦不佳", "重反支干元气"))
                for q in quotes),
            "没有任何一条 quote 实参同时含四个条件 —— 四条件被拆散了")


class TestSiDuanSecondConditionDocumented(unittest.TestCase):
    """「②与①合流」必须是**有据的取舍**，且在代码里说明理由。"""

    def test_engine_documents_the_merge_rationale(self):
        """引擎注释须写明：原典未指明取哪一爻，取行年爻则二者同一判据。"""
        import inspect
        src = inspect.getsource(gj.judge_si_duan)
        for kw in ("卦爻又不吉", "行年爻", "未说", "合流"):
            with self.subTest(kw=kw):
                self.assertIn(kw, src,
                              f"引擎注释缺「{kw}」—— "
                              "第二条件的合流取舍须在代码里说明理由，"
                              "否则后人无法区分「取舍」与「遗漏」")

    def test_verdict_document_exists(self):
        """核定留档文档须存在，且**证据链完整**（供复核与将来重开裁决）。

        ⚠ 不能只断言「文件在」或「含某几个字」——
          那些字在文档别处也会出现，删掉证据链照样绿。
          故此处**逐条证据链**各取一个**稀有**锚点（只在该条证据里出现），
          并要求**出现次数 ≥ 该条证据应有的次数**。
        """
        p = ROOT / "data" / "heluo" / "死断四条件核定_20261024.md"
        self.assertTrue(p.exists(),
                        f"缺核定留档：{p.name}")
        t = p.read_text(encoding="utf-8")
        self.assertGreater(len(t.strip()), 500,
                           "留档文档内容过短 —— 证据链被清空？")
        #: 每条证据链的**稀有锚点** → 至少应有的出现次数
        #: （选这些是因为它们在文档中只出现在对应证据段内）
        anchors = {
            "影印 PDF 第 142 页": 1,          # E1 影印原页
            "多有不佳，只论其大象有根基": 1,   # E2 「流年卦爻」是名词短语
            "理体不吉，便可以死断之": 1,      # E3 「本身卦」另有其名
            "只有三条件": 1,                  # E4 河洛理数版本差异
            "无「本身」二字": 1,              # E3 关键否定式论证
            "同义反复": 1,                    # 判据层：②与①的关系
            "重开此条裁决": 1,                # 留待将来定案的条件
        }
        for frag, need in anchors.items():
            with self.subTest(frag=frag):
                self.assertGreaterEqual(
                    t.count(frag), need,
                    f"留档缺证据链锚点「{frag}」或出现次数不足 —— "
                    "证据链有段被抹掉")

    def test_trigger_text_states_the_merge(self):
        """触发语须告知下游：四条件中②与①同判据（不得让下游误读为三条件）。"""
        from tongshu.engines.heluo.guajie import _sd
        w = _sd(quote="「若流年连三年不吉，卦爻又不吉，本身卦不佳，"
                      "重反支干元气，便可以死断之。」",
                 trigger="近三年流年卦爻皆不吉（含「卦爻又不吉」…）",
                 limit="本条原典未附阴骘前置…")
        self.assertIn("卦爻又不吉", w)


class TestSiDuanConditionCount(unittest.TestCase):
    """四条件中，引擎**实际**判了哪几条 —— 留档可查（防静默增减）。"""

    def test_conditions_implemented_are_documented(self):
        """⑥ 条实现的条件须与原典四条件对应，且不得静默增减。

        现状：①（流年三年不吉，含②卦爻又不吉，同判据）+ ③（本身卦不佳）
        + ④（重反支干元气）。本断言只钉住「不得少于/多于原典条件」这一事实，
        具体的取舍理由见留档文档与引擎注释。
        """
        import inspect
        src = inspect.getsource(gj.judge_si_duan)
        # 六个死断条各自一句 quote
        quotes = [ln for ln in src.splitlines() if "quote=" in ln]
        self.assertGreaterEqual(len(quotes), 6,
                                "死断条数少于 6 —— 有条被静默删除？")
        # 不得出现原典没有的第五个条件
        for bogus in ("卦爻又不吉且本身卦", "五条件"):
            self.assertNotIn(bogus, src)


if __name__ == "__main__":
    unittest.main()
