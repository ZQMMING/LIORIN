"""起例卷之上新落码规则的原典保真守卫（2026-10-08）。

三份只读审计查出的「原典有文而未实现」缺口，本批落码其中判据完备者。
每张表逐条比对原典逐字，并保留跨转录本的讹字裁决证据。

**取证纪律**（本批新立，写在这里以免后人重犯）：
* 原典转录有多本独立传本。凡采信一句，先在多本上对一遍——
  一致才认；不一致才可能是讹，再看是哪一读能与本段其余条文自洽。
* 「自校验」优先于「读起来像对」：本批的元气两说表，
  靠「反者干支必须等于对宫卦的干支组」这一条机械校验钉死，
  连「震反辛辰己/巳」的讹字都是这样定的。
"""
from __future__ import annotations

import io
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo import yuanqi_tables as Y      # noqa: E402

ORIG = (Path.home() / "AppData/Local/Programs/Python").exists()
GUAS = ("乾", "坤", "坎", "离", "震", "巽", "艮", "兑")


class TestYuanQiFanTable(unittest.TestCase):
    """反表 L495–L516：逐条比对原典逐字。"""

    VERBATIM = {
        "乾": ("乙癸未申", "夭寿", ""),
        "坤": ("壬甲戌亥", "贫贱", ""),
        "艮": ("丁酉", "瘫疽（气不通）", "手"),
        "兑": ("丙丑寅", "缺唇翻唇疏齿", "口"),
        "震": ("辛辰巳", "跛", "足"),
        "巽": ("庚卯", "痼疾", "股"),
        "坎": ("己午", "聋", "耳"),
        "离": ("戊子", "瞽眇", "目"),
    }

    def test_every_row_matches_original_verbatim(self):
        self.assertEqual(set(Y.YUANQI_FAN_TABLE), set(self.VERBATIM))
        for g, (gz, sym, part) in self.VERBATIM.items():
            row = Y.YUANQI_FAN_TABLE[g]
            self.assertEqual(row.fan_ganzhi, gz, g)
            self.assertEqual(row.suffering, sym, g)
            self.assertEqual(row.body_part, part, g)

    def test_erratum_jizhen_yi_is_decided_and_recorded(self):
        """L507「震反辛辰己/巳」：A/D 本作「己」，取「巳」——须留证。

        取「巳」的硬依据不是「看着顺」，而是机械自校验：
        「反者的干支组 == 对宫卦在纳表中的干支组」，巽为辛辰**巳**。
        作「己」则「辛辰己」不是任何卦的干支组，八条自校验立刻断一条。
        C（河洛真数OCR）本亦作「巳」。
        """
        src = Path(Y.__file__).read_text(encoding="utf-8")
        self.assertIn("辛辰巳", src)
        self.assertIn("己", src, "讹字「己」未被旁注存疑，违反留证规矩")
        self.assertTrue(Y.yuanqi_fan_suffering("震")[0], "震之病症缺失")

    def test_all_eight_rows_satisfy_dui_self_check(self):
        """反表的八条，反者干支必须正好是对宫卦的干支组。"""
        for g, row in Y.YUANQI_FAN_TABLE.items():
            duo_gan, duo_zhi = Y.YUANQI_GANZHI_TABLE_A[Y.DUI_GUA[g]]
            self.assertEqual(row.fan_ganzhi, duo_gan + duo_zhi,
                             "%s 的反者与对宫 %s 的干支不符"
                             % (g, Y.DUI_GUA[g]))


class TestYuanQiTwoReadings(unittest.TestCase):
    """两说并存：这是本批最要紧的结构性结论。"""

    def test_both_readings_cover_eight_gua(self):
        self.assertEqual(set(Y.YUANQI_GANZHI_TABLE_A), set(GUAS))
        self.assertEqual(set(Y.YUANQI_GANZHI_TABLE_B), set(GUAS))

    def test_youyun_marker_preserved_in_source(self):
        """L519「又云」是原典自陈的另立一说，源码须保留该出处标记。"""
        src = Path(Y.__file__).read_text(encoding="utf-8")
        self.assertIn("又云", src, "「又云」出处标记被删，等于抹掉原典的并列声明")

    def test_two_readings_actually_disagree(self):
        """两说必须在干支归属上**真的不同**——若哪天变得相同，说明有人偷合了。"""
        diff = 0
        for g in GUAS:
            gan, zhi = Y.gua_of_ganzhi_table_a(g)
            a, b = Y.yuanqi_ganzhi_conflict(gan, zhi)
            if a:
                diff += 1
                self.assertEqual(a, g, "%s 的说一归属应是自己" % g)
                self.assertNotEqual(b, g, "%s 两说归属相同，分歧计数失真" % g)
        self.assertEqual(diff, 8, "两说分歧应为八组，实得 %d" % diff)

    def test_conflict_needs_two_args_not_one_string(self):
        """单字干组（「戊」）按位置切片会切错——这是本函数第一版的实际 bug。"""
        self.assertEqual(Y.yuanqi_ganzhi_conflict("戊", "子"), ("坎", "离"))
        self.assertEqual(Y.yuanqi_ganzhi_conflict("壬甲", "戌亥"), ("乾", "巽"))
        self.assertEqual(Y.yuanqi_ganzhi_conflict("乙癸", "申未"), ("坤", "艮"),
                         "支序不同（未申/申未）也须认作同组")

    def test_youyun_opposite_is_nayin_ke_not_dui(self):
        """又云表的「相反」是**纳音相克**，不是对宫——八条里只有坎↔离同属对宫。"""
        ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
        same_as_dui = []
        for g, row in Y.YUANQI_GANZHI_TABLE_B.items():
            opp = row.opposite_gua
            o = Y.YUANQI_GANZHI_TABLE_B[opp]
            self.assertTrue(ke.get(row.nayin_element) == o.nayin_element
                            or ke.get(o.nayin_element) == row.nayin_element,
                            "%s↔%s 纳音不相克" % (g, opp))
            if opp == Y.DUI_GUA[g]:
                same_as_dui.append(g)
        self.assertEqual(same_as_dui, ["坎", "离"],
                         "又云表与对宫重合的应恰为坎、离，实得 %s" % same_as_dui)

    def test_youyun_ganzhi_equals_its_own_opposite_in_table_a(self):
        for g, row in Y.YUANQI_GANZHI_TABLE_B.items():
            duo = Y.gua_of_ganzhi_table_a(row.opposite_gua)
            self.assertEqual(row.gan, duo[0], g)
            self.assertEqual(set(row.zhi), set(duo[1]), g)


