# -*- coding: utf-8 -*-
"""《河洛真数》原典算例回归守卫（2026-10-22）。

**这是本引擎最重要的一道校准尺。**

原典出处：《河洛真数·起例卷之中》L183「先贤命格假令例」下 L184-L187
**四个完整算例**，每个都给出：出生年月日时、四柱、**天数地数**、成卦过程、
**元堂**、**后天卦**、换后天的岁数、以及逐条断语。

本守卫逐项对拍引擎，覆盖**整条链**：
    四柱 → 天地二数 → 先天卦 → 元堂 → 后天卦 → 大运（换后天岁数）

**对拍结果（2026-10-22 实测）：4 例 20 项全部吻合。**

## 算例 1 的底本讹字（重要留证）

L184 底本作「命庚午甲申**丙午**丁酉」，但：

1. **天地二数反推**：只有日柱作「**丙申**」才得原典自述的
   「阳数四十四 / 阴数二十八」（引擎对「丙午」给 天42 地26，对「丙申」给
   天44 地28 —— 后者与原典逐字相同）。
   穷举验证：改动 `numbers` 里**任何**一个天干值或地支值，都不能让四个
   算例同时吻合 → 数表本身无误。
2. **引擎历法独立印证**：`sxtwl` 从公历 1150-08-16（= 农历 1150 年七月二十二日）
   算出的日柱正是**丙申**，丙申日酉时 = 丁酉时 → 与原典时柱相合。
3. 两路独立证据互证 → 判定为**底本转录讹字**（午/申形近），非引擎缺陷。

故本守卫对算例 1 使用**校正后**的四柱（丙申），并在
`heluo_engine/docs/起例卷之下算法对照表_20261007.md` 留档。

## 不对拍的部分（如实说明）

* **断语文本**：逐条长句、且含大量随上下文而变的措辞，不作字面断言。

> ⚠ 2026-10-22 更正：此条原写「历法层：原典用的是南宋历，其农历日期与现代农历
> 有数日之差（L184「七月二十二日」在现代历下推不出「丙午日丁酉时」），故只对四柱
> 及其下游对拍」—— **该定性已撤回**。真因是 1582 年前的**儒略历 / proleptic
> Gregorian 口径差**（1150/1206 年差 7 天），不是「南宋历与现代农历差数日」。
> 改走 sxtwl（儒略历标签）后，五例「农历 → 公历 → 四柱 → 判词」**全链逐字吻合**，
> 见 `tests/heluo/test_heluo_calendar_original.py` 与 docs §14.22。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.canonical import HeluoCanonical
from heluo_engine.engines.heluo.numbers import build_six_lines
from heluo_engine.engines.heluo.timeline_yun import compute_dayun_liyao
from heluo_engine.engines.heluo.yuan_tang import find_yuantang

#: 《起例卷之中》L184-L187 四个原典算例。
#: - bazi        : 原典四柱（算例 1 用校正后的日柱丙申，见模块 docstring）
#: - tian/di     : 原典自述的天地二数
#: - prenatal    : 原典自述的先天卦全名
#: - yuantang    : 原典自述的元堂爻名
#: - postnatal   : 原典自述的后天卦全名（「重离」= 离为火，见下）
#: - switch_age  : 原典自述的换后天岁数
CASES = [
    dict(
        no=1, line="L184",
        bazi=[("庚", "午"), ("甲", "申"), ("丙", "申"), ("丁", "酉")],
        hour="酉", tian=44, di=28,
        prenatal="火山旅", yuantang="初六",
        postnatal="离为火", postnatal_in原文="重离", switch_age=46,
        quote="假令绍兴庚午七月二十二日酉时生男，命庚午甲申丙午丁酉，二篇之策，"
              "阳数四十四，除天数二十五，剩十九，除十不用，零九数属离，"
              "阴数二十八，除二十外而用零八数属艮，合之得火山旅卦。"
              "其阴时在初六爻为元堂，辞云旅琐琐，斯其所取灾。……"
              "到四十六年换后天而为重离",
    ),
    dict(
        no=2, line="L185",
        bazi=[("乙", "亥"), ("乙", "酉"), ("戊", "寅"), ("庚", "申")],
        hour="申", tian=26, di=26,
        prenatal="天水讼", yuantang="初六",
        postnatal="泽天夬", postnatal_in原文="夬", switch_age=49,
        quote="假令绍兴乙亥八月初三日申时生男，命乙亥乙酉戊寅庚申，"
              "天数二十六，除二十五零一，地数二十六零六，阴男天数在内，"
              "一为坎，六为乾，合得天水讼卦。申阴时在初六为元堂，"
              "辞曰不永所事。……至四十九岁换后天之卦为夬",
    ),
    dict(
        no=3, line="L186",
        bazi=[("丙", "寅"), ("庚", "子"), ("丙", "子"), ("己", "亥")],
        hour="亥", tian=18, di=42,
        prenatal="山地剥", yuantang="上九",
        postnatal="坤为地", postnatal_in原文="坤", switch_age=None,
        quote="假令开僖二年丙寅十月二十九日亥时生男，命丙寅庚子丙子己亥，"
              "天数十八零八，地数四十二以二零，用二篇之策，演得山地剥卦。"
              "亥上九为元堂，辞云硕果不食，君子得舆，小人剥庐。……"
              "然后天换而为坤",
    ),
    dict(
        no=4, line="L187",
        bazi=[("戊", "子"), ("甲", "子"), ("癸", "巳"), ("癸", "亥")],
        hour="亥", tian=11, di=30,
        prenatal="水雷屯", yuantang="九五",
        postnatal=None, postnatal_in原文=None, switch_age=None,
        quote="假令绍定三年戊子十一月二十三日亥时生男，命戊子甲子癸巳癸亥，"
              "天数十一而用一为坎，地数三十用三为震，演得水雷屯。"
              "然又卦为屯，元堂在九五，爻辞曰屯其膏，小贞吉，大贞凶，不甚佳",
    ),
]


def _engine(c):
    res = HeluoCanonical().calculate(
        bazi=c["bazi"], gender="male", birth_hour=c["hour"], era="zhong",
        birth_year=1900)
    pre = build_six_lines(res.prenatal.upper_gua, res.prenatal.lower_gua)
    post = build_six_lines(res.postnatal.upper_gua, res.postnatal.lower_gua)
    pyt = find_yuantang(six_lines=post, birth_hour=c["hour"], gender="male",
                         xiantian_name=res.postnatal.hexagram_name)
    dy = compute_dayun_liyao(pre, res.yuantang.yuantang_index, post,
                              pyt.yuantang_index)
    switch = next((e.age_start for e in dy.sequence if e.phase == "后天"), None)
    return res, switch


class TestOriginalCasesTianDiShu(unittest.TestCase):
    """天地二数：四例逐一对拍。"""

    def test_all_cases(self):
        for c in CASES:
            with self.subTest(case=c["no"], line=c["line"]):
                res, _ = _engine(c)
                self.assertEqual(
                    (res.numbers.tian_shu, res.numbers.di_shu),
                    (c["tian"], c["di"]),
                    f"算例{c['no']}（{c['line']}）天地二数与原典不符")

    def test_reduced_numbers_map_to_original_trigrams(self):
        """余数 → 三画卦，与原典的「零九数属离」「一为坎」「以二零」等逐一吻合。

        洛书序：1坎 2坤 3震 4巽 5中 6乾 7兑 8艮 9离。
        """
        san = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中",
               6: "乾", 7: "兑", 8: "艮", 9: "离"}
        for c in CASES:
            with self.subTest(case=c["no"]):
                res, _ = _engine(c)
                self.assertIn(san[res.numbers.tian_reduced],
                              (res.prenatal.upper_gua, res.prenatal.lower_gua),
                              f"算例{c['no']} 天数余数所归三画与先天卦不符")
                self.assertIn(san[res.numbers.di_reduced],
                              (res.prenatal.upper_gua, res.prenatal.lower_gua),
                              f"算例{c['no']} 地数余数所归三画与先天卦不符")


class TestOriginalCasesHexagramAndYuantang(unittest.TestCase):
    """先天卦 / 元堂 / 后天卦 / 换后天岁数：四例逐一对拍。"""

    def test_prenatal_hexagram(self):
        for c in CASES:
            with self.subTest(case=c["no"], line=c["line"]):
                res, _ = _engine(c)
                self.assertEqual(res.prenatal.hexagram_name, c["prenatal"],
                                 f"算例{c['no']}（{c['line']}）先天卦与原典不符")

    def test_yuantang(self):
        for c in CASES:
            with self.subTest(case=c["no"], line=c["line"]):
                res, _ = _engine(c)
                self.assertEqual(res.yuantang.yuantang, c["yuantang"],
                                 f"算例{c['no']}（{c['line']}）元堂与原典不符")

    def test_postnatal_hexagram(self):
        """后天卦。

        算例 1 的原典作「**重离**」—— 离☲ 即两离相重，故「重离」= 「离为火」，
        属同一卦的别称，非另一卦。
        """
        for c in CASES:
            if not c["postnatal"]:
                continue
            with self.subTest(case=c["no"], line=c["line"]):
                res, _ = _engine(c)
                self.assertEqual(res.postnatal.hexagram_name, c["postnatal"],
                                 f"算例{c['no']}（{c['line']}）后天卦与原典不符"
                                 f"（原典作「{c['postnatal_in原文']}」）")

    def test_switch_to_postnatal_age(self):
        """换后天的岁数（爻位值运：先天六爻行毕转后天）。"""
        for c in CASES:
            if not c["switch_age"]:
                continue
            with self.subTest(case=c["no"], line=c["line"]):
                _, switch = _engine(c)
                self.assertEqual(switch, c["switch_age"],
                                 f"算例{c['no']}（{c['line']}）换后天岁数与原典不符")


class TestNumberTableIsPinnedByCases(unittest.TestCase):
    """穷举证明：数表（天干值/地支值）**与四个算例自洽**，不得擅改。

    算例 1 若按底本原样的「丙午」日柱，会差 2/2（天42地26 vs 原典天44地28）。
    那很容易让人怀疑「是数表错了」而去改 ``numbers`` 的取值表。
    本类把这件事**穷举钉死**：改动 ``STEM_VALUES`` 里**任何一个**天干值，
    或 ``BRANCH_VALUES`` 里**任何一个**地支值，都**不可能**让四个算例同时
    与原典吻合 —— 说明数表本身无误，算例 1 的差是**底本讹字**。

    同时反证：算例 1 的日柱若作「丙申」，四例即全数吻合。
    """

    def _td(self, bazi):
        from heluo_engine.engines.heluo.numbers import BRANCH_VALUES, STEM_VALUES
        t = d = 0
        for g, z in bazi:
            allv = [STEM_VALUES[g]] + list(BRANCH_VALUES[z])
            t += sum(v for v in allv if v % 2 == 1)
            d += sum(v for v in allv if v % 2 == 0)
        return t, d

    def _all(self):
        return [self._td(c["bazi"]) for c in CASES]

    def test_cases_match_original(self):
        want = [(c["tian"], c["di"]) for c in CASES]
        self.assertEqual(self._all(), want)

    def test_no_single_stem_or_branch_value_change_fixes_everything(self):
        """改动**算例中实际出现**的任一天干值/地支值，都不能让四例**仍然**全对。

        即：现表是这四个算例在「单值修正」范围内的**唯一解**。

        注：只穷举**算例里出现过的**干支 —— 未出现的干（如辛）本就不影响
        四例结果，穷举它们会误判成「有人能改对」。
        """
        from heluo_engine.engines.heluo.numbers import BRANCH_VALUES, STEM_VALUES
        want = [(c["tian"], c["di"]) for c in CASES]
        used_gans = {g for c in CASES for g, _ in c["bazi"]}
        used_zhis = {z for c in CASES for _, z in c["bazi"]}
        for g in sorted(used_gans):
            old = STEM_VALUES[g]
            for v in range(1, 11):
                if v == old:
                    continue
                STEM_VALUES[g] = v
                try:
                    self.assertNotEqual(
                        self._all(), want,
                        f"改 STEM_VALUES[{g}]={v} 后四例仍全对 —— "
                        f"说明现表不是唯一解，请重新核对算例")
                finally:
                    STEM_VALUES[g] = old
        for z in sorted(used_zhis):
            old = BRANCH_VALUES[z]
            for pair in ((1, 6), (5, 10), (3, 8), (2, 7), (4, 9)):
                if pair == old:
                    continue
                BRANCH_VALUES[z] = pair
                try:
                    self.assertNotEqual(
                        self._all(), want,
                        f"改 BRANCH_VALUES[{z}]={pair} 后四例仍全对 —— "
                        f"说明现表不是唯一解，请重新核对算例")
                finally:
                    BRANCH_VALUES[z] = old

    def test_case1_ganzhi_typo_is_the_only_cause(self):
        """算例 1：日柱作「丙申」才吻合；作「丙午」则差 2/2。"""
        c1 = CASES[0]
        with_typo = [(g, z) for g, z in c1["bazi"]]
        with_typo[2] = ("丙", "午")           # 底本原样
        self.assertEqual(self._td(with_typo), (42, 26),
                         "底本原样应为 天42 地26")
        self.assertEqual(self._td(c1["bazi"]), (44, 28),
                         "校正日柱后应为 天44 地28（与原典合）")
        self.assertNotEqual(self._td(with_typo), self._td(c1["bazi"]))


class TestOriginalCasesYuanQiTables(unittest.TestCase):
    """算例**逐句点名**的「年干／年支纳何卦」—— 直接校验引擎的元气表。

    四个算例的断语里都点了名：

    · L184「况**离是午人**，地支元气援己」        → 年支午 纳离
    · L185「有**乾**为元气，况**坎**相交初六」   → 年支亥 纳乾
    · L186「**丙人以艮为元气**，而**寅**生地支」 → 年干丙 纳艮、年支寅 纳艮
    · L187「**坎**又为**戊**生人之天元气，**子**人得坎又为地支元气」
                                             → 年干戊 纳坎、年支子 纳坎

    引擎 `yuan_qi.STEM_TO_TRIGRAM` / `BRANCH_TO_TRIGRAM` 必须与之一致。
    """

    #: 算例号 → {干/支: 该算例原典点名的卦}
    CLAIMED = {
        1: {"午": "离"},
        2: {"亥": "乾"},
        3: {"丙": "艮", "寅": "艮"},
        4: {"戊": "坎", "子": "坎"},
    }

    def test_tables_match_original_claims(self):
        from heluo_engine.engines.heluo.yuan_qi import (
            BRANCH_TO_TRIGRAM, STEM_TO_TRIGRAM,
        )
        for c in CASES:
            claimed = self.CLAIMED[c["no"]]
            with self.subTest(case=c["no"], line=c["line"]):
                for gz, want in claimed.items():
                    if gz in STEM_TO_TRIGRAM:
                        got = STEM_TO_TRIGRAM[gz]
                        kind = "年干"
                    else:
                        got = BRANCH_TO_TRIGRAM[gz]
                        kind = "年支"
                    self.assertEqual(got, want,
                                     f"算例{c['no']}（{c['line']}）{kind}{gz} "
                                     f"所纳之卦与原典不符")

    def test_all_claimed_entries_cover_both_tables(self):
        """上述断言须**同时**用到天干表与地支表（否则可能只验到一边）。"""
        from heluo_engine.engines.heluo.yuan_qi import (
            BRANCH_TO_TRIGRAM, STEM_TO_TRIGRAM,
        )
        stems = {gz for c in CASES for gz in self.CLAIMED[c["no"]] if gz in STEM_TO_TRIGRAM}
        branches = {gz for c in CASES for gz in self.CLAIMED[c["no"]] if gz in BRANCH_TO_TRIGRAM}
        self.assertGreaterEqual(len(stems), 2, "天干表的对拍点太少")
        self.assertGreaterEqual(len(branches), 3, "地支表的对拍点太少")


class TestCase5QiShaoL62(unittest.TestCase):
    """算例 5（起例卷之上 L62 + L95）：绍兴四年甲寅十月初四日申时生男。

    原典：
        「假令绍兴四年，甲寅，十月初四日申时生男，**命未得十月节气，只作九月论**。
          甲寅年甲戌月己卯日壬申时，**天数得二十有九**，除二十五还天正数外，
          余四数，得巽卦。**地数四十有八**，除三十还地正数外，余十八数，
          除十不用，只用八，得艮卦。**阳命男**，天数卦巽合在外，地数卦艮合在内，
          二篇之策演得**风山渐卦**是也。」
        L95：「假令前局甲寅年，甲戌月，己卯日，壬申时，演得风山渐，是**申时生人，
          申时是第三个阴时**，合在本卦**第三阴爻**为元堂也。**渐卦第三阴爻正是六四**」
    """

    BAZI = [("甲", "寅"), ("甲", "戌"), ("己", "卯"), ("壬", "申")]

    @classmethod
    def setUpClass(cls):
        cls.res = HeluoCanonical().calculate(
            bazi=cls.BAZI, gender="male", birth_hour="申", era="zhong",
            birth_year=1124)

    def test_tian_di_shu(self):
        n = self.res.numbers
        self.assertEqual((n.tian_shu, n.di_shu), (29, 48),
                         "算例5（起例卷之上 L62）天地二数与原典不符")

    def test_prenatal_hexagram(self):
        self.assertEqual(self.res.prenatal.hexagram_name, "风山渐",
                         "算例5 先天卦与原典不符")

    def test_yuantang(self):
        """申时是第三个阴时 → 渐卦第三阴爻 = 六四。"""
        self.assertEqual(self.res.yuantang.yuantang, "六四",
                         "算例5 元堂与原典（L95）不符")
        self.assertEqual(self.res.yuantang.yuantang_index, 3,
                         "六四 = 爻位索引 3")


class TestCase6DayunSwitchL136(unittest.TestCase):
    """算例 6（起例卷之上 L136）：渐卦元堂四爻，45 岁行尽，46 岁变入后天卦。

    原典：
        「假如前命得渐卦，上巽下艮，元堂在四爻，**其人至四十五岁行尽**。
          渐卦六爻气数**到四十六岁，却变入后天卦**，以上卦巽初爻变为乾，
          移入内为下卦，升下卦艮，移出外为上卦，是……」
        ⇒ 46 岁起的大运卦 = 上艮下乾 = **山天大畜**
    """

    BAZI = [("甲", "寅"), ("甲", "戌"), ("己", "卯"), ("壬", "申")]

    def test_dayun_switches_to_postnatal_at_46(self):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_dayun_liyao
        from heluo_engine.engines.heluo.yuan_tang import find_yuantang

        res = HeluoCanonical().calculate(
            bazi=self.BAZI, gender="male", birth_hour="申", era="zhong",
            birth_year=1124)
        pre = build_six_lines(res.prenatal.upper_gua, res.prenatal.lower_gua)
        post = build_six_lines(res.postnatal.upper_gua, res.postnatal.lower_gua)
        pyt = find_yuantang(six_lines=post, birth_hour="申", gender="male",
                             xiantian_name=res.postnatal.hexagram_name)
        dy = compute_dayun_liyao(pre, res.yuantang.yuantang_index, post,
                                  pyt.yuantang_index)

        xian_tian = [e for e in dy.sequence if e.phase == "先天"]
        hou_tian = [e for e in dy.sequence if e.phase == "后天"]
        self.assertTrue(xian_tian and hou_tian, "大运应分先天/后天两段")
        # 45 岁行尽 → 先天段最后一岁是 45
        self.assertEqual(xian_tian[-1].age_end, 45,
                         "先天段应止于 45 岁（原典「其人至四十五岁行尽」）")
        # 46 岁变入后天
        self.assertEqual(hou_tian[0].age_start, 46,
                         "后天段应起于 46 岁（原典「到四十六岁，却变入后天卦」）")
        self.assertEqual(hou_tian[0].hexagram_name, "山天大畜",
                         "46 岁起的后天大运卦与原典不符")

    def test_postnatal_hexagram_is_shantian_daxu(self):
        """原典的后天变法：上卦巽初爻变乾（移入内为下卦）、下卦艮移出为上卦
        ⇒ 上艮下乾 = 山天大畜。"""
        res = HeluoCanonical().calculate(
            bazi=self.BAZI, gender="male", birth_hour="申", era="zhong",
            birth_year=1124)
        self.assertEqual(res.postnatal.hexagram_name, "山天大畜",
                         "渐卦的后天卦与原典 L136 不符")


class TestCase8CeShuL117(unittest.TestCase):
    """算例 8（起例卷之下 L117）：睽九二爻的先天策数。

    原典：「假如睽九二爻祖数一百九十二……共得三千八百四十策。……共得四千二百二十四数。
    又加祖数一百九十二，合得四千四百一十六。又加外卦离三数，内卦兑二数，动爻二数，
    共合得**四千四百二十三数**。……以千为元，十为会，百为运，零为世」
    """

    def test_ce_shu_and_yuan_hui_yun_shi(self):
        from heluo_engine.engines.heluo.xian_tian_ce_shu import compute_xian_tian_ce_shu
        r = compute_xian_tian_ce_shu("睽", "离", "兑", 1, 192)
        self.assertEqual(r.ce_shu, 4423,
                         "睽九二爻策数与原典 L117 不符")
        self.assertEqual(r.yuan_hui_yun_shi, (4, 4, 2, 3),
                         "元会运世与原典「千为元、十为会、百为运、零为世」不符")

    def test_steps_record_original_figures(self):
        """逐段数字应与原典逐条对应（3840 / 4224 / 4416 / 4423）。"""
        from heluo_engine.engines.heluo.xian_tian_ce_shu import compute_xian_tian_ce_shu
        r = compute_xian_tian_ce_shu("睽", "离", "兑", 1, 192)
        joined = " ".join(r.steps)
        for frag in ("3840", "4224", "4416", "4423"):
            self.assertIn(frag, joined, f"推演步骤缺原典数字 {frag}")


class TestCase7CeShuRefusalKept(unittest.TestCase):
    """算例 7（起例卷之下 L115）：中孚上九爻 —— **引擎必须拒算**。

    原典自身对不上：
        「假如中孚上九爻……先下祖数一百二十九策，却以六爻六数因之，
          下六十个百为六千，次下六十个九十为五千四百，次下六个二十为一百二十，
          共计得**一万一千七百一十二策**。」
    按它自己写的分解式：60×100 + 60×90 + 6×20 = **11520**，与自述 11712 **差 192**，
    而 192 恰是**下一例（睽九二）的祖数** —— 疑为原典**串例**。

    引擎据此拒算（首段基数不可复算 → 策数与元会运世一律不给）。
    本类把**这个拒算钉死**：不得有人「好心」替它臆算出一个数来。
    """

    def test_engine_refuses_to_compute(self):
        from heluo_engine.engines.heluo.xian_tian_ce_shu import compute_shangti_ce_shu
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        self.assertEqual(r.ce_shu, 0,
                         "中孚上九一例原典自相矛盾，引擎不得给出策数")
        self.assertEqual(r.yuan_hui_yun_shi, (0, 0, 0, 0),
                         "拒算时元会运世也不得给出数值")

    def test_refusal_states_the_reason(self):
        """拒算必须**说明理由**（不得静默返回 0）。"""
        from heluo_engine.engines.heluo.xian_tian_ce_shu import compute_shangti_ce_shu
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        self.assertTrue(r.caveat, "拒算须留下说明")
        self.assertIn("11712", r.caveat, "拒算说明应点出原典自述数")
        self.assertIn("11520", r.caveat, "拒算说明应点出按原文分解式算出的数")
        self.assertIn("192", r.caveat, "拒算说明应点出差额 192（疑串例）")


class TestCase9LiuYueL124(unittest.TestCase):
    """算例 9（起例卷之上 L124 + L126）：起月卦例。

    原典：
        L124「凡起月卦，就年卦中前一位起，**单月变爻，双月变应爻**。
              假如**观卦上九爻**流年，**进一位从初爻变起**。」
        L126「又假如小象是**泰卦九二**，卦**应爻居五**，双月取应爻。」

    「进一位」= 爻位 +1（六爻循环，故上九的下一位是初爻）。

    「双月变应爻」的应爻基准已由《河洛理数》卷五「月卦」四组显式对拍裁定
    （见 TestCase12HeLuoLiShuYueGua）：取**当月阳月居位变爻**的隔三位应爻，
    而非元堂之应爻（若按元堂取，六个月双月将同变一爻，与该卷实证冲突）。
    """

    def test_guan_month_chain(self):
        """观卦上九爻为元堂：月1 变初爻、月2 变应爻、月3 变次爻。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_liuyue
        guan = build_six_lines("巽", "艮")          # 观卦
        res = compute_liuyue(guan, 5)               # 上九 = 爻位 5
        got = {m["month"]: m for m in res.months}
        # 进一位：上九(5) → 初爻(0)
        self.assertEqual(got[1]["yue_yao_index"], 0, "月1 应从初爻起")
        self.assertEqual(got[1]["name"], "风火家人",
                         "观卦单月变初爻 → 风火家人")
        # 双月变应爻：应爻 = 0 + 3
        self.assertEqual(got[2]["yue_yao_index"], 3, "月2 应变应爻（爻位3）")
        self.assertEqual(got[2]["name"], "天火同人",
                         "观卦双月变应爻 → 天火同人")
        # 次月再进一位
        self.assertEqual(got[3]["yue_yao_index"], 1, "月3 应进一位到爻位1")
        self.assertEqual(got[3]["name"], "风天小畜", "月3 卦名")

    def test_tai_ying_yao_at_five(self):
        """L126「又假如小象是泰卦九二，卦应爻居五，双月取应爻」。

        泰卦元堂在九二（爻位 1）：
          - 阳月居位 = 元堂 + 1、+2 … +6 = 三、四、五、上、初、二
          - 双月取「当月阳月居位变爻」的应爻（隔三位）= 上、初、二、三、四、五
        故走到居位九二的那一轮（十一月居位九二）之后，十二月双月取应爻
        1+3 = 4（五爻），与原典「卦应爻居五，双月取应爻」逐字吻合。
        """
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_liuyue
        tai = build_six_lines("坤", "乾")           # 泰卦
        res = compute_liuyue(tai, 1)                # 九二 = 爻位 1
        got = {m["month"]: m for m in res.months}
        yang = [got[m]["yue_yao_index"] for m in (1, 3, 5, 7, 9, 11)]
        self.assertEqual(yang, [2, 3, 4, 5, 0, 1],
                         "阳月居位 = 元堂九二 + 1…+6（三、四、五、上、初、二）")
        yin = [got[m]["yue_yao_index"] for m in (2, 4, 6, 8, 10, 12)]
        self.assertEqual(yin, [5, 0, 1, 2, 3, 4],
                         "双月取当月居位变爻的应爻（隔三位）")
        self.assertEqual(got[11]["yue_yao_index"], 1,
                         "十一月居位应落在九二")
        self.assertEqual(got[12]["yue_yao_index"], 4,
                         "十二月双月取九二的应爻，居五（爻位4）")


