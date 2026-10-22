# -*- coding: utf-8 -*-
"""纳甲**逐字回查**守卫（2026-10-23；2026-10-24 六源对拍后修订定性）。

**为什么不做公理重算**
--------------------

判词数据里的**纳甲**（每卦六爻配地支）由卦头断语「纳甲是：…」解析而来
（`guajie._parse_gua_header`）。曾尝试用纳甲公理
（「八纯卦各有六位纳甲；任一卦 = 下卦纳甲前三位 + 上卦纳甲后三位」）重算比对，
**被原典本身否证** —— 6 卦与该规则不符：

| 卦 | 原典卦头（逐字） | 与「下前3+上后3」 |
|---|---|---|
| 观（巽上坤下） | 乙未、乙巳、乙卯、**辛巳、辛卯、辛丑** | 外巽应作 辛未、辛巳、辛卯 ✗ |
| 贲（艮上离下） | 己卯、己丑、己亥、**丙寅、丙子、丙戌** | 外艮应作 丙戌、丙子、丙寅（序倒）✗ |
| 损（艮上兑下） | 丁巳、丁卯、丁丑、**丙戊**、丙子、丙寅 | 「丙**戊**」是**讹字**（地支无戊，当作丙戌）→ 引擎按合法干支过滤 → 损只存 5 条 ✗ |
| 比 / 小畜 / 夬 | 卦头「纳甲是」段只列**内卦 3 条** | 外卦 3 条只见于其后的「借用…」段（影印本逐页核实：比=借用段后 3 条即戊申、戊戌、戊子）✗ 条数不同 |

⇒ **《河洛真数》此本的纳甲表与京房标准不完全一致**。引擎的处理是
**忠实照录 + 只收合法干支**（不臆造、不订正），故守卫只能是**逐字回查**：
每条纳甲干支必须在该卦的原典卦头里逐字出现。
**不做公理修正 —— 订正原典是另一件事，须单独立据。**

**2026-10-24 六源对拍后的定性修订（重要）**
------------------------------------------------
此前本文档写「原典纳甲表既不统一、又有讹字」，**表述不准**，现更正为：

* 「辛巳、辛卯、辛丑」「丙寅、丙子、丙戌」「丙戊」三处**并非本地 OCR 讹误** ——
  已用**影印原页**逐字核实（《河洛真数·续修四库全书本》PDF 第 241 页「观」、
  第 322 页「损」）：**原书即如此**。本地切片、diancang 清本、
  影印本转录文本、`河洛真数——原著.txt` **四源逐字一致**。
* 《河洛理数》（**另一部书**，非《河洛真数》）的卦解（3door.org / Daum Cafe）
  在这三处作「辛未、辛巳、辛卯」「丙戌、丙子、丙寅」「丙戌」——
  与京房标准一致。即：**《河洛真数》天一阁本**与**《河洛理数》整理本**
  在这 3 处存在异文，属**版本异文**，不是本地数据失真。
* 另：此前文档称「小过 外兑应作 丁亥、丁酉、丁未」——**该条有误**。
  小过为**震上艮下**（兑宫四世卦），其外卦是**震**（庚午、庚申、庚戌），
  原典作「丙辰、丙午、丙申、庚午、庚申、庚戌」**与京房标准一致**，并无不一致。
  现已从不一致清单中移除。

完整对拍过程、六源清单与逐页影印核验见
`docs/heluo/纳甲异文多源对拍_20261024.md`。

**覆盖**：64 卦全部纳甲项（60 卦 × 6 条 + 3 卦 × 3 条 + 1 卦 × 5 条 = 374 条）
+ 形态守卫 + **原典不一致留档**（KNOWN_INCONSISTENCIES，逐条注明，不掩盖）。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import guajie as gj

_ROOT = Path(__file__).resolve().parents[2]
_RAW = _ROOT / "data" / "heluo" / "guajie_data.json"

#: 合法干支（地支无「戊」—— 「丙戊」是原书讹字）
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_GANZHI_RE = re.compile(rf"^[{_GAN}][{_ZHI}]$")

#: 已知原典不一致（**留档，不掩盖**）：卦名 → 说明
KNOWN_INCONSISTENCIES = {
    "观": "《河洛真数》天一阁本外巽作「辛巳、辛卯、辛丑」，与京房标准"
          "（辛未、辛巳、辛卯）不符；《河洛理数》整理本作标准写法。"
          "影印本第241页已逐字核实为原书如此。",
    "贲": "《河洛真数》天一阁本外艮作「丙寅、丙子、丙戌」，与京房标准"
          "（丙戌、丙子、丙寅）序倒；《河洛理数》整理本作标准写法。",
    "损": "原书「丙戌」讹作「丙戊」（地支无戊）→ 引擎按合法干支过滤，损只存 5 条。"
          "影印本第322页已逐字核实为原书如此；《河洛理数》整理本作「丙戌」。",
    "比": "原典「纳甲是」段只列内坤三条（乙未、乙巳、乙卯），外卦三条"
          "（戊申、戊戌、戊子）见于其后「借用…」段后 3 位。",
    "小畜": "原典「纳甲是」段只列内乾三条（甲子、甲寅、甲辰），外卦三条"
            "（辛未、辛巳、辛卯）见于其后「借用…」段后 3 位。",
    "夬": "原典「纳甲是」段只列内乾三条（甲子、甲寅、甲辰），外卦三条"
          "（丁亥、丁酉、丁未）见于其后「借用…」段后 3 位。",
}


def _raw_lines() -> dict[str, list[str]]:
    import json
    raw = json.loads(_RAW.read_text(encoding="utf-8"))
    return {g["name"]: [str(x) for x in (g.get("lines") or [])] for g in raw}


class TestNajiaVerbatim(unittest.TestCase):
    """纳甲逐字来自原典卦头。"""

    @classmethod
    def setUpClass(cls):
        cls.data = gj.load_guajie_data()
        cls.raw = _raw_lines()

    def test_najia_items_appear_verbatim_in_header(self):
        total = 0
        for short, g in self.data.items():
            header = " ".join(self.raw.get(short, []))
            for item in (g.najia or []):
                with self.subTest(gua=short, najia=item):
                    total += 1
                    self.assertIn(item, header,
                                  f"{short} 的纳甲项「{item}」未在原典卦头中逐字出现")
        self.assertEqual(total, 374, "应覆盖 374 条纳甲项（60×6 + 3×3 + 1×5）")

    def test_najia_well_formed(self):
        """形态守卫：每条都必须是合法干支（讹字如「丙戊」应被拒收）。"""
        for short, g in self.data.items():
            for item in (g.najia or []):
                with self.subTest(gua=short, najia=item):
                    self.assertRegex(item, _GANZHI_RE,
                                     f"{short} 纳甲项非合法干支：{item}")

    def test_known_inconsistencies_documented(self):
        """原典的纳甲不一致必须**在案**（改动前先更新留档，不得静默消失）。"""
        for short, note in KNOWN_INCONSISTENCIES.items():
            with self.subTest(gua=short):
                g = self.data.get(short)
                self.assertIsNotNone(g, f"{short} 应在引擎数据中")
                self.assertTrue(note, "每条不一致须有说明")
        # 损：原书讹字「丙戊」不得被当作合法干支收进来
        self.assertNotIn("丙戊", list(self.data["损"].najia or []),
                         "讹字「丙戊」不得收进纳甲")

    def test_known_inconsistencies_no_false_positive(self):
        """2026-10-24 修订：旧清单误把「小过」列为不一致，实为原典正确。

        小过为**震上艮下**（兑宫四世卦），外卦是震（庚午、庚申、庚戌），
        原典作「丙辰、丙午、丙申、庚午、庚申、庚戌」**与京房标准一致**。
        此条已移出不一致清单 —— 若有人日后把它加回，此守卫会失败。
        """
        self.assertNotIn("小过", KNOWN_INCONSISTENCIES,
                         "小过纳甲与京房标准一致，不属不一致项")

    def test_jieyong_segment_parsed_not_dropped(self):
        """「借用…」段须被解析出来（2026-10-24：此前整段被静默丢弃）。

        旧正则 `[^，。；]{2,60}` 在第一个逗号处截断，而「借用」段前正好跟一个逗号，
        于是借用干支从未进入引擎。现已单列为 `GuaDuan.jieyong`。
        """
        with_jieyong = {k: v.jieyong for k, v in self.data.items() if v.jieyong}
        self.assertEqual(len(with_jieyong), 28,
                         f"应解析出 28 卦的借用段，实得 {len(with_jieyong)}")
        total = sum(len(v) for v in with_jieyong.values())
        self.assertEqual(total, 105, f"借用干支应共 105 条，实得 {total}")
        # 借用干支同样必须是合法干支
        for short, items in with_jieyong.items():
            for item in items:
                with self.subTest(gua=short, jieyong=item):
                    self.assertRegex(item, _GANZHI_RE,
                                     f"{short} 借用项非合法干支：{item}")
        # 借用段不得混入本卦 najia（原典语义：借用别卦之甲）
        for short, g in self.data.items():
            overlap = set(g.najia or []) & set(g.jieyong or [])
            self.assertEqual(overlap, set(),
                             f"{short} 的借用干支与本卦纳甲重复：{sorted(overlap)}")

    def test_three_short_guas_keep_outer_trigram_in_jieyong(self):
        """比 / 小畜 / 夬：外卦 3 条只见于借用段后 3 位（影印本逐页核实）。"""
        expected = {
            "比": ["戊申", "戊戌", "戊子"],
            "小畜": ["辛未", "辛巳", "辛卯"],
            "夬": ["丁亥", "丁酉", "丁未"],
        }
        for short, tail in expected.items():
            with self.subTest(gua=short):
                g = self.data[short]
                self.assertEqual(len(g.najia or []), 3,
                                 f"{short} 纳甲段应只有内卦 3 条")
                self.assertEqual(list(g.jieyong or [])[-3:], tail,
                                 f"{short} 借用段后 3 条应为其外卦纳甲")

    def test_header_parse_covers_all_hexagrams(self):
        """每卦的纳甲都应被解析出来（不漏）。"""
        empty = [short for short, g in self.data.items() if not (g.najia or [])]
        self.assertEqual(empty, [],
                         f"以下卦未解析出纳甲（卦头格式可能变了）：{empty}")


if __name__ == "__main__":
    unittest.main()
