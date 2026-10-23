"""数足不足论：余数奇偶与命名的逐条对照（2026-10-07）

起因：起例卷之中对照表核查发现，`judge_shu_xiong` 的「孤阳不偶」「孤阴背阳」
**漏掉了原典明文的「余偶数／余奇数」限定**，导致原典另立的
「孤阳自偶」「孤阴向阳」两个命名被吞掉。

原典逐字：

    L974  「孤阳不偶　天数二十六以上，至四十以下，**余偶数**，
           而地数只得三十是也，乃阳数有余，阴数无余。」
    L983  「孤阳自偶　天数三十一至四十一、五十一，**余奇数**，
           地数只得三十是也。」
    L1046 「孤阴背阳　地数三十至五十、六十，**余偶数**，
           而天数只二十五是也。乃阳无余，阴数有余。」
    L1055 「孤阴向阳　天数二十五，地数得四十至六十以下，**余奇数**是也。
           乃阴数过，阳数足。」
    L1073 「以弱敌强　地数三十至四十、五十、六十以上，
           天数只得二十四以下是也。」

「余」的定义：**天数−25**（阳数之正）／**地数−30**（阴数之正）。
本文件钉死该定义，并逐个命名验证奇偶分流正确。

另钉死一条反直觉但有据的行为：**孤阳自偶与孤阴向阳不判凶**。
原典对二者只给诗断、未言「必凶」，且诗明言
「晚年得势始荣欣」「有阳能改过」——故不套用孤阳不偶的凶断。
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _orig_text():
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        return f.read()


class TestOriginalWording(unittest.TestCase):
    """四条命名的原文必须逐字存在（含余数限定词）。"""

    def setUp(self):
        self.orig = _orig_text()

    def test_four_named_patterns_exist_verbatim(self):
        for frag in ("孤阳不偶", "孤阳自偶", "孤阴背阳", "孤阴向阳", "以弱敌强"):
            self.assertIn(frag, self.orig, f"原典无「{frag}」")

    def test_yu_odd_even_words_present(self):
        """原典确以「余偶数／余奇数」区分，不是后人臆加。"""
        self.assertIn("余偶数", self.orig)
        self.assertIn("余奇数", self.orig)
        self.assertIn("天数二十六以上，至四十以下", self.orig)
        self.assertIn("地数三十至五十、六十", self.orig)


class TestYuParitySplitsNames(unittest.TestCase):
    """「余」的奇偶必须真正分流命��。"""

    def setUp(self):
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        self.judge = judge_shu_xiong

    def _pattern(self, tian, di, month=11):
        return self.judge(tian, di, month).pattern

    def test_gu_yang_bu_ou_is_even_yu(self):
        # 天数 26..40 且地数=30；余 = 天数−25
        # 余偶 → 孤阳不偶
        for tian in range(26, 41):
            if (tian - 25) % 2 == 0:
                self.assertEqual(self._pattern(tian, 30), "孤阳不偶",
                                 f"天数{tian} 余{tian - 25} 偶，应为孤阳不偶")

    def test_gu_yang_zi_ou_is_odd_yu(self):
        for tian in range(26, 41):
            if (tian - 25) % 2 == 1:
                self.assertEqual(self._pattern(tian, 30), "孤阳自偶",
                                 f"天数{tian} 余{tian - 25} 奇，应为孤阳自偶（原典 L983）")

    def test_gu_yin_bei_yang_is_even_yu(self):
        """原典 L1046：地数 30-60 余偶（余 0 即地数正数 30 属安和自宁，从 32 起）。"""
        for di in range(32, 61):
            if (di - 30) % 2 == 0:
                self.assertEqual(self._pattern(25, di), "孤阴背阳",
                                 f"地数{di} 余{di - 30} 偶，应为孤阴背阳")

    def test_gu_yin_xiang_yang_is_odd_yu(self):
        """原典 L1055：天数25、地数 40-60、余奇 → 孤阴向阳。"""
        hits = 0
        for di in range(40, 61):
            if (di - 30) % 2 == 1:
                self.assertEqual(self._pattern(25, di), "孤阴向阳",
                                 f"地数{di} 余{di - 30} 奇，应为孤阴向阳")
                hits += 1
        self.assertGreater(hits, 0, "测试数据本身有问题：没有余奇数用例")


class TestNewPatternsNotAutoXiong(unittest.TestCase):
    """孤阳自偶／孤阴向阳按原典**不判凶**（原典只给诗断，未言必凶）。"""

    def setUp(self):
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        self.judge = judge_shu_xiong

    def test_gu_yang_zi_ou_not_shu_xiong(self):
        """原典诗：「壮岁艰辛勤苦立，晚年得势始荣欣」——非必凶。"""
        r = self.judge(27, 30, 11)      # 余 2 偶 → 孤阳不偶（此为对照）
        self.assertEqual(r.pattern, "孤阳不偶")
        self.assertTrue(r.shu_xiong, "孤阳不偶在阳月令应凶（原典 L1073）")
        r2 = self.judge(26, 30, 11)     # 余 1 奇 → 孤阳自偶
        self.assertEqual(r2.pattern, "孤阳自偶")
        self.assertFalse(r2.shu_xiong,
                         "孤阳自偶原典未言必凶，不应套用孤阳不偶的凶断")

    def test_gu_yin_xiang_yang_not_shu_xiong(self):
        r = self.judge(25, 41, 11)      # 余 11 奇 → 孤阴向阳
        self.assertEqual(r.pattern, "孤阴向阳")
        self.assertFalse(r.shu_xiong,
                         "孤阴向阳原典「有阳能改过」，不应判凶")

    def test_old_behavior_would_have_misjudged(self):
        """反证：若不判余数奇偶，这两个命名会被吞进前者而误判凶。"""
        r = self.judge(26, 30, 11)      # 余奇
        self.assertNotEqual(r.pattern, "孤阳不偶",
                            "余奇数仍被判孤阳不偶 → 余数限定未生效")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