class TestCase12HeLuoLiShuYueGua(unittest.TestCase):
    """算例 12（《河洛理数》卷五「月卦」K3-447/448）：起月卦的显式逐月对拍。

    《河洛理数》月卦卷给出四组「阳月居位 → 双月所取应爻」的实例
    （K3-448 修正版 L469-L471；K3-447 修正版 L1132-L1146）：

        「如前五月是**小畜三爻**，六月则取**小畜应爻上九**」
        「如前七月是**乾九四**，八月则取**乾卦应爻初九**」
        「九月……**大有六五**……取**大有应爻**……**离卦六二**」
        「如前十一月是**大壮上爻**，则十二月取**大壮应爻**……**归妹六三**」

    四组一律是「双月 = 当月阳月居位变爻的隔三位应爻」，且该链阳月居位序为
    上爻 → 初、二、三、四、五、上（即元堂 + 1…+6），与引擎口径逐字吻合。
    """

    def test_yin_yang_month_ying_yao_pairs(self):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_liuyue
        kun = build_six_lines("坤", "坤")           # 坤为地（纯阴，年卦本身不入判）
        res = compute_liuyue(kun, 5)               # 元堂在上爻
        got = {m["month"]: m for m in res.months}
        yang = [got[m]["yue_yao_index"] for m in (1, 3, 5, 7, 9, 11)]
        self.assertEqual(yang, [0, 1, 2, 3, 4, 5],
                         "阳月居位 = 元堂上爻 + 1…+6（初、二、三、四、五、上）")
        # 四组显式对拍：阳月居位 → 紧随其后的双月所取应爻
        for yang_m, yin_m, yao, ying in (
            (5, 6, 2, 5),    # 小畜三爻 → 六月取小畜应爻上九
            (7, 8, 3, 0),    # 乾九四 → 八月取乾卦应爻初九
            (9, 10, 4, 1),   # 大有六五 → 十月取大有应爻（离卦六二）
            (11, 12, 5, 2),  # 大壮上爻 → 十二月取大壮应爻（归妹六三）
        ):
            self.assertEqual(got[yang_m]["yue_yao_index"], yao,
                             f"第{yang_m}月（阳月）居位")
            self.assertEqual(got[yin_m]["yue_yao_index"], ying,
                             f"第{yin_m}月（双月）应取居位爻的隔三位应爻")


