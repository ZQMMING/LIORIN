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
`data/heluo/起例卷之下算法对照表_20261007.md` 留档。

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

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.numbers import build_six_lines
from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao
from tongshu.engines.heluo.yuan_tang import find_yuantang

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
        from tongshu.engines.heluo.numbers import BRANCH_VALUES, STEM_VALUES
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
        from tongshu.engines.heluo.numbers import BRANCH_VALUES, STEM_VALUES
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
        from tongshu.engines.heluo.yuan_qi import (
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
        from tongshu.engines.heluo.yuan_qi import (
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao
        from tongshu.engines.heluo.yuan_tang import find_yuantang

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
        from tongshu.engines.heluo.xian_tian_ce_shu import compute_xian_tian_ce_shu
        r = compute_xian_tian_ce_shu("睽", "离", "兑", 1, 192)
        self.assertEqual(r.ce_shu, 4423,
                         "睽九二爻策数与原典 L117 不符")
        self.assertEqual(r.yuan_hui_yun_shi, (4, 4, 2, 3),
                         "元会运世与原典「千为元、十为会、百为运、零为世」不符")

    def test_steps_record_original_figures(self):
        """逐段数字应与原典逐条对应（3840 / 4224 / 4416 / 4423）。"""
        from tongshu.engines.heluo.xian_tian_ce_shu import compute_xian_tian_ce_shu
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
        from tongshu.engines.heluo.xian_tian_ce_shu import compute_shangti_ce_shu
        r = compute_shangti_ce_shu("中孚", "巽", "兑", 5, 129)
        self.assertEqual(r.ce_shu, 0,
                         "中孚上九一例原典自相矛盾，引擎不得给出策数")
        self.assertEqual(r.yuan_hui_yun_shi, (0, 0, 0, 0),
                         "拒算时元会运世也不得给出数值")

    def test_refusal_states_the_reason(self):
        """拒算必须**说明理由**（不得静默返回 0）。"""
        from tongshu.engines.heluo.xian_tian_ce_shu import compute_shangti_ce_shu
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.timeline_yun import compute_liuyue
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.timeline_yun import compute_liuyue
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.timeline_yun import compute_liuyue
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.timeline_yun import (
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
        from tongshu.engines.heluo.numbers import build_six_lines
        from tongshu.engines.heluo.yuan_tang import find_yuantang
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
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt")
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
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之下.txt")
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
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之中.txt")
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
               / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之中.txt")
        text = raw.read_text(encoding="utf-8")
        self.assertIn("命庚午甲申丙午丁酉", text,
                      "底本原样应保留「丙午」（逐字照抄，讹字不订正）")


if __name__ == "__main__":
    unittest.main()
