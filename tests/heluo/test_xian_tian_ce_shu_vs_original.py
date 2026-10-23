"""六十四卦爻先天策数 —— 与原典算例对拍（2026-10-07）

**本文件所有期望值一律硬编码自原典原文，不调用被测函数求期望。**

原典 L1807「睽九二」例逐段自洽，可完整对拍至 4423；
原典 L1801「中孚上九」例首段自相矛盾，**必须拒算**——
守卫确保它永远不会悄悄吐出一个看似合理的数
（2026-10-07 首版实现正是在这一路算出 11436，与原典 11712 不符、
又与自家 docstring 写的 11760 不符，且该分支当时零测试覆盖）。
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.xian_tian_ce_shu import (  # noqa: E402
    BAGUA_NUM_CONFIRMED,
    BAGUA_NUM_LUOSHU_REFERENCE,
    BAGUA_NUM_QILUO_L174,
    ORIGINAL_CASES,
    UP_PART_SEG2_ITEMS,
    UP_PART_SEG2_SUM,
    compute_shangti_ce_shu,
    compute_xian_tian_ce_shu,
    split_yuan_hui_yun_shi,
)

_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _orig() -> str:
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        return f.read()


class TestOriginalTextPresent(unittest.TestCase):
    """规则与算例必须真的在原典里，不能凭记忆写实现。"""

    def test_rule_lines_present(self):
        orig = _orig()
        self.assertIn("六十四卦爻先天策数", orig)
        self.assertIn("凡占卦，看演得何卦，阴阳数得若干为祖数", orig)
        self.assertIn("如上体卦动，则以动爻因十而加大数，以卦数因零而加小数", orig)
        self.assertIn("下卦动以卦数因十而加大数，以动爻数因零而加小数", orig)

    def test_kui_example_verbatim(self):
        orig = _orig()
        for frag in ("假如睽九二爻祖数一百九十二",
                     "下二十个一百为二千",
                     "共得三千八百四十策",
                     "共得四千二百二十四数",
                     "又加祖数一百九十二，合得四千四百一十六",
                     "共合得四千四百二十三数",
                     "以千为元，百为会，十为运，零为世，元四会四运二世三"):
            self.assertIn(frag, orig, f"睽例原文缺失：{frag}")

    def test_zhongfu_example_verbatim(self):
        """拒算所依据的那处矛盾，必须能在原典里指到。"""
        orig = _orig()
        for frag in ("先下祖数一百二十九策",
                     "次下六个二十为一百二十",
                     "共计得一万一千七百一十二策",
                     "又以上卦巽五数因之",
                     "共合得一万二千六百七十二策",
                     "通共计得一万二千六百八十五策",
                     "除万不用，以二六八五四位布为元会运世是也"):
            self.assertIn(frag, orig, f"中孚例原文缺失：{frag}")

    def test_bagua_num_witnesses_present(self):
        """卦数确证所依赖的三处文字。"""
        orig = _orig()
        self.assertIn("上卦巽五数", orig)
        self.assertIn("内卦兑二数", orig)
        self.assertIn("外卦离三数", orig)


class TestKuiExampleExact(unittest.TestCase):
    """睽九二：算式逐段对拍，须得 4423。"""

    def setUp(self):
        self.r = compute_xian_tian_ce_shu("睽", "离", "兑", 1, 192)

    def test_total_is_4423(self):
        self.assertEqual(self.r.ce_shu, 4423, f"睽例策数应为 4423，实得 {self.r.ce_shu}")

    def test_segment_arithmetic(self):
        """逐段复算：3840 + 384 = 4224，+192 = 4416，+7 = 4423。"""
        self.assertEqual(20 * 100 + 20 * 90 + 20 * 2, 3840)
        self.assertEqual(2 * 100 + 2 * 90 + 2 * 2, 384)
        self.assertEqual(3840 + 384, 4224)
        self.assertEqual(4224 + 192, 4416)
        self.assertEqual(4416 + 3 + 2 + 2, 4423)

    def test_yuan_hui_yun_shi(self):
        """原典明言「元四会四运二世三」。"""
        self.assertEqual(self.r.yuan_hui_yun_shi, (4, 4, 2, 3))

    def test_no_caveat_and_not_refused(self):
        self.assertEqual(self.r.caveat, "", f"睽例不应有歧义标记：{self.r.caveat}")
        self.assertFalse(self.r.refused)
        self.assertEqual(self.r.moving_part, "下卦")

    def test_steps_record_trajectory(self):
        joined = " ".join(self.r.steps)
        for frag in ("3840", "384", "4224", "4416", "4423"):
            self.assertIn(frag, joined, f"推演痕迹缺 {frag}")

    def test_reports_original_typo(self):
        """原典「下二十个九百为一千八百」是讹（20×900≠1800），须在痕迹里留痕。"""
        self.assertIn("讹", " ".join(self.r.steps))


class TestSplitYuanHuiYunShi(unittest.TestCase):
    def test_four_digit(self):
        self.assertEqual(split_yuan_hui_yun_shi(4423), (4, 4, 2, 3))

    def test_strip_ten_thousand(self):
        """原典「除万不用，以二六八五四位布为元会运世」→ 12685 取 2685。"""
        self.assertEqual(split_yuan_hui_yun_shi(12685), (2, 6, 8, 5))

    def test_leading_zero_is_kept(self):
        self.assertEqual(split_yuan_hui_yun_shi(967), (0, 9, 6, 7))


class TestZhongfuRefusesToGuess(unittest.TestCase):
    """中孚例：首段歧义未裁决 → **恒拒算**，不得吐出任何策数。"""

    def test_refuses_with_zero_and_caveat(self):
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        self.assertEqual(r.ce_shu, 0, "原典歧义未裁决时不得给出策数")
        self.assertTrue(r.refused)
        self.assertEqual(r.yuan_hui_yun_shi, (0, 0, 0, 0),
                         "拒算时不得把 (0,0,0,0) 之外的元会运世吐出来")
        self.assertIn("不敢臆算", r.caveat)

    def test_caveat_names_the_192_discrepancy(self):
        """歧义必须具体到数字：11520 vs 11712，差 192。"""
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        self.assertEqual(60 * 100 + 60 * 90 + 6 * 20, 11520)
        self.assertEqual(11712 - 11520, 192)
        for frag in ("11520", "11712", "192"):
            self.assertIn(frag, r.caveat, f"歧义登记缺 {frag}")

    def test_steps_reproduce_the_unreproducible_segment(self):
        """拒算也要把算不出来的那个式子原样摆出来，供后人复核。"""
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        joined = " ".join(r.steps)
        for frag in ("11520", "11712", "960"):
            self.assertIn(frag, joined, f"拒算痕迹缺 {frag}")

    def test_refuses_regardless_of_bagua_num(self):
        """**回归守卫**：首版实现会在八卦数齐备时照算，产出 11436。

        上体卦动一路的障碍不止八卦数——即使离/兑/巽都已确证，
        首段仍不可复算，故必须恒拒算。
        """
        for upper in ("离", "兑", "巽"):
            r = compute_shangti_ce_shu("某卦", upper, "兑", 5, 129)
            self.assertEqual(r.ce_shu, 0, f"上卦={upper} 时竟给出策数 {r.ce_shu}")
            self.assertTrue(r.refused)

    def test_lower_part_values_are_self_consistent(self):
        """拒算不等于全盘否定：首段之后的链条本身自洽，照录备查。"""
        self.assertEqual(UP_PART_SEG2_ITEMS, (500, 450, 10))
        self.assertEqual(UP_PART_SEG2_SUM, 960)
        self.assertEqual(11712 + 960, 12672)   # 原典「共合得一万二千六百七十二策」
        self.assertEqual(12672 + 13, 12685)    # 原典「通共计得一万二千六百八十五策」
        self.assertEqual(split_yuan_hui_yun_shi(12685), (2, 6, 8, 5))

    def test_compute_xian_tian_refuses_upper_moving(self):
        """下卦动函数遇到上体动爻也须拒算，不得越界给数。"""
        r = compute_xian_tian_ce_shu("某卦", "离", "兑", 5, 129)
        self.assertEqual(r.ce_shu, 0)
        self.assertTrue(r.refused)


class TestUnknownBaguaRefuses(unittest.TestCase):
    """卦数未确证者（乾/震/坎/艮/坤）一律拒算，不按洛书序填默认值。"""

    def test_unconfirmed_trigrams_have_no_default(self):
        for name in ("乾", "震", "坎", "艮", "坤"):
            self.assertNotIn(name, BAGUA_NUM_CONFIRMED,
                             f"{name} 无算例佐证，不应被列为确证卦数")

    def test_refuses_when_lower_unconfirmed(self):
        r = compute_xian_tian_ce_shu("某卦", "离", "震", 1, 100)
        self.assertEqual(r.ce_shu, 0)
        self.assertTrue(r.refused)
        self.assertIn("未裁决", r.caveat)

    def test_refuses_when_upper_unconfirmed(self):
        r = compute_xian_tian_ce_shu("某卦", "乾", "兑", 1, 100)
        self.assertEqual(r.ce_shu, 0)
        self.assertTrue(r.refused)
        self.assertIn("未裁决", r.caveat)


class TestBaguaNumRuling(unittest.TestCase):
    """卦数裁决：先天策数用洛书序，与起例卷 L174 那套并存。"""

    def test_confirmed_values(self):
        self.assertEqual(BAGUA_NUM_CONFIRMED, {"离": 3, "兑": 2, "巽": 5})

    def test_witness_evidence_beats_l174(self):
        """三处算例佐证在洛书序上全中、在 L174 上全错——这是裁决依据。"""
        for name, luoshu in (("兑", 2), ("离", 3), ("巽", 5)):
            self.assertEqual(BAGUA_NUM_CONFIRMED[name], luoshu)
            self.assertNotEqual(BAGUA_NUM_LUOSHU_REFERENCE[name], BAGUA_NUM_QILUO_L174[name],
                                f"{name} 在两套序中同值，L174 并存的前提不成立")

    def test_l174_recorded_for_cross_check(self):
        """起例卷那套仍留档，供人工核对，不被本模块抹掉。"""
        self.assertEqual(BAGUA_NUM_QILUO_L174["兑"], 7)
        self.assertEqual(BAGUA_NUM_QILUO_L174["离"], 9)
        self.assertEqual(BAGUA_NUM_QILUO_L174["巽"], 4)

    def test_luoshu_reference_is_complete_eight(self):
        self.assertEqual(len(BAGUA_NUM_LUOSHU_REFERENCE), 8)
        self.assertEqual(sum(BAGUA_NUM_LUOSHU_REFERENCE.values()), 36)


class TestOriginalCasesTable(unittest.TestCase):
    def test_two_cases_recorded(self):
        self.assertEqual(len(ORIGINAL_CASES), 2)
        self.assertEqual({c[0] for c in ORIGINAL_CASES}, {"中孚", "睽"})

    def test_reproducible_flag_matches_behaviour(self):
        for gua, up, lo, my, zu, want, repro in ORIGINAL_CASES:
            r = compute_xian_tian_ce_shu(gua, up, lo, my, zu)
            if repro:
                self.assertEqual(r.ce_shu, want, f"{gua} 应可对拍得 {want}")
                self.assertFalse(r.refused)
            else:
                self.assertEqual(r.ce_shu, 0, f"{gua} 标注为不可复算，却给出了策数")
                self.assertTrue(r.refused)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