class TestCase10LiuRiL129(unittest.TestCase):
    """算例 10（起例卷之上 L129）：起日卦例（hou5 原典链）。

    原典：「假如正月得**乾卦初爻**，初一日当在**三爻**，变为**履六三**，
    初二日变履九四为**中孚六四**，初三日变中孚九五为**损六五**，
    初四日变损上九为**临上六**，初五日变临初九为**师初六**，挨次而变，不容紊也。」
    """

    def test_five_day_chain_verbatim(self):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            _lines_to_hexagram, liuri_day_lines, liuri_day_positions,
        )
        qian = build_six_lines("乾", "乾")
        # 逐日爻位：初一起自下一爻，阳日寻阳位（初/三/五）、阴日寻阴位（二/四/上）
        self.assertEqual(liuri_day_positions(0)[:5], [2, 3, 4, 5, 0],
                         "逐日爻位应与原典逐字对应（三/四/五/上/初）")
        chain = liuri_day_lines(qian, 0)
        want = ["天泽履", "风泽中孚", "山泽损", "地泽临", "地水师"]
        for i, w in enumerate(want):
            with self.subTest(day=i + 1):
                pos, lines = chain[i]
                self.assertEqual(_lines_to_hexagram(lines)[2], w,
                                 f"第{i + 1}日卦名与原典不符")


