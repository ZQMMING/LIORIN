# -*- coding: utf-8 -*-
"""河洛判词层「原典引文」守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

河洛判词层大量输出带「（原典：…）」标注，宣称该句出自《河洛真数》。
这些标注若与原典不符 —— 措辞被改写、章节名颠倒、乃至**自撰却标原典** ——
输出层就会**以原典的权威**呈现一句并非原典的话，比不标更坏。

2026-10-24 全面审计时实测发现两处：
* 章节名「**元气化工有无论**」→ 原典是「**化工元气有无论**」（词序颠倒，9 处）。
  已修（`guajie.py` 9 处）。
* 「**三者俱反方不可保**」→ 这是引擎**自撰的概括语**；
  原典实为「若运既反，流年又反，数又反，其人不可保矣」。
  仍标注「（原典：…）」→ 属**自撰冒引**，须改标注（见 KNOWN_SELF_WRITTEN）。

本守卫把「凡标（原典：X）者，X 须能在 `data/heluo/guajie_raw/` 原典切片中逐字命中」
变成可回归的断言 —— 引擎侧新增/改写任一引文而未对原典，即刻红。

**判定口径**
------------
1. 比对时**去标点与空白**（原典断语标点密集，逐字比对会误报）；
2. 引文里的 **「…」** 表示节选 → 按节选段**分别**命中即可；
3. **已知版本异文**（`KNOWN_VARIANTS`）单独列名，不阻断守卫 ——
   如「公卿节制」：包内切片是通行本「公**乡**节制」，而 1632 最古刻本作「公**卿**节制」，
   引擎用后者（2026-09-15 已定案），属**已裁决的版本异文**，不是引擎错。
4. **自撰概括语**（`KNOWN_SELF_WRITTEN`）必须**不带**「（原典：…）」标注 ——
   即：引擎仍可输出这句话，但不得宣称它是原典引文。

**覆盖**
--------
`src/tongshu/engines/heluo/*.py`（含 `relationship/`）+ `heluo_adapter.py` 里
全部「（原典：…）」标注（实测 43 处）。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

RAW = ROOT / "data" / "heluo" / "guajie_raw"
SRC = ROOT / "src" / "tongshu" / "engines" / "heluo"

#: 「（原典：…）」标注的提取
_PAREN = re.compile(r"（原典[:：]\s*([^）]{1,160})）")

#: 注释行（# 开头）须排除 —— 注释里也会写到「原标注曾写作（原典：X）」这类
#: **历史说明**，若一并扫描会把「已修掉的自撰冒引」当成现行标注而误报。
_COMMENT = re.compile(r"^\s*#")

#: 已知**版本异文**（引擎写法正确，但包内切片是另一版本）—— 键为引文，值为说明。
#: 这些不阻断守卫（引擎已按 2026-09-15 裁决采用最古刻本写法）。
KNOWN_VARIANTS: dict[str, str] = {
    "三为公卿节制": "包内切片（通行本）作「公乡节制」；1632 最古刻本作「公卿节制」，"
                    "引擎用后者（2026-09-15 定案：公乡为形近误刻）",
}

#: 已知**自撰概括语** —— 引擎可输出，但不得标「（原典：…）」。
#: 键为引文串，值为原典实情。
KNOWN_SELF_WRITTEN: dict[str, str] = {
    "三者俱反方不可保": "原典实为「若运既反，流年又反，数又反，其人不可保矣」—— "
                        "引擎这句是概括语，非原典引文",
}

#: 已知的**合法节选**（引文用「…」表示取两段，中间省略）—— 这些不是逐字连续串，
#: 守卫按「分节各自命中」判定。
_KNOWN_ELLIPSIS: set[str] = {
    "元气谓…金音人得乾兑之卦是也",
    "六为天枢…山林八极之外",
}


def _norm(s: str) -> str:
    """去全部空白与标点，只留可比较的字符。"""
    return re.sub(r"[^\w一-鿿]", "", s or "")


def _corpus() -> str:
    parts = [f.read_text(encoding="utf-8") for f in sorted(RAW.glob("*.txt"))]
    return _norm("\n".join(parts))


def _source_files() -> list[Path]:
    files = sorted(SRC.glob("*.py"))
    files += sorted(SRC.glob("relationship/*.py"))
    files.append(ROOT / "src" / "tongshu" / "engines" / "heluo_adapter.py")
    return [f for f in files if f.exists()]


class TestOriginalQuotesVerbatim(unittest.TestCase):
    """凡标「（原典：X）」者，X 须在原典切片中逐字命中。"""

    @classmethod
    def setUpClass(cls):
        cls.corpus = _corpus()
        cls.assertTrue(cls.corpus, "原典切片为空，无法做引文保真校验")
        cls.quotes: list[tuple[str, str]] = []
        for f in _source_files():
            for ln in f.read_text(encoding="utf-8").splitlines():
                if _COMMENT.match(ln):
                    continue                # 注释里的历史说明不是现行标注
                for m in _PAREN.finditer(ln):
                    q = m.group(1).strip()
                    if "{" in q:
                        # f-string 模板占位（如「{_deju_quote}」）是**代码**，
                        # 不是引文本身 —— 实际输出由变量决定，另行核对。
                        continue
                    cls.quotes.append((f.name, q))

    def test_quotes_found(self):
        """至少要扫到一批引文（防正则失配导致守卫空转）。"""
        self.assertGreaterEqual(len(self.quotes), 30,
                                f"只扫到 {len(self.quotes)} 条引文，正则可能失配")

    def test_each_quote_verbatim_in_original(self):
        """逐条：引文（去标点后）须在原典切片中命中。

        判定分三种可接受形态：
          ① 整串逐字连续命中；
          ② **分段**命中（引文里用「；」「，」把原典的**两处**短句并置 ——
             如「二为侯牧；惟五位为佳」：两段各自是原典，但并非连续串）；
          ③ 「…」节选：各节分别命中。
        """
        bad = []
        for fname, q in self.quotes:
            if q in KNOWN_SELF_WRITTEN:
                continue                    # 自撰概括语由另一条测试管
            if q in KNOWN_VARIANTS:
                continue                    # 已裁决的版本异文
            nq = _norm(q)
            if not nq:
                continue
            if nq in self.corpus:
                continue
            # 分节：省略号切
            if "…" in q or "..." in q:
                segs = [s for s in re.split(r"…|\.\.\.", q) if _norm(s)]
                if segs and all(_norm(s) in self.corpus for s in segs):
                    continue
            # 分句：逗号/分号切（两处原典短句并置）
            segs = [s for s in re.split(r"[，；、]", q) if len(_norm(s)) >= 3]
            if len(segs) >= 2 and all(_norm(s) in self.corpus for s in segs):
                continue
            bad.append((fname, q))
        self.assertEqual(
            bad, [],
            "以下「（原典：…）」标注在原典切片中找不到逐字依据：\n%s"
            % "\n".join("  [%s] %s" % (f, q) for f, q in bad))

    def test_self_written_claims_are_not_labelled_as_original(self):
        """自撰概括语不得标「（原典：…）」。

        这些句子引擎仍可输出（如「仅运反或数反一项，未至不可保」是合理的**结论表述**），
        但必须让调用方看得出它**不是**原典引文。
        """
        bad = []
        for fname, q in self.quotes:
            if q in KNOWN_SELF_WRITTEN:
                bad.append((fname, q))
        self.assertEqual(
            bad, [],
            "以下句子是引擎自撰概括语，却标成了原典引文：\n%s"
            % "\n".join("  [%s] %s（%s）" % (f, q, KNOWN_SELF_WRITTEN[q])
                        for f, q in bad))

    def test_known_self_written_still_documented(self):
        """自撰概括语清单不得为空/失真（改动前须先更新本清单）。"""
        self.assertTrue(KNOWN_SELF_WRITTEN,
                        "自撰概括语清单为空 —— 若已全部改为真引文，请同步清空并更新本测试")
        for q, why in KNOWN_SELF_WRITTEN.items():
            with self.subTest(quote=q):
                self.assertTrue(why, "每条须写明原典实情")

    def test_known_variants_still_documented(self):
        """版本异文清单每条须有说明。"""
        for q, why in KNOWN_VARIANTS.items():
            with self.subTest(quote=q):
                self.assertTrue(why, "每条版本异文须写明依据")

    def test_known_self_written_not_in_original(self):
        """清单里的自撰语确实**不在**原典中（否则就不该叫自撰）。"""
        for q in KNOWN_SELF_WRITTEN:
            with self.subTest(quote=q):
                self.assertNotIn(_norm(q), self.corpus,
                                 f"「{q}」已在原典中出现 —— 请从自撰清单移除")

    def test_chapter_name_word_order(self):
        """章节名「化工元气有无论」的词序（原典语序）—— 防再次写反。

        2026-10-24 实测：引擎曾 9 处写成「元气化工有无论」（词序颠倒），
        原典（包内切片 / 原著.txt / 影印本三源一致）作「化工元气有无论」。

        只查**确实引用该章节**的文件（不是每个文件都得有这句）。
        """
        checked = 0
        for f in _source_files():
            txt = f.read_text(encoding="utf-8")
            if "有无论" not in txt:
                continue
            checked += 1
            with self.subTest(file=f.name):
                self.assertNotIn("元气化工有无论", txt,
                                 f"{f.name} 仍把章节名写成「元气化工有无论」，"
                                 "原典作「化工元气有无论」")
        self.assertGreater(checked, 0, "未扫到任何引用「有无论」章节的文件 —— 正则/路径失效？")


if __name__ == "__main__":
    unittest.main()