class TestGanzhiGuaTable(unittest.TestCase):
    """干支纳卦表 L681–L693。"""

    JIAZHI = None

    def _jiazhi(self):
        """六十甲子：十干与十二支同序轮转取前 60，**不是** 10×12 全组合。"""
        if self.JIAZHI is None:
            gan = "甲乙丙丁戊己庚辛壬癸"
            zhi = "子丑寅卯辰巳午未申酉戌亥"
            self.JIAZHI = [gan[i % 10] + zhi[i % 12] for i in range(60)]
        return self.JIAZHI

    def test_covers_all_sixty_exactly_once(self):
        got = sorted(Y.GANZHI_TO_GUA)
        self.assertEqual(len(got), 60)
        self.assertEqual(got, sorted(self._jiazhi()))
        for el, (lst, guas) in Y.GANZHI_GUA_GROUPS.items():
            self.assertEqual(len(lst), 12, "%s 组应十二干支" % el)
            self.assertEqual(len(set(lst)), 12, "%s 组内有重" % el)

    def test_group_wuxing_and_gua_match_original(self):
        """L681 金=乾兑 / L684 水=坎 / L687 火=离 / L690 土=坤艮 / L693 木=震巽。"""
        want = {"金": "乾兑", "水": "坎", "火": "离", "土": "坤艮", "木": "震巽"}
        self.assertEqual({k: v[1] for k, v in Y.GANZHI_GUA_GROUPS.items()}, want)

    def test_first_row_is_verbatim_jiazi_group(self):
        """L681 逐字首组：甲子、甲午、乙丑、乙未、庚戌、庚辰、辛巳、辛亥、壬寅、壬申、癸卯、癸酉。"""
        self.assertEqual(
            list(Y.GANZHI_GUA_GROUPS["金"][0]),
            ["甲子", "甲午", "乙丑", "乙未", "庚戌", "庚辰",
             "辛巳", "辛亥", "壬寅", "壬申", "癸卯", "癸酉"])
        self.assertEqual(Y.ganzhi_guas("甲子"), ("乾", "兑"))
        self.assertEqual(Y.ganzhi_element("甲子"), "金")

    def test_unknown_ganzhi_returns_empty_not_raise(self):
        self.assertEqual(Y.ganzhi_guas("甲丑"), ())
        self.assertEqual(Y.ganzhi_element("甲丑"), "")

    def test_must_not_be_merged_with_canping_nayin(self):
        """L681 原文自带「即纳音」限定，但本表给的是**卦**，与 canping._NAYIN
        （纳音→五行）是两张独立表，重合不等于同一。守卫在此钉死合并冲动。"""
        sys.path.insert(0, str(Path(Y.__file__).resolve().parents[2] / "src"))
        from heluo_engine.engines.heluo import canping
        gz = "甲子"
        self.assertIn(gz, canping._NAYIN)
        self.assertEqual(Y.ganzhi_element(gz), "金")
        # 五行一致，但一个给「卦组元组」一个给「五行字符串」——不得断言为同一形状
        self.assertIsInstance(Y.ganzhi_guas(gz), tuple)
        self.assertIsInstance(Y.ganzhi_element(gz), str)


class TestModuleBoundary(unittest.TestCase):
    def test_dui_gua_not_same_as_huagong_opposite(self):
        """对宫（错卦）与化工相反（四季对宫）必须是两张不同的表。"""
        from heluo_engine.engines.heluo.hua_gong import HUAGONG_FAN_GUA
        self.assertNotEqual(Y.DUI_GUA, HUAGONG_FAN_GUA,
                            "对宫与化工相反被合成了同一张表")
        self.assertEqual(set(HUAGONG_FAN_GUA), {"坎", "离", "兑", "震"})
        self.assertEqual(set(Y.DUI_GUA), set(GUAS))


if __name__ == "__main__":
    unittest.main()