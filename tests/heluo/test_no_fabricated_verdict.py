"""防伪造判词 / 防节卦爻名分叉（2026-10-07）

两处都是「起例卷对照表」核查中实测发现的 P0：

1. **伪造判词**：`judge_shu_xiong` 原无条件输出
   「判词：数凶者身亡，但**德小者不能当之**」——
   经 20158 行全库检索，「德小者」「不能当之」**零命中**，
   系拼凑半句伪造，且已污染 `compose_guajie` 的下游 summary。
2. **节卦爻名分叉**：`guajie._JIE_GUA_START` 把离卦第三爻写成「九三」、
   兑卦第三爻写成「六三」，均与原典 L1492 不符
   （原典作「**九二大暑**」「**九三霜降**」），
   且这是**生产在跑**的路径（`judge_jiehua_gong`）。
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

_ROOT = Path(__file__).resolve().parents[2]
_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _corpus_texts():
    """全库文本语料（data/guajie_raw + 原著全文），用于伪造判词检测。"""
    texts = {}
    base = _ROOT / "src" / "heluo_engine" / "orig"
    if base.exists():
        for p in base.glob("*.txt"):
            with io.open(p, encoding="utf-8") as f:
                texts[p.name] = f.read()
    if _ORIGINAL.exists():
        with io.open(_ORIGINAL, encoding="utf-8") as f:
            texts[_ORIGINAL.name] = f.read()
    return texts


class TestNoFabricatedVerdict(unittest.TestCase):
    """输出里的判词必须在原典中找得到。"""

    def setUp(self):
        self.corpus = "\n".join(_corpus_texts().values())
        if not self.corpus:
            self.skipTest("语料不可用")

    def test_fragments_traceable_to_source(self):
        """★ 2026-10-24 **订正**：这两个半句**不是伪造** —— 它们是原典原句。

        旧断言是「全库零命中 ⇒ 伪造的铁证」。该断言**成立过**（当时包内
        切片**不含《河洛理数》卷二经文** ⇒ 检索不到），
        但 2026-10-24 补切经文（``orig/河洛理数_年卦月卦切片.txt`` S8/S10 段）
        后，在**卷二经文·震卦**断语里查到：

            「…山身亡但**德小者不能之**」  （OCR 形态；正字疑为「德小者不能当之」，
            「当」字被 OCR 漏识）

        ⇒ 「零命中」只是**切片缺口**，不是「原典没有」——
        这正是「不得用『包内检索不到』当作『原典没有』」的又一次实证。

        现断言改为：**这两个词必须能在包内经文切片回查**（防止将来误删真原典），
        且**不得**出现在别处（说明它只属这一条经文语境）。
        """
        corpus = self.corpus
        for frag in ("德小者", "不能之"):
            self.assertIn(frag, corpus,
                          f"「{frag}」竟在语料中查不到 —— 它是卷二经文震卦的原句"
                          "（正字「德小者不能当之」），不得误删真原典")
        # 它只出现在这一处语境：不得被引擎当成**通用**数凶判词输出
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        joined = " ".join(judge_shu_xiong(40, 60, 11).evidence)
        self.assertNotIn("德小者", joined,
                         "数凶判词不得直接输出经文里的「德小者不能当之」"
                         "（那是震卦的条件式断语，脱离卦语境即失真）")
        self.assertNotIn("不能当之", joined,
                         "数凶判词不得直接输出经文里的「德小者不能当之」")

    def test_shu_xiong_cites_real_original_lines(self):
        """数凶判词须引原典明文（L2274 / L2292 / L741），不拼造整句。"""
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        joined = " ".join(judge_shu_xiong(40, 60, 11).evidence)
        self.assertIn("L2274", joined, "缺原典 L2274 引文")
        self.assertIn("L2292", joined, "缺原典 L2292 引文")

    def test_source_comment_does_not_call_it_fabricated(self):
        """源码注释**不得**再把这两句称作「伪造」——它有原典出处。"""
        src = (_ROOT / "src" / "heluo_engine" / "engines" / "heluo" /
               "guajie.py").read_text(encoding="utf-8")
        for frag in ("德小者", "不能当之"):
            for line in src.splitlines():
                if frag in line and ("伪造" in line or "证伪" in line
                                     or "拼凑" in line):
                    raise AssertionError(
                        f"guajie.py 仍把「{frag}」称作伪造/拼凑 —— "
                        "它实为《河洛理数》卷二经文震卦的原句（补切经文后可见）")

    def test_shu_xiong_no_longer_emits_fabricated_line(self):
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        ev = judge_shu_xiong(40, 60, 11).evidence      # 阳月令 → 数凶
        joined = " ".join(ev)
        self.assertNotIn("德小者", joined, "仍在输出伪造判词")
        self.assertNotIn("不能当之", joined, "仍在输出伪造判词")

    def test_summary_no_longer_emits_fabricated_line(self):
        """下游 summary 曾被污染，一并守住。

        只检查**可执行代码行**（剔除注释与 docstring），
        因为注释里为说明「此句系伪造」而引用原句是必要且正确的。
        """
        from heluo_engine.engines.heluo import guajie as gj
        src = io.open(gj.__file__, encoding="utf-8").read()
        code_only = []
        for line in src.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
                continue
            code_only.append(line)
        joined = "\n".join(code_only)
        self.assertNotIn("数凶者身亡，但德小者不能当之", joined,
                         "伪系判词仍在可执行代码中")


class TestJieGuaUsesSingleSource(unittest.TestCase):
    """节卦爻名必须来自 jiegua.JIE_GUA_TABLE，不得在 guajie 里另抄一份。"""

    def test_known_wrong_yao_names_are_gone(self):
        """离卦第三爻曾误作「九三」，兑卦第三爻曾误作「六三」。"""
        from heluo_engine.engines.heluo import guajie as gj
        src = io.open(gj.__file__, encoding="utf-8").read()
        # 不得再有内联的爻名序列字面量
        for bad in ('"初九", "六二", "九三", "九四", "六五", "上九"',
                    '"初九", "九二", "六三", "九四", "九五", "上六"'):
            self.assertNotIn(bad, src,
                             f"guajie.py 仍内联节卦爻名序列：{bad}（应改用 jiegua 表）")

    def test_output_matches_original_yao_names(self):
        """实测：几个出生日应产出原典的爻名。"""
        from heluo_engine.engines.heluo.guajie import judge_jiehua_gong
        cases = [
            ("2026-06-25", "夏至·初九爻"),     # 离卦初爻
            ("2026-07-10", "小暑·六二爻"),     # 离卦二爻（原典「六二小暑」）
            ("2026-12-30", "冬至·初六爻"),     # 坎卦初爻
            ("2026-01-10", "小寒·九二爻"),     # 坎卦二爻
        ]
        for date_str, expect in cases:
            ev = judge_jiehua_gong(date_str)
            self.assertTrue(any(expect in e for e in ev),
                            f"{date_str} 应含「{expect}」，实得 {ev}")

    def test_third_yao_is_original(self):
        """原典离卦「大暑」= 九二，兑卦「霜降」= 九三——这两条曾写错。"""
        from heluo_engine.engines.heluo.jiegua import JIE_GUA_TABLE
        li = [e for e in JIE_GUA_TABLE if e.trigram == "离"]
        dui = [e for e in JIE_GUA_TABLE if e.trigram == "兑"]
        self.assertEqual(li[2].yao_name, "九二", "原典「离…九二大暑」")
        self.assertEqual(li[2].jq_name, "大暑")
        self.assertEqual(dui[2].yao_name, "九三", "原典「兑…九三霜降」")
        self.assertEqual(dui[2].jq_name, "霜降")

    def test_jiehua_evidence_mentions_superconnect_caveat(self):
        """原典「卦爻有超接」——代码里的 15 日均分只是近似，须有登记。"""
        from heluo_engine.engines.heluo import guajie as gj
        src = io.open(gj.__file__, encoding="utf-8").read()
        self.assertIn("超接", src,
                      "均分近似必须注明原典「卦爻有超接」的警告")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
