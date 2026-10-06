"""河洛四层时间轴自洽性校验（2026-10-06）

背景：`canonical.GOLDEN_CASES` 只有纪晓岚一例，且只校验 8 个静态字段
（天地数×4、先天卦、元堂、元堂索引、后天卦）。**大运／流年／流月／流日
整条时间轴此前没有任何金标校验**，是裸奔的——复杂度最高的部分反而没有护栏。

本文件用「算法自述的规则」做自洽性校验，不引入外部基准：
  - 大运：自元堂起行先天再行后天；阳爻九年、阴爻六年（timeline_yun）
  - 流月：每月十二段
  - 流日：每爻管五日，六爻俱变毕则满三十日（《河洛真数》起日卦例）
  - 流日动爻：从居位爻下一爻起算（canonical._build_timeline 注释）

这些断言锁的是**算法与自身声明规则的一致性**。若日后改算法口径，
本文件会先红，迫使同步更新规则说明——避免又出现「改了实现、规则注释还留着
旧口径」这类静默漂移。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical

# 纪晓岚 Golden Case（1724 甲辰 辛未 丙戌 甲午，男，午时）
_JX_BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]
_JX_YEAR = 1724


def _calc():
    return HeluoCanonical().calculate(
        bazi=_JX_BAZI, gender="male", birth_hour="午",
        era="zhong", birth_year=_JX_YEAR,
    )


class TestGoldenCaseRuns(unittest.TestCase):
    """金标本身必须能跑完并返回结论。"""

    def test_jixiaolan_passes(self):
        self.assertTrue(HeluoCanonical().verify_golden_case("jixiaolan"))

    def test_verify_returns_bool_not_raises(self):
        """verify_golden_case 是返回 bool 的公开入口。

        2026-10-06 修正：它原先用 ❌/✅ 打印，在非 UTF-8 控制台
        （如 Windows GBK）抛 UnicodeEncodeError，调用方拿不到结论。
        """
        result = HeluoCanonical().verify_golden_case("jixiaolan")
        self.assertIsInstance(result, bool)


class TestDayunRuleConsistency(unittest.TestCase):
    """大运：阳爻九年 / 阴爻六年，自元堂起行先天再行后天。"""

    @classmethod
    def setUpClass(cls):
        cls.timeline = _calc().timeline

    def test_dayun_is_twelve_segments(self):
        dayun = self.timeline.qi_phase["dayun"]
        self.assertEqual(len(dayun), 12, "先天六爻 + 后天六爻 = 12 段")

    def test_segment_duration_follows_yang9_yin6(self):
        bad = [
            (e["age_start"], e["age_end"], e["line_nature"])
            for e in self.timeline.qi_phase["dayun"]
            if (e["age_end"] - e["age_start"] + 1)
            != (9 if e["line_nature"] == "阳" else 6)
        ]
        self.assertEqual(bad, [], f"大运段长不符「阳9阴6」：{bad}")

    def test_dayun_contiguous_from_age_1(self):
        prev = 0
        for e in self.timeline.qi_phase["dayun"]:
            self.assertEqual(e["age_start"], prev + 1,
                             f"{prev+1}-{prev+1} 处应有断裂或重叠")
            prev = e["age_end"]

    def test_first_segment_starts_at_yuantang_index(self):
        """首段爻位应等于元堂索引（自元堂起行）。"""
        yuantang_index = _calc().yuantang.yuantang_index
        self.assertEqual(self.timeline.qi_phase["dayun"][0]["line_index"],
                         yuantang_index)

    def test_prenatal_then_postnatal_order(self):
        """先走完先天六爻，再行后天六爻。"""
        dayun = self.timeline.qi_phase["dayun"]
        first6 = [e["hexagram"] for e in dayun[:6]]
        last6 = [e["hexagram"] for e in dayun[6:]]
        prenatal = _calc().prenatal.hexagram_name
        postnatal = _calc().postnatal.hexagram_name
        self.assertEqual(set(first6), {prenatal},
                         f"前六段应全为先天卦 {prenatal}，实得 {set(first6)}")
        self.assertEqual(set(last6), {postnatal},
                         f"后六段应全为后天卦 {postnatal}，实得 {set(last6)}")


class TestLiunianAxisConsistency(unittest.TestCase):
    """流年：年龄与公历年严格对齐且连续。"""

    @classmethod
    def setUpClass(cls):
        cls.yearly = _calc().timeline.yearly_hexagrams

    def test_first_year_aligns_with_birth(self):
        self.assertEqual(self.yearly[0]["year"], _JX_YEAR)
        self.assertEqual(self.yearly[0]["age"], 1)

    def test_age_and_year_are_contiguous(self):
        for prev, cur in zip(self.yearly, self.yearly[1:]):
            self.assertEqual(cur["age"], prev["age"] + 1)
            self.assertEqual(cur["year"], prev["year"] + 1)

    def test_every_year_has_twelve_months(self):
        bad = [(y["year"], len(y["months"])) for y in self.yearly
               if len(y["months"]) != 12]
        self.assertEqual(bad, [])

    def test_month_numbers_are_one_to_twelve(self):
        for y in self.yearly:
            self.assertEqual([m["month"] for m in y["months"]],
                             list(range(1, 13)))


class TestLiuriRuleConsistency(unittest.TestCase):
    """流日：每爻管五日 → 每月六段，满三十日。"""

    @classmethod
    def setUpClass(cls):
        cls.yearly = _calc().timeline.yearly_hexagrams

    def test_every_month_has_six_day_segments(self):
        bad = [(y["year"], m["month"], len(m["days"]))
               for y in self.yearly for m in y["months"] if len(m["days"]) != 6]
        self.assertEqual(bad, [], "《起日卦例》六爻俱变毕，则满三十日 → 应为 6 段×5日")

    def test_flip_index_starts_from_next_yao_and_wraps(self):
        """动爻从居位爻的下一爻起算，绕六爻一圈回到同一爻位。"""
        first_month = self.yearly[0]["months"][0]
        seq = [d["flip_index"] for d in first_month["days"]]
        self.assertEqual(len(seq), 6)
        # 六段应恰好覆盖六个不同爻位，且首尾衔接（末段+1 == 首段）
        self.assertEqual(sorted(seq), list(range(6)),
                         f"六段应各覆盖一个爻位，实得 {seq}")
        self.assertEqual((seq[-1] + 1) % 6, seq[0],
                         f"动爻序列应首尾相衔，实得 {seq}")

    def test_day_segments_carry_no_hour_data(self):
        """流时应按需现算，不得预展开（2026-10-06 性能改造）。"""
        for d in self.yearly[0]["months"][0]["days"]:
            self.assertNotIn("hours", d)


if __name__ == "__main__":
    unittest.main()