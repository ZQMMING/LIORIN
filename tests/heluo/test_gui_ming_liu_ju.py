"""贵命六项判据 —— 逐条比对原典 L630–L648 / L669（2026-10-07）

**本文件的作用**：防止再次出现「无原典依据的自拟规则」混进引擎。

背景：``hexagram_state.get_base_factors``（静0.5/动0.7/变0.6/互0.4）与
``interpretation._hexagram_base_score``（乾0.8/坤0.6/震巽0.5/坎离0.4…）
都是**凭空捏造的分数**，在任何原典条目中都找不到出处。
本模块用起例卷之中 L630–L648 的**六项明文判据**取代它们。

**不臆造的红线**（本文件逐条钉死）：
1. 「四得时」原典只给春震/夏离/秋兑/冬坎**四季**例，未给月份划分规则
   → **不把十二月摊到四季**，只接受显式传入的 season。
2. 「六顺时」原典只举**正月、九月**两例
   → **只判这两月**，其余月份返回 None（"原典未言此月"）。
3. 「一卦名吉」原文作「**之类**」= 举例未穷举
   → 不在举例之列的卦**不判凶**，只登记不判。
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.gui_ming_liu_ju import (
    GUA_MING_GOOD_EXAMPLES,
    JI_CI_GOOD_CHARS,
    JI_YAO_GOOD,
    LIU_JU,
    SEASON_TRIGRAM_GUA,
    XIU_JU,
    judge_de_shi,
    judge_shun_shi,
    judge_yao_ci,
    judge_yao_wei,
    judge_you_yuan,
)

_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _lines():
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        return f.read().split("\n")


class TestLiuJuQuotedFromOriginal(unittest.TestCase):
    """六项判据的原文摘录必须逐字出自原典。"""

    def setUp(self):
        self.orig = "\n".join(_lines())

    def test_each_basis_appears_verbatim(self):
        for name, (line_no, text) in LIU_JU.items():
            self.assertIn(text.replace("……", "").split("。")[0], self.orig,
                          f"「{name}」的原文摘录不在原典中：{text}")
            self.assertEqual(
                _lines()[line_no - 1][:len(text.replace("……", "").split("。")[0])],
                text.replace("……", "").split("。")[0],
                f"「{name}」标注行号 {line_no} 与实际内容不符")

    def test_xiu_ju_appears_in_original(self):
        for name, text in XIU_JU.items():
            self.assertIn(text, self.orig, f"凶断「{text}」不在原典中")


class TestYaoWeiLiteral(unittest.TestCase):
    """二爻位吉（原典 L636「元堂住在二五爻是也」）。"""

    def test_good_positions_are_2_and_5(self):
        self.assertEqual(JI_YAO_GOOD, (1, 4), "二五爻对应索引 1 与 4")

    def test_judge(self):
        self.assertTrue(judge_yao_wei(1).passed, "二爻应吉")
        self.assertTrue(judge_yao_wei(4).passed, "五爻应吉")
        for bad in (0, 2, 3, 5):
            self.assertFalse(judge_yao_wei(bad).passed, f"索引{bad}非二五爻")


class TestYaoCiLiteral(unittest.TestCase):
    """三辞吉（原典 L639「卦爻中有元吉亨利是也」）。"""

    def test_good_chars(self):
        self.assertEqual(JI_CI_GOOD_CHARS, ("元吉", "亨利"))

    def test_judge(self):
        self.assertTrue(judge_yao_ci("元吉，利见大人").passed)
        self.assertTrue(judge_yao_ci("亨利贞").passed)
        self.assertFalse(judge_yao_ci("困于葛藟").passed)


class TestYouYuanLiteral(unittest.TestCase):
    """五有援（原典 L645「元堂在阳爻，应爻得阴…是也」）。"""

    def test_yin_yang_opposite_is_you_yuan(self):
        self.assertTrue(judge_you_yuan(1, -1).passed, "元堂阳、应阴 → 有援")
        self.assertTrue(judge_you_yuan(-1, 1).passed, "元堂阴、应阳 → 有援")

    def test_same_nature_is_wu_yuan(self):
        self.assertFalse(judge_you_yuan(1, 1).passed, "元堂阳、应阳 → 无援")
        self.assertFalse(judge_you_yuan(-1, -1).passed, "元堂阴、应阴 → 无援")


class TestDeShiNoMonthInference(unittest.TestCase):
    """「四得时」**不得**自行把月份摊到四季。"""

    def test_season_table_has_only_four_keys(self):
        """原典只给春/夏/秋/冬四季例 → 表键必须是季节，不是月份。"""
        self.assertEqual(sorted(SEASON_TRIGRAM_GUA), ["冬", "夏", "春", "秋"])
        self.assertEqual(SEASON_TRIGRAM_GUA,
                         {"春": "震", "夏": "离", "秋": "兑", "冬": "坎"},
                         "原典 L642：春震木、夏离火、秋兑金、冬坎水")

    def test_quarterly_case_needs_explicit_season(self):
        """未传季节时，不得因月份而擅自判定季度正卦。"""
        r = judge_de_shi("震", month=1, gua_qi_month=5)   # 卦气不合
        self.assertIsNone(r.passed,
                          "未给 season 时不得据月份判季度正卦得时（属臆造）")

    def test_quarterly_case_with_explicit_season(self):
        r = judge_de_shi("震", season="春")
        self.assertTrue(r.passed, "春震木 → 得时")
        r2 = judge_de_shi("离", season="春")
        self.assertFalse(r2.passed, "春当震非离 → 不得时")

    def test_guaqi_month_case(self):
        """原典「正月得泰卦」——卦气月合即得时。"""
        r = judge_de_shi("乾", month=1, gua_qi_month=1)
        self.assertTrue(r.passed, "生月正月 = 卦气属正月 → 得时")
        r2 = judge_de_shi("乾", month=9, gua_qi_month=1)
        self.assertFalse(r2.passed, "生月九月 ≠ 卦气正月 → 不得时")


class TestShunShiNoMonthInference(unittest.TestCase):
    """「六顺时」只判原文明举的正月、九月，其余不判。"""

    def test_zheng_yue(self):
        r = judge_shun_shi(1, 30, 20)
        self.assertTrue(r.passed, "正月天数多地数少 → 顺时")
        self.assertFalse(judge_shun_shi(1, 20, 30).passed)

    def test_jiu_yue(self):
        r = judge_shun_shi(9, 20, 30)
        self.assertTrue(r.passed, "九月地数多天数少 → 顺时")
        self.assertFalse(judge_shun_shi(9, 30, 20).passed)

    def test_other_months_are_undecided(self):
        """原典未举之月一律 None，绝不按「阳月令=天数多」内插。"""
        for m in (2, 3, 4, 5, 6, 7, 8, 10, 11, 12):
            r = judge_shun_shi(m, 30, 20)
            self.assertIsNone(r.passed,
                              f"{m}月原典未言，不应判定顺/逆时（属臆造）")
            self.assertIn("原典无明文", r.detail)


class TestGuaMingLiteral(unittest.TestCase):
    """一卦名吉（原典 L633「如泰、大有、同人、晋、豫之类是也」）。"""

    def test_examples_from_original(self):
        self.assertEqual(GUA_MING_GOOD_EXAMPLES, ("泰", "大有", "同人", "晋", "豫"))

    def test_others_are_undecided_not_bad(self):
        """原文作「之类」= 举例未穷举，不在列举内不等于凶。"""
        from heluo_engine.engines.heluo.gui_ming_liu_ju import judge_liu_ju
        r = judge_liu_ju(gua_name="乾")["卦名"]
        self.assertIsNone(r.passed, "乾不在明举例内，原典未言其凶，不应判 False")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