class TestCase11PureHexagramYuantang(unittest.TestCase):
    """算例 11（起例卷之上 L98 / L99）：纯卦（乾/坤）的元堂行向。

    原典：
        L98「假令**男得乾卦纯阳**，不问阴阳，但十二时**皆自下而上行**，**子午皆在初爻**。
              如**女得乾卦**，生冬至以后，至夏至以前，**自上九为始，往下行**至初爻。
              若生夏至以后，至冬至以前，当**自初九为始，往上行**至上九。」
        L99「假令**女得坤卦纯阴**，不问阴阳，但十二时**皆自下而上**……
              如**男得坤卦**，生冬至以后，夏至以前，**自上六行至初六**，
              夏至以后，冬至以前，当**自下而上行**。」
    """

    def _yuan_tang(self, gua, gender, hour, phase):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.yuan_tang import find_yuantang
        lines = build_six_lines("乾", "乾") if gua == "乾" else build_six_lines("坤", "坤")
        r = find_yuantang(six_lines=lines, birth_hour=hour, gender=gender,
                          xiantian_name=gua, solar_phase=phase)
        return r.yuantang

    def test_male_qian_always_from_below(self):
        """男得乾：十二时皆自下而上行，子午皆在初爻。"""
        self.assertEqual(self._yuan_tang("乾", "male", "午", "winter"), "初九")
        self.assertEqual(self._yuan_tang("乾", "male", "午", "summer"), "初九")
        self.assertEqual(self._yuan_tang("乾", "male", "子", "winter"), "初九")

    def test_female_qian_direction_by_season(self):
        """女得乾：冬至后→夏至前自上九而下行；夏至后→冬至前自初九而上行。"""
        self.assertEqual(self._yuan_tang("乾", "female", "午", "winter"), "上九")
        self.assertEqual(self._yuan_tang("乾", "female", "午", "summer"), "初九")

    def test_male_kun_direction_by_season(self):
        """男得坤：冬至后→夏至前自上六而下行；夏至后→冬至前自下而上行。"""
        self.assertEqual(self._yuan_tang("坤", "male", "午", "winter"), "上六")
        self.assertEqual(self._yuan_tang("坤", "male", "午", "summer"), "初六")

    def test_female_kun_always_from_below(self):
        """女得坤：不问阴阳，十二时皆自下而上。"""
        self.assertEqual(self._yuan_tang("坤", "female", "午", "winter"), "初六")
        self.assertEqual(self._yuan_tang("坤", "female", "午", "summer"), "初六")


