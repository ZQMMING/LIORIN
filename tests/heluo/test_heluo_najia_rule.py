# -*- coding: utf-8 -*-
"""纳甲**逐字回查**守卫（2026-10-23）。

**为什么不做公理重算**
--------------------

判词数据里的**纳甲**（每卦六爻配地支）由卦头断语「纳甲是：…」解析而来
（`guajie._parse_gua_header`）。曾尝试用纳甲公理
（「八纯卦各有六位纳甲；任一卦 = 下卦纳甲前三位 + 上卦纳甲后三位」）重算比对，
**被原典本身否证** —— 原典的各卦卦头自说自话，至少 7 卦与该规则不符：

| 卦 | 原典卦头（逐字） | 与「下前3+上后3」 |
|---|---|---|
| 观（巽上坤下） | 乙未、乙巳、乙卯、**辛巳、辛卯、辛丑** | 外巽应作 辛未、辛巳、辛卯 ✗ |
| 贲（艮上离下） | 己卯、己丑、己亥、**丙寅、丙子、丙戌** | 外艮应作 丙戌、丙子、丙寅（序倒）✗ |
| 小过（兑上艮下） | 丙辰、丙午、丙申、**庚午、庚申、庚戌** | 外兑应作 丁亥、丁酉、丁未 ✗ |
| 比 / 小畜 / 夬 | 各只列 3 条 +「借用」六条 | 条数不同 ✗ |
| 损（艮上兑下） | 丁巳、丁卯、丁丑、**丙戊**、丙子、丙寅 | 「丙**戊**」是**讹字**（地支无戊，当作丙戌）→ 引擎按合法干支过滤 → 损只存 5 条 ✗ |

⇒ **原典纳甲表既不统一、又有讹字**。引擎的处理是**忠实照录 + 只收合法干支**
（不臆造、不订正），故守卫只能是**逐字回查**：每条纳甲干支必须在该卦的原典
卦头里逐字出现。**不做公理修正 —— 订正原典是另一件事，须单独立据。**

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

#: 合法干支（地支无「戊」—— 「丙戊」是原典讹字）
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_GANZHI_RE = re.compile(rf"^[{_GAN}][{_ZHI}]$")

#: 已知原典纳甲不一致（**留档，不掩盖**）：卦名 → (原典卦头原文片段, 说明)
KNOWN_INCONSISTENCIES = {
    "观": "原典外巽作「辛巳、辛卯、辛丑」，与八纯卦合成规则（辛未、辛巳、辛卯）不符",
    "贲": "原典外艮作「丙寅、丙子、丙戌」，与合成规则（丙戌、丙子、丙寅）序倒",
    "小过": "原典外兑作「庚午、庚申、庚戌」，与合成规则（丁亥、丁酉、丁未）不符",
    "比": "原典只列内坤三条（乙未、乙巳、乙卯）+「借用」六条，条数与其余卦不同",
    "小畜": "原典只列内乾三条（甲子、甲寅、甲辰）+「借用」六条",
    "夬": "原典只列内乾三条（甲子、甲寅、甲辰）+「借用」六条",
    "损": "原典「丙戌」讹作「丙戊」（地支无戊）→ 引擎按合法干支过滤，损只存 5 条",
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
        # 损：讹字「丙戊」不得被当作合法干支收进来
        self.assertNotIn("丙戊", list(self.data["损"].najia or []),
                         "讹字「丙戊」不得收进纳甲")

    def test_header_parse_covers_all_hexagrams(self):
        """每卦的纳甲都应被解析出来（不漏）。"""
        empty = [short for short, g in self.data.items() if not (g.najia or [])]
        self.assertEqual(empty, [],
                         f"以下卦未解析出纳甲（卦头格式可能变了）：{empty}")


if __name__ == "__main__":
    unittest.main()
