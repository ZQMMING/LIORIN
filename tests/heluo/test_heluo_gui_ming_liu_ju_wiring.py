# -*- coding: utf-8 -*-
"""贵命六项原典判据的**接线正确性**守卫（2026-10-22）。

本文件锁死四件此前**静默失效**的事（判据在跑、但算的���是别的东西）：

1. **元堂名有两种书写**，只认一种会让四个爻位漏判「二爻位」判据。
   元堂名由 ``yuan_tang.find_yuantang`` 生成：
       · 初爻/上爻 → 「初六」「上九」（爻位在前）
       · 二~五爻   → 「九二」「六四」（阴阳在前）
   旧解析式 ``^(初|[二三四五]|上)`` 只认前者 → 二/三/四/五爻的盘
   （六个爻位里的四个）「爻位」判据恒不判。

2. **爻位号 ≠ 爻阴阳**。``gui_ming_liu_ju.judge_you_yuan`` 要的是
   +1(阳)/-1(阴)，旧实现把 0-5 的爻位号塞进去；初爻(0)会让
   「0 × 应爻 < 0」恒不成立，「五有援」恒判无援。

3. **应爻 = 元堂隔三位**（原典起例卷之上 L121/L126 两例互证）。
   应爻的阴阳取自**本卦**该爻的爻性 —— 无卦六爻时**不判**，不造值。

4. **「一卦名吉」判的是卦名**（原典 L633 明举泰/大有/同人/晋/豫），
   不是三画卦名。旧实现按「乾上乾下」拆出三画卦（乾/坤/…），
   与吉卦表（全是卦名）永不相交 → 该判据恒不判。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.gui_ming_liu_ju import (
    GUA_MING_GOOD_EXAMPLES,
    judge_liu_ju,
    ying_yao_index,
)
from tongshu.engines.heluo.interpretation import (
    HeluoInput,
    RelationalInterpretationEngine,
)
from tongshu.engines.heluo.numbers import (
    HEXAGRAM_SHORT_NAMES,
    short_hexagram_name,
)
from tongshu.engines.heluo.yuan_tang import parse_yuantang_name

_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]


def _result():
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午", era="zhong",
        birth_year=1983, target_year=2026,
    )


def _input(result, **kw):
    yt = result.yuantang
    d = dict(
        prenatal_hexagram=result.prenatal.hexagram_name,
        yuan_tang=yt.yuantang,
        postnatal_hexagram=result.postnatal.hexagram_name,
        day_hexagram="屯上蒙下",
        year_cycle="乙巳", month_cycle="甲申", day_cycle="丙午",
        element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
        line_position={"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
        time_state={"solar_term": "立秋", "hour": 14},
        prenatal_lines=list(yt.lines),
    )
    d.update(kw)
    return HeluoInput(**d)


class TestParseYuantangName(unittest.TestCase):
    """元堂名解析：两种书写都要认。"""

    def test_all_six_positions_recognized(self):
        """六个爻位在两种书写下都要解出正确爻位索引。"""
        cases = {
            # 初爻/上爻：爻位在前
            "初九": (0, 1), "初六": (0, -1),
            "上九": (5, 1), "上六": (5, -1),
            # 二~五爻：阴阳在前
            "九二": (1, 1), "六二": (1, -1),
            "九三": (2, 1), "六三": (2, -1),
            "九四": (3, 1), "六四": (3, -1),
            "九五": (4, 1), "六五": (4, -1),
        }
        for name, (idx, nature) in cases.items():
            self.assertEqual(parse_yuantang_name(name), (idx, nature), name)

    def test_positional_only_form_has_no_nature(self):
        """只含爻位的写法解不出阴阳 → 返回 None（无据不造）。"""
        self.assertEqual(parse_yuantang_name("五爻"), (4, None))
        self.assertEqual(parse_yuantang_name("初爻"), (0, None))

    def test_unparsable_returns_none(self):
        self.assertEqual(parse_yuantang_name("?"), (None, None))
        self.assertEqual(parse_yuantang_name(""), (None, None))


class TestYingYaoPosition(unittest.TestCase):
    """应爻定位：原典两例互证。"""

    def test_original_case_l121(self):
        """L121「同人九三……二岁取应爻，变同人上九」→ 九三(2) 的应爻是上九(5)。"""
        self.assertEqual(ying_yao_index(2), 5)

    def test_original_case_l126(self):
        """L126「泰卦九二，卦应爻居五」→ 九二(1) 的应爻居五(4)。"""
        self.assertEqual(ying_yao_index(1), 4)

    def test_all_positions_are_three_apart(self):
        for idx in range(6):
            self.assertEqual((ying_yao_index(idx) - idx) % 6, 3, idx)


class TestLiujuKwargs(unittest.TestCase):
    """_liuju_kwargs 传参必须是判据要的东西。"""

    @classmethod
    def setUpClass(cls):
        cls.res = _result()
        cls.eng = RelationalInterpretationEngine(_input(cls.res))

    def test_yuantang_line_is_polarity_not_index(self):
        """yuantang_line 必须是 ±1（阴阳），不是 0-5 的爻位号。"""
        kw = self.eng._liuju_kwargs()
        self.assertIn("yuantang_line", kw)
        self.assertIn(kw["yuantang_line"], (-1, 1),
                      "yuantang_line 必须是 +1(阳)/-1(阴)")
        self.assertNotEqual(kw["yuantang_line"], kw.get("yuantang_index"))

    def test_yuantang_index_matches_engine(self):
        """解出的爻位索引必须与引擎的 yuantang_index 一致。"""
        kw = self.eng._liuju_kwargs()
        self.assertEqual(kw["yuantang_index"], self.res.yuantang.yuantang_index)

    def test_ying_yao_index_is_three_apart(self):
        kw = self.eng._liuju_kwargs()
        self.assertEqual(
            kw["ying_yao_index"],
            ying_yao_index(kw["yuantang_index"]),
        )
        self.assertIn(kw["ying_yao_line"], (-1, 1))

    def test_gua_name_is_hexagram_name_not_trigram(self):
        """卦名判据要的是**卦名**，不是三画卦名。"""
        kw = self.eng._liuju_kwargs()
        self.assertIn("gua_name", kw)
        self.assertNotIn(kw["gua_name"], ("乾", "坤", "震", "巽", "坎", "离", "艮", "兑"),
                         "三画卦名与吉卦表（泰/大有/同人/晋/豫）永不相交")
        self.assertEqual(kw["gua_name"], short_hexagram_name(self.res.prenatal.hexagram_name))

    def test_no_prenatal_lines_means_no_youyuan_judgement(self):
        """没有卦六爻 → 应爻爻性无从得知 → 「五有援」不判，不造值。"""
        eng = RelationalInterpretationEngine(_input(self.res, prenatal_lines=[]))
        kw = eng._liuju_kwargs()
        self.assertNotIn("ying_yao_line", kw)
        base, ju = eng._liuju_base()
        self.assertNotIn("有援", ju.get("吉", []))
        self.assertNotIn("有援", ju.get("凶", []))


class TestYouYuanAgainstOriginal(unittest.TestCase):
    """「五有援」按原典 L645 判：元堂与应爻阴阳相反。"""

    def test_real_chart_yields_youyuan(self):
        """真实命盘应能判出「有援」，且方向与原典一致。"""
        res = _result()
        eng = RelationalInterpretationEngine(_input(res))
        base, ju = eng._liuju_base()
        kw = eng._liuju_kwargs()
        expect = (kw["yuantang_line"] * kw["ying_yao_line"]) < 0
        if expect:
            self.assertIn("有援", ju.get("吉", []))
            self.assertNotIn("有援", ju.get("凶", []))
        else:
            self.assertIn("有援", ju.get("凶", []))

    def test_judge_you_yuan_polarity_contract(self):
        """judge_you_yuan：同阴阳 → 无援；反阴阳 → 有援。"""
        from tongshu.engines.heluo.gui_ming_liu_ju import judge_you_yuan
        self.assertTrue(judge_you_yuan(1, -1).passed, "阳元堂 + 阴应爻 → 有援")
        self.assertTrue(judge_you_yuan(-1, 1).passed, "阴元堂 + 阳应爻 → 有援")
        self.assertFalse(judge_you_yuan(1, 1).passed, "阳元堂 + 阳应爻 → 无援")
        self.assertFalse(judge_you_yuan(-1, -1).passed, "阴元堂 + 阴应爻 → 无援")


class TestShortHexagramName(unittest.TestCase):
    """卦名简称归一（64 卦全表）。"""

    def test_all_64_have_short_names(self):
        self.assertEqual(len(HEXAGRAM_SHORT_NAMES), 64)
        self.assertEqual(len(set(HEXAGRAM_SHORT_NAMES.values())), 64,
                         "64 个简称应互不相同")

    def test_known_forms(self):
        self.assertEqual(short_hexagram_name("天水讼"), "讼")
        self.assertEqual(short_hexagram_name("水火既济"), "既济")
        self.assertEqual(short_hexagram_name("乾为天"), "乾")
        self.assertEqual(short_hexagram_name("地天泰"), "泰")
        self.assertEqual(short_hexagram_name("讼"), "讼")
        self.assertEqual(short_hexagram_name("乾上乾下"), "乾")

    def test_unknown_returns_empty(self):
        """认不出返回空串（不猜）——判据层据此判「不判」。"""
        self.assertEqual(short_hexagram_name("???"), "")
        self.assertEqual(short_hexagram_name(""), "")

    def test_all_good_examples_are_reachable(self):
        """原典 L633 明举的吉卦都能归一成简称。"""
        for g in GUA_MING_GOOD_EXAMPLES:
            self.assertEqual(short_hexagram_name(g), g, g)


class TestGuaMingJudgeNowFires(unittest.TestCase):
    """「一卦名吉」在真实卦名下能判吉（不再恒不判）。"""

    def test_ta_i_gua_is_judged_good(self):
        """地天泰 = 明举吉卦 → 「卦名」项判吉。"""
        res = _result()
        gua = short_hexagram_name("地天泰")
        self.assertEqual(gua, "泰")
        out = judge_liu_ju(gua_name=gua)
        self.assertTrue(out["卦名"].passed, "泰卦应判卦名吉")

    def test_non_example_is_not_judged(self):
        """不在明举例内 → 判「不判」（原典未言其余卦为凶），不判凶。"""
        out = judge_liu_ju(gua_name="讼")
        self.assertIsNone(out["卦名"].passed,
                          "原典未言其余卦为凶，应为 None（不判）而非 False")


if __name__ == "__main__":
    unittest.main()