class TestNewCaseQuotesInRepo(unittest.TestCase):
    """新增算例（起例卷之上 L62/L95/L136、起例卷之下 L115/L117）的原文在库。"""

    def test_shangjuan_quotes(self):
        raw = (Path(__file__).resolve().parents[2]
               / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之上.txt")
        text = raw.read_text(encoding="utf-8")
        for frag in (
            "假令绍兴四年，甲寅，十月初四日申时生男，命未得十月节气，只作九月论",
            "甲寅年甲戌月己卯日壬申时，天数得二十有九",
            "地数四十有八",
            "二篇之策演得风山渐卦是也",
            "申时是第三个阴时",
            "渐卦第三阴爻正是六四",
            "假如前命得渐卦，上巽下艮，元堂在四爻，其人至四十五岁行尽",
            "渐卦六爻气数到四十六岁，却变入后天卦",
        ):
            self.assertIn(frag, text, f"起例卷之上原文缺失：{frag}")

    def test_xiajuan_quotes(self):
        raw = (Path(__file__).resolve().parents[2]
               / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之下.txt")
        text = raw.read_text(encoding="utf-8")
        for frag in (
            "假如中孚上九爻四阳二阴之卦",
            "共计得一万一千七百一十二策",
            "假如睽九二爻祖数一百九十二",
            "共合得四千四百二十三数",
        ):
            self.assertIn(frag, text, f"起例卷之下原文缺失：{frag}")


class TestOriginalCasesAreInRepo(unittest.TestCase):
    """四个算例的原文必须在库（可逐字回查）。"""

    def test_quotes_present_verbatim(self):
        raw = (Path(__file__).resolve().parents[2]
               / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之中.txt")
        text = raw.read_text(encoding="utf-8")
        self.assertIn("先贤命格假令例", text, "原典「先贤命格假令例」标题缺失")
        for c in CASES:
            with self.subTest(case=c["no"]):
                # 取算例原文的首句与关键数字句
                for frag in c["quote"].split("……")[0].rstrip("，"):
                    self.assertIn(frag, text,
                                  f"算例{c['no']}（{c['line']}）原文缺失：{frag}")

    def test_case1_ganzhi_typo_documented(self):
        """算例 1 的底本讹字（丙午→丙申）必须**留在原文里**，不得被订正。

        原文录入是**逐字照抄**，讹字照录；订正只在守卫与对照表里说明。
        """
        raw = (Path(__file__).resolve().parents[2]
               / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之中.txt")
        text = raw.read_text(encoding="utf-8")
        self.assertIn("命庚午甲申丙午丁酉", text,
                      "底本原样应保留「丙午」（逐字照抄，讹字不订正）")


class TestCase13HeLuoLiShuLiUriCase(unittest.TestCase):
    """算例 13（《河洛理数》卷五「日卦起例卷」K3-448/K3-447）：万历二十三年七月流日卦例。

    原典（逐字，底本 OCR 讹字照录）：
        「日卦者每月變五卦每卦管六日方成一月」（K3-447 L1154）
        「假如七月月得既濟六二爻除此一爻不變先將既濟九三爻變為屯卦管六日
          再將月卦上六爻變為家人管六日」（K3-447 L1153/L1158）
        「…只將既濟九三變為屯卦…屯卦六爻從下而上一爻一日自初二日至初七
          卦二爻管初三日屯卦三爻管初四日卦四爻管初五日卦五爻管初六日…」
          （K3-448 L478-L480）
        「至初八日又變前既濟卦…為革卦…此一卦自下而上」（K3-448 L477）
        「至十四日又變前既卦九五爻為明夷六五自下而上」（K3-448 L483）
        「如本年七月初二日午時交立秋節…日卦行起必須按月卦節氣方不[誤]」
          （K3-448 L481-L482）
        「以此推之則每日添一刻七分天」（K3-448 L491）

    **2026-10-22 发现并修正的引擎缺陷**：流日 5 段本卦原取链式累变的
    ``day_lines[k*6]``（《河洛真数》hou5 的链），在 gua6 口径下产出**退化序列**
    （既济·居位二爻 → 屯、鼎、屯、鼎、屯）。原典明文：五卦是月卦**各变一爻**
    （居位爻不动），变爻序 = 爻位顺序跳过居位（既济·二爻 → 屯、革、明夷、家人、蹇），
    且段2/段3 的段序由日算互证（初八 = 初二+6、十四 = 初二+12）。
    """

    def test_five_bases_match_original(self):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            liuri_gua6_bases, _lines_to_hexagram,
        )
        ji = build_six_lines("坎", "离")          # 既济（坎上离下）
        names = [_lines_to_hexagram(b)[2] for b in liuri_gua6_bases(ji, 1)]
        self.assertEqual(names,
                         ["水雷屯", "泽火革", "地火明夷", "风火家人", "水山蹇"],
                         "既济·居位二爻 的五段本卦应逐字等于原典")

    def test_yue_yao_never_flipped(self):
        """「除此一爻不變」：居位爻在五段中始终不变。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import liuri_gua6_bases
        ji = build_six_lines("坎", "离")
        for base in liuri_gua6_bases(ji, 1):
            self.assertEqual(base[1], ji[1], "居位二爻不得被变")

    def test_segment_six_days_and_sequential_yao(self):
        """每卦管六日；段内自下而上一爻一日（初二→初七 = 初九→上六）。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            liuri_gua6_bases, _flip_line, _lines_to_hexagram,
        )
        ji = build_six_lines("坎", "离")
        base = liuri_gua6_bases(ji, 1)[0]         # 段1 = 屯
        # 段内自下而上一爻一日：段首日「屯卦初九爻」（原典「初二日午前屯卦初九爻
        # 即从初二日午时管起」），逐日翻下一爻 → 动爻依次 初六、九二、九三、九四、
        # 九五、上六（即 屯卦各爻取反）
        yao_seq = [_flip_line(list(base), d)[d] for d in range(6)]
        self.assertEqual(yao_seq, [-1, 1, 1, 1, -1, 1],
                         "段内六日动爻应逐日取初→上（屯：初六/九二/九三/九四/九五/上六）")
        self.assertEqual(base[0], 1, "段首日居位应为屯卦初九")


class TestCase14QiShiL124(unittest.TestCase):
    """算例 14（《河洛真数》起例卷之上 L402 起时卦例）：流时卦十二时。

    原典（逐字）：
        「凡起时卦，于日中寻时，就值日卦上从前一爻起，子丑寅卯辰巳六时，
          主进数变去；值日卦后一爻起，午未申酉戌亥六时，主退数变去。
          假如得乾卦初爻值日，则从二爻变起。
          又云，日卦变时卦，与年卦变月卦同。但子寅辰午申戌居左，变爻用点，
          丑卯巳未酉亥居右取应，变爻不同点。凡居位进一爻起，子时其应爻则丑时也。
          假令乾卦初九居位，进一爻起数。自下而上挨次变去，取变卦应爻变之。
          **二法皆通，前法为优，学者详之。**」

    **2026-10-22 案例验证发现**：引擎原实现把两法**混用**（前六时用后法的
    阴阳时分配、后六时用「退数 + 阴时取应」的第三种组合），十二时中只有
    子、午两时与原典前法相符 —— 既不是前法，也不是后法；该层因此在
    2026-10-06 被整段剥离。

    **2026-10-22 用户裁决：「不要算流时卦，到流日就可以」** —— 故本类把两件事
    都钉住：
      · **算法本体**（``timeline_yun.compute_liushi``）按「**前法为优**」更正，
        不在代码里留一颗「看着能用、实则两法混用」的地雷（将来若启用，口径已对）；
      · **生产链维持剥离**：流时恒空，传 target_hour 只留痕、不产出。
    """

    #: 乾初爻值日 → 前法十二时（卦名、变爻位）——「前法」逐时对拍
    QIAN_CASES = [
        ("子", "天火同人", 1), ("丑", "天雷无妄", 2), ("寅", "风雷益", 3),
        ("卯", "山雷颐", 4), ("辰", "地雷复", 5), ("巳", "坤为地", 0),
        ("午", "泽天夬", 5), ("未", "雷天大壮", 4), ("申", "地天泰", 3),
        ("酉", "地泽临", 2), ("戌", "地雷复", 1), ("亥", "坤为地", 0),
    ]

    def test_qian_method_twelve_hours(self):
        """前法：子…巳 进数、午…亥 退数，十二时皆变爻。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_liushi
        qian = build_six_lines("乾", "乾")
        r = compute_liushi(qian, 0)             # 乾初爻值日
        got = {h["hour"]: (h["name"], h["shi_yao_index"]) for h in r.hours}
        for i, (shi, name, yao) in enumerate(self.QIAN_CASES):
            with self.subTest(hour=shi):
                self.assertEqual(got[i + 1][0], name, f"{shi}时卦名")
                self.assertEqual(got[i + 1][1], yao, f"{shi}时变爻位")

    def test_original_instance_two_hours(self):
        """原典实例：乾初爻值日 → 子时变二爻（天火同人）、午时变上爻（泽天夬）。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import compute_liushi
        r = compute_liushi(build_six_lines("乾", "乾"), 0)
        got = {h["hour"]: (h["name"], h["shi_yao_index"]) for h in r.hours}
        self.assertEqual(got[1], ("天火同人", 1), "子时应变二爻")
        self.assertEqual(got[7], ("泽天夬", 5), "午时应变上爻")

    def test_hou_method_kept_as_variant(self):
        """后法（又云）留档：阳时链式变爻、阴时取应。"""
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            LIUSHI_METHOD_HOU, compute_liushi,
        )
        r = compute_liushi(build_six_lines("乾", "乾"), 0,
                           method=LIUSHI_METHOD_HOU)
        got = {h["hour"]: (h["name"], h["shi_yao_index"]) for h in r.hours}
        # 后法：阳时子寅辰午申戌 = 变爻 1,2,3,4,5,0；阴时取应（+3）
        self.assertEqual([got[h][1] for h in (1, 3, 5, 7, 9, 11)],
                         [1, 2, 3, 4, 5, 0])
        self.assertEqual([got[h][1] for h in (2, 4, 6, 8, 10, 12)],
                         [4, 5, 0, 1, 2, 3])
        self.assertNotEqual(got[1][0], got[2][0], "后法阴时取应，不得与阳时同卦")

    def test_guajie_hour_layer_stays_stripped(self):
        """生产层**维持剥离**（用户裁决「不要算流时卦，到流日就可以」）。

        传 target_hour 仍须**明确留痕**（不得静默忽略），但不产出流时卦/爻辞。
        """
        from heluo_engine.engines.heluo.canonical import HeluoCanonical
        from heluo_engine.engines.heluo import guajie as gj
        bazi = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
        res = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="午", era="zhong",
            birth_date="1983-11-03", target_year=2026, target_month=6,
            target_day=15)
        out = gj.build_guajie_from_result(
            res, bazi=bazi, target_year=2026, target_month=6, target_day=15,
            target_hour=7)
        self.assertEqual(out["liushi_hexagram"], "", "流时层应维持剥离（到流日为止）")
        self.assertIsNone(out["liushi_yao"])
        self.assertTrue(any("流时：已剥离" in e for e in out["evidence"]),
                        "传 target_hour 必须留痕，不得静默忽略")
        # 到流日为止：流年/流月/流日三层仍须正确定位
        self.assertTrue(out["liuri_hexagram"], "流日仍应定位")
        out2 = gj.build_guajie_from_result(
            res, bazi=bazi, target_year=2026, target_month=6, target_day=15)
        self.assertFalse(out2["liushi_hexagram"])
        self.assertFalse(any("流时：已剥离" in e for e in out2["evidence"]),
                         "未传 target_hour 时无需留痕")


