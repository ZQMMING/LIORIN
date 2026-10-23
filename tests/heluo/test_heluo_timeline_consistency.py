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

from heluo_engine.engines.heluo.canonical import HeluoCanonical

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
    """流日：**一卦管 6 日、一爻一日、首日从初爻起** → 每月 5 段，满三十日。

    2026-10-22 口径统一：生产流日口径由 hou5（《河洛真数》L390 每爻管五日）
    统一为 gua6（定稿口径，一卦管六日）。hou5 的「每爻管五日 / 阳日寻阳位、
    阴日寻阴位」规则**未被删除**，仍由
    ``tests/heluo/test_liuri_vs_original.py`` 按 L390 字面实例逐条对拍；
    本类改为守卫 gua6 的逐日推进规则。
    """

    @classmethod
    def setUpClass(cls):
        cls.yearly = _calc().timeline.yearly_hexagrams

    def test_every_month_has_five_gua6_segments(self):
        bad = [(y["year"], m["month"], len(m["days"]))
               for y in self.yearly for m in y["months"] if len(m["days"]) != 5]
        self.assertEqual(bad, [], "一卦管六日 → 应为 5 段×6日")

    def test_gua6_segment_day_positions_are_sequential(self):
        """gua6 逐日推进：段内初→二→三→四→五→上顺推，首日从初爻起。

        原典（《河洛理数》K3-448 L483 硬算例 + L488「其餘五爻五變 一卦管六日」）：
        每卦管六日，段内六日依次取初、二、三、四、五、上爻。
        """
        first_month = self.yearly[0]["months"][0]
        seq = []
        for d in first_month["days"]:
            seq.extend(d.get("day_positions") or [])
        self.assertEqual(len(seq), 30, "起日卦应覆盖 30 日")
        self.assertEqual(seq, [0, 1, 2, 3, 4, 5] * 5,
                         "gua6 段内爻位应逐日顺推（初→上），五段循环")

    def test_gua6_segments_advance_by_month_gua_flipping_each_yao(self):
        """段间推进：**月卦逐爻变**（居位爻不动），非链式累变。

        2026-10-22 原典硬算例更正：《河洛理数》日卦定式（K3-448 L464-L491 /
        K3-447 L1149-L1159）「日卦者每月變五卦，每卦管六日」「假如七月月得既濟六二爻，
        **除此一爻不變**」—— 五个段本卦是月卦**各变一爻**，不是链式累变。
        原实现取链式 `day_lines[k*6]`，产出退化序列（屯、鼎、屯、鼎、屯），与原典不合。
        """
        from heluo_engine.engines.heluo.timeline_yun import liuri_gua6_bases
        m = self.yearly[0]["months"][0]
        bases = liuri_gua6_bases(m["lines"], m["yue_yao_index"])
        for k, seg in enumerate(m["days"]):
            self.assertEqual(seg["lines"], list(bases[k]),
                             f"第{k + 1}段本卦应等于月卦变第 {k + 1} 个未变之爻")

    def test_gua6_original_case_five_bases(self):
        """《河洛理数》万历二十三年七月硬算例：既济·居位二爻 → 屯、革、明夷、家人、蹇。

        引文与日算互证见 ``timeline_yun._GUA6_FLIP_ORDER`` 的注释：
          段1 變既濟九三 → 屯（L479「屯卦六爻從下而上一爻一日，自初二日至初七」）
          段2 變既濟六四 → 革（L477「至初八日又變…為革卦」；初八 = 初二 + 6）
          段3 變既濟九五 → 明夷（L483「至十四日…明夷六五」；十四 = 初二 + 12）
          段4 變既濟上六 → 家人（K3-447 L1158）
          段5 變既濟初九 → 蹇（余爻，排除法定）
        """
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            liuri_gua6_bases, _lines_to_hexagram,
        )
        ji = build_six_lines("坎", "离")          # 既济（坎上离下）
        names = [_lines_to_hexagram(b)[2] for b in liuri_gua6_bases(ji, 1)]
        self.assertEqual(names, ["水雷屯", "泽火革", "地火明夷", "风火家人", "水山蹇"],
                         "既济·居位二爻 的五段本卦应逐字等于原典")

    def test_hou5_original_rule_still_pinned_at_function_level(self):
        """hou5《起日卦例》原典规则仍在（函数级），未被口径统一删掉。

        「每一爻管五日」+「阳日寻阳位（初三五）/阴日寻阴位（二四上）」
        —— 见 ``tests/heluo/test_liuri_vs_original.py`` 的字面展开守卫。
        """
        from heluo_engine.engines.heluo.timeline_yun import liuri_day_positions
        for yi in range(6):
            seq = liuri_day_positions(yi)
            self.assertEqual(len(seq), 30)
            self.assertEqual([seq.count(i) for i in range(6)], [5] * 6,
                             f"居位爻 {yi}：每爻应恰管 5 日")
            yang = [seq[d] for d in range(30) if d % 2 == 0]
            yin = [seq[d] for d in range(30) if d % 2 == 1]
            self.assertTrue(all(p in (0, 2, 4) for p in yang), f"阳日应落阳位：{yang}")
            self.assertTrue(all(p in (1, 3, 5) for p in yin), f"阴日应落阴位：{yin}")

    def test_day_segments_carry_no_hour_data(self):
        """流时应按需现算，不得预展开（2026-10-06 性能改造）。"""
        for d in self.yearly[0]["months"][0]["days"]:
            self.assertNotIn("hours", d)


if __name__ == "__main__":
    unittest.main()