class TestCase15XiaoXiangL366(unittest.TestCase):
    """算例 15（《河洛真数》起例卷之上 L366 小象行年卦气）：流年卦链三条九年链。

    原典（逐字）：
        「其一年变一卦之法，亦自本卦之爻而始。假如同人九三爻是元堂，其阳爻
          九年者，此大象也。其小象当看此年是阳是阴，如此年是阳年，则不变。
          一岁在同人九三元爻，二岁取应爻，变同人上九为革上六，三岁复取应爻，
          变革九三为随六三，然后自下而上，四岁变随九四为屯六四，五岁变屯九五
          为复六五，六岁变复上六为颐上九，七岁变颐初九为剥初六，八岁变剥六二
          为蒙九二，九岁变蒙六三为蛊九三，此阳年九爻变例也。」（阳年链）
        「…如一岁是阴年…此年当变为无妄六三。二岁取应爻，变无妄上九为随上六，
          三岁复取应爻，变随六三为革九三，然后自下而上，四岁变既济六四，五岁变
          明夷六五，六岁变贲上九，七岁变艮初六，八岁变蛊九二，九岁变蒙六三，
          此同人九三阴年小象九年变例也。」（阴年链）
        「…九四爻…如一岁是阳，不变，仍用九四元爻断，次年取应爻，变同人初九为
          遁初六，三年又取应爻，变遁九四为渐六四，四岁挨次变去，自下而上，
          变渐九五为艮六五，五岁变谦上六，六岁变明夷初九，七岁变泰九二，
          八岁变临六三，九岁变归妹九四。」（九四·阳年链）

    这三条链是引擎**流年卦层**最核心的判据，此前无任何原典算例把关。
    """

    TONGREN = ("乾", "离")     # 同人（乾上离下）

    #: 三条链的期望（卦名 + 动爻），顺序 = 一岁…九岁
    CHAINS = [
        ("同人九三·阳年", 2, 1990, [
            "同人九三", "革上六", "随六三", "屯六四", "复六五",
            "颐上九", "剥初六", "蒙九二", "蛊九三"]),
        ("同人九三·阴年", 2, 1991, [
            "无妄六三", "随上六", "革九三", "既济六四", "明夷六五",
            "贲上九", "艮初六", "蛊九二", "蒙六三"]),
        ("同人九四·阳年", 3, 1990, [
            "同人九四", "遁初六", "渐六四", "艮六五", "谦上六",
            "明夷初九", "泰九二", "临六三", "归妹九四"]),
    ]

    def _run_chain(self, yt_index, birth_year):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            compute_dayun_liyao, compute_liunian,
        )
        lines = build_six_lines(*self.TONGREN)
        dayun = compute_dayun_liyao(lines, yt_index, lines, yt_index)
        res = compute_liunian(lines, yt_index, lines, yt_index,
                              birth_year=birth_year, age_from=1, age_to=9,
                              dayun=dayun)
        out = []
        prev = None
        for y in res.years:
            idx = yt_index if prev is None else next(
                (k for k in range(6) if y.lines[k] != prev[k]), None)
            pos = "初二三四五上"[idx] if idx is not None else ""
            short = (y.hexagram_name[0] if "为" in y.hexagram_name
                     else y.hexagram_name[2:])
            # 原典（《周易》）爻名格式：初/上 **位在前**（初九、上六），
            # 二三四五 **性质在前**（九三、六二）
            if idx is None:
                yao = ""
            else:
                pos = "初二三四五上"[idx]
                nat = "九" if y.lines[idx] > 0 else "六"
                yao = f"{pos}{nat}" if idx in (0, 5) else f"{nat}{pos}"
            out.append(f"{short}{yao}")
            prev = y.lines
        return out, res

    def test_three_chains_match_original(self):
        for label, yt, birth_year, expect in self.CHAINS:
            with self.subTest(chain=label):
                got, _ = self._run_chain(yt, birth_year)
                self.assertEqual(got, expect,
                                 f"{label} 的九年流年卦链应逐字等于原典")


class TestCase16YuanTangL98(unittest.TestCase):
    """算例 16（《河洛真数》起例卷之上 L98-L99 定元堂式）：元堂十一个举例。

    原典（逐字）：
        「如亥时生人得小畜，午未同在六四，申九五，酉上九，戌初九，亥九二是也。
          戌时生得讼，午初六，未六三，申复初六，酉复六三，戌九四是也。
          亥时生得咸，亥在上六是也。戌时得明夷，元堂初九是也。
          亥时得颐，元堂初九是也。亥时得升，元堂九三是也。
          亥时得谦，元堂九三是也。巳时生得屯，元堂六二是也。
          巳时生得既济，元堂九五是也。巳时生得大过，元堂在初六。
          巳时生得遁，元堂在六二。」

    六爻一律取自**引擎自己的六十四卦表**（不手抄卦序），验的是元堂定法本身。
    """

    CASES = [
        ("小畜", "亥", "九二"), ("讼", "戌", "九四"), ("咸", "亥", "上六"),
        ("明夷", "戌", "初九"), ("颐", "亥", "初九"), ("升", "亥", "九三"),
        ("谦", "亥", "九三"), ("屯", "巳", "六二"), ("既济", "巳", "九五"),
        ("大过", "巳", "初六"), ("遁", "巳", "六二"),
    ]

    def test_yuantang_eleven_examples(self):
        from heluo_engine.engines.heluo.numbers import (
            SIXTY_FOUR_HEXAGRAMS, build_six_lines,
        )
        from heluo_engine.engines.heluo.yuan_tang import find_yuantang
        name2ul = {}
        for (up, lo), full in SIXTY_FOUR_HEXAGRAMS.items():
            name2ul[full[0] if "为" in full else full[2:]] = (up, lo)
        for name, hour, expect in self.CASES:
            with self.subTest(gua=name, hour=hour):
                up, lo = name2ul[name]
                r = find_yuantang(six_lines=build_six_lines(up, lo),
                                  birth_hour=hour, gender="male",
                                  xiantian_name=name)
                self.assertEqual(r.yuantang, expect,
                                 f"{name} {hour}时的元堂应逐字等于原典")


class TestCase17GuaQiMonthTable(unittest.TestCase):
    """算例 17（《河洛真数》起例卷之中 月令消息论）：十二月卦气表。

    原典（逐字）：
        「泰属正月雨水节，三阳出于寅…大壮属二月春分节…夬属三月谷雨节…
          乾属四月小满节…姤属五月夏至节…遁属六月大暑节…否属七月处暑节…
          观属八月秋分节…剥属九月霜降节…坤属十月…复属十一月冬至候…
          临属十二月大寒节…」
    """

    def test_twelve_month_guaqi(self):
        from heluo_engine.engines.heluo.guajie import GUA_QI_MONTH_TABLE
        expect = {1: ("雨水", "泰"), 2: ("春分", "大壮"), 3: ("谷雨", "夬"),
                  4: ("小满", "乾"), 5: ("夏至", "姤"), 6: ("大暑", "遁"),
                  7: ("处暑", "否"), 8: ("秋分", "观"), 9: ("霜降", "剥"),
                  10: ("—", "坤"), 11: ("冬至", "复"), 12: ("大寒", "临")}
        for month, (jie, gua) in expect.items():
            with self.subTest(month=month):
                got = GUA_QI_MONTH_TABLE.get(month)
                self.assertIsNotNone(got, f"{month}月卦气缺失")
                self.assertEqual(got[0], jie, f"{month}月节气锚点")
                self.assertEqual(got[1], gua, f"{month}月卦气卦名")


class TestCase18YinYaoSixYearChain(unittest.TestCase):
    """算例 18（《河洛真数》起例卷之上 L366）：阴爻六年游链。

    原典（逐字）：
        「假如同人六二爻为元堂，则一变为乾九二，再变为履六三，三变为中孚六四，
          四变为损六五，五变为临上六，六变为师初六，一年变一爻为一卦，馀仿此。」

    阴爻大运段（6 年）**不分阳年阴年**（原典此例无分支）—— 故两种出生年
    应给出同一条链。
    """

    EXPECT = ["乾九二", "履六三", "中孚六四", "损六五", "临上六", "师初六"]

    def _run(self, birth_year):
        from heluo_engine.engines.heluo.numbers import build_six_lines
        from heluo_engine.engines.heluo.timeline_yun import (
            compute_dayun_liyao, compute_liunian,
        )
        lines = build_six_lines("乾", "离")          # 同人
        dayun = compute_dayun_liyao(lines, 1, lines, 1)
        res = compute_liunian(lines, 1, lines, 1, birth_year=birth_year,
                              age_from=1, age_to=6, dayun=dayun)
        out = []
        prev = None
        for y in res.years:
            idx = 1 if prev is None else next(
                (k for k in range(6) if y.lines[k] != prev[k]), None)
            short = (y.hexagram_name[0] if "为" in y.hexagram_name
                     else y.hexagram_name[2:])
            if idx is None:
                yao = ""
            else:
                pos = "初二三四五上"[idx]
                nat = "九" if y.lines[idx] > 0 else "六"
                yao = f"{pos}{nat}" if idx in (0, 5) else f"{nat}{pos}"
            out.append(f"{short}{yao}")
            prev = y.lines
        return out

    def test_six_year_chain(self):
        for birth_year in (1990, 1991):
            with self.subTest(birth_year=birth_year):
                self.assertEqual(self._run(birth_year), self.EXPECT,
                                 "阴爻六年游链应逐字等于原典")


if __name__ == "__main__":
    unittest.main()
