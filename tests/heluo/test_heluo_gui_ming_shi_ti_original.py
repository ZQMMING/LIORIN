# -*- coding: utf-8 -*-
"""贵命十体：**逐条对拍原典**《河洛真数·起例卷之上》L209-L224（2026-10-22）。

**本文件锁的是「权威是哪一套」这个曾经悬着的问题。**

2026-10-22 逐字核实结论（此前仓里有两套实现，体检报告判为「口径冲突、
需原典裁定」）：

  · 原典的正式条目是 **《河洛真数·起例卷之上》L209「贵命十体」**，
    十项齐全（L210-L219）+ 分级（L220）+ 贱命十体（L221-L224）。
  · `guajie.judge_gui_ming_shi_ti` / `judge_jian_ming_shi_ti` 实现的正是这
    **十项全套** → **它就是权威**，生产链在用它。
  · `gui_ming_liu_ju.judge_liu_ju` 的六项**恰是本十项的前六项（①~⑥）**，
    不是另一套规则；其行号 L633-L648 指向**另一底本**。
    → 该模块降为「前六项子集转录，留档与对拍用」，不作生产口径。

本文件把十项的**原文**与**实现的判据名**逐条钉死，并锁住三处易漂移处：
  ① 卦名「之类」= 举例未穷举 → 未举例之卦**不判吉也不判凶**
  ③ 辞吉按**词组**「元吉/亨利」命中（单字匹配会几乎恒中）
  ④ 得时须覆盖原文明文的两类（季正卦 + 卦气月）
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo import guajie as g
from tongshu.engines.heluo import gui_ming_liu_ju as lmj

_RAW = (Path(__file__).resolve().parents[2]
        / "data" / "heluo" / "guajie_raw" / "河洛真数_起例卷之上.txt")


def _text() -> str:
    return _RAW.read_text(encoding="utf-8")


class TestOriginalTextIsInRepo(unittest.TestCase):
    """贵命十体原文必须在库（可逐字回查）。"""

    def test_ten_items_present_verbatim(self):
        text = _text()
        for frag in (
            "贵命十体",
            "一卦名吉。（如泰、大有、同人、晋、豫之类是也。）",
            "二爻吉。（如元堂住在二五爻是也。）",
            "三辞吉。（卦爻中有元吉亨利是也。）",
            "四得时。（如春震木、夏离火、秋兑金、冬坎水之类。"
            "又如正月得泰卦、九月得剥卦之类皆是。）",
            "五有援。（谓元堂在阳爻，应爻得阴，或元堂在阴爻，而应爻得阳是也。）",
            "六顺时。（谓天地二数多寡与时偕行。"
            "如正月生人得天数多地数少，九月生人得地数多人数少是也。）",
            "七得体。",
            "八当位。",
            "九合理。",
            "十众宗。",
        ):
            self.assertIn(frag, text, f"贵命十体原文缺失：{frag}")

    def test_grading_and_jianming_present(self):
        text = _text()
        for frag in ("得三四者选曹命，得五六者如通命，得七八者乡监侍从，得九十者将相侯王",
                     "贱命十体皆与十贵相反是也",
                     "一卦名凶", "二爻位凶", "三辞凶", "四不得时", "五无援",
                     "得三四者，僧道九流之命"):
            self.assertIn(frag, text, f"十体分级/贱命条文缺失：{frag}")


class TestTenItemsAreWhatOriginalSays(unittest.TestCase):
    """十项判据名与原典逐条对应。"""

    def test_gui_ming_item_labels(self):
        """贵命十体产出的十项标记与原典十项一一对应。

        注：\`yao_lines\` 是 **1 阳 / 0 阴**（guajie._TRI_LINES 约定），
        泰 = 上坤下乾 = [1,1,1] + [0,0,0]；元堂九二（阳）对应应爻四爻（阴）
        → ⑤有援成立（原典 L214「元堂在阳爻，应爻得阴」）。
        """
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="泰", yuantang_yao="九二",
            yao_cis=["九二：亨利，小往大来"], yao_lines=[1, 1, 1, 0, 0, 0],
            birth_month_branch="寅", gua_qi_month=1,
            tian_shu=30, di_shu=20, year_gan="癸", year_zhi="亥",
        )
        joined = "；".join(out)
        for label in ("①卦名吉", "②爻吉", "③辞吉", "④得时", "⑤有援", "⑥顺时"):
            self.assertIn(label, joined, f"贵命十体缺 {label}")

    def test_ten_item_labels_are_numbered_1_to_10(self):
        """十项用 ①-⑩ 编号，不多不少。"""
        src = g.judge_gui_ming_shi_ti.__doc__ or ""
        for i in "①②③④⑤⑥⑦⑧⑨⑩":
            self.assertIn(i, src or "", f"缺 {i}")

    def test_liu_ju_module_is_the_same_six_items(self):
        """gui_ming_liu_ju 的六项 = 贵命十项的前六项（同一套规则）。"""
        self.assertEqual(list(lmj.LIU_JU.keys()),
                         ["卦名", "爻位", "爻辞", "得时", "有援", "顺时"],
                         "该模块六项应恰是十体的前六项")


class TestItem1GuaNameIsNotJudgedOutsideExamples(unittest.TestCase):
    """① 卦名：原典用「之类」= 举例未穷举 → 未举例之卦不判吉、亦不判凶。"""

    def test_gui_ming_does_not_judge_outside_examples(self):
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="乾", yuantang_yao="九二",
            yao_cis=["九二：亨"], yao_lines=[0, 1, 0, 1, 1, 1],
            birth_month_branch="寅", gua_qi_month=4,
            tian_shu=30, di_shu=20, year_gan="癸", year_zhi="亥",
        )
        joined = "；".join(out)
        self.assertIn("①卦名不判", joined, "未举例之卦应留痕「不判」")
        self.assertNotIn("①卦名吉", joined, "乾不在明举例内，不得判吉")

    def test_jian_ming_does_not_judge_gua_name_wrong(self):
        """贱命十体不得产出「①卦名凶」—— 「取反」无从取起。"""
        out = g.judge_jian_ming_shi_ti(
            prenatal_name="乾", yuantang_yao="初六",
            yao_cis=["初六：凶"], yao_lines=[0, 0, 0, 0, 0, 1],
            birth_month_branch="午", gua_qi_month=4,
            tian_shu=20, di_shu=35, year_gan="庚", year_zhi="申",
        )
        joined = "；".join(out)
        self.assertNotIn("①卦名凶", joined, "原典「之类」不得据此判凶")
        self.assertIn("①卦名不判", joined)


class TestItem3CiUsesWordGroups(unittest.TestCase):
    """③ 辞吉：按词组「元吉/亨利」命中（单字口径实测几乎恒真）。"""

    def test_word_group_chars(self):
        self.assertEqual(g._GUI_JI_CI_GOOD_CHARS, ("元吉", "亨利"))

    def test_single_char_hits_are_almost_always_true(self):
        """实测依据：单字口径在 64 卦中命中 60 卦（93.8%）→ 几乎恒真。

        本断言用真实判词库复算这个数字，把它钉死：若将来有人把口径改回单字，
        本断言仍绿（它测的是事实），但 ``test_word_group_hits_far_less_often``
        会显示差异。
        """
        data = g.load_guajie_data()
        hit = tot = 0
        for gd in data.values():
            cis = [y.ci for y in gd.yaos.values() if y.ci]
            if not cis:
                continue
            tot += 1
            if any(any(k in (c or "") for k in ("元", "吉", "亨", "利")) for c in cis):
                hit += 1
        self.assertEqual(tot, 64, "64 卦都应有爻辞")
        self.assertGreaterEqual(hit / float(tot), 0.9,
                                "单字口径实测应近乎恒中（若不再如此，说明判词库变了）")

    def test_word_group_hits_far_less_often(self):
        """词组口径实测命中 11/64（17.2%）—— 保留判据的区分度。"""
        data = g.load_guajie_data()
        single = group = tot = 0
        for gd in data.values():
            cis = [y.ci for y in gd.yaos.values() if y.ci]
            if not cis:
                continue
            tot += 1
            if any(any(k in (c or "") for k in ("元", "吉", "亨", "利")) for c in cis):
                single += 1
            if any(any(k in (c or "") for k in ("元吉", "亨利")) for c in cis):
                group += 1
        self.assertEqual(group, 11, "词组口径命中数（实测基准）")
        self.assertLess(group, single,
                        "词组口径应是单字口径的子集（更严），不产生反向差异")

    def test_gui_ming_hits_on_real_word_group(self):
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="泰", yuantang_yao="九二",
            yao_cis=["九二：亨利，小往大来"], yao_lines=[1, 1, 1, 0, 0, 0],
            birth_month_branch="寅", gua_qi_month=1,
            tian_shu=30, di_shu=20, year_gan="癸", year_zhi="亥",
        )
        self.assertIn("③辞吉", "；".join(out), "爻辞含「亨利」应判辞吉")


class TestItem4DeShiHasBothHalves(unittest.TestCase):
    """④ 得时：原文明文两类 —— 季正卦 ＋ 卦气月。"""

    def test_gua_qi_month_half_is_judged(self):
        """「正月得泰卦」那半：生月 == 本卦卦气月 → 得时。"""
        out = g.judge_gui_ming_shi_ti(
            prenatal_name="泰", yuantang_yao="九二",
            yao_cis=["九二：亨利"], yao_lines=[0, 1, 0, 1, 1, 1],
            birth_month_branch="寅", gua_qi_month=1,     # 寅=正月，卦气月=1
            tian_shu=30, di_shu=20, year_gan="癸", year_zhi="亥",
        )
        self.assertIn("④得时", "；".join(out),
                      "正月得泰卦（卦气月相合）应判得时")

    def test_jian_ming_takes_reverse_of_gua_qi_half(self):
        """贱命十体：卦气月不合 → 不得时。"""
        out = g.judge_jian_ming_shi_ti(
            prenatal_name="泰", yuantang_yao="初六",
            yao_cis=["初六：凶"], yao_lines=[0, 0, 0, 0, 0, 1],
            birth_month_branch="午", gua_qi_month=1,        # 午=五月，卦气月=1 → 不合
            tian_shu=20, di_shu=35, year_gan="庚", year_zhi="申",
        )
        self.assertIn("④不得时", "；".join(out))

    def test_gua_qi_month_lookup_is_per_hexagram(self):
        """取的是**本卦自己的**卦气月（卦头自述），不是月令卦。"""
        self.assertEqual(g._kz_gua_qi_month("乾"), 4)
        self.assertEqual(g._kz_gua_qi_month("讼"), 2)


class TestSeasonMonthMappingIsEngineConvention(unittest.TestCase):
    """④ 前半的「月份→季节」是**引擎口径**（原典只给四季代表卦）——如实留档。

    原典 L213「如春震木、夏离火、秋兑金、冬坎水之类」只给了四季代表卦，
    **没有**给月份到四季的划分规则；`guajie._SEASON_BY_BRANCH`
    （寅卯辰春/巳午未夏/申酉戌秋/亥子丑冬）是引擎自定的摊法。
    本类把这一点钉死，防止后人误以为它有原典明文依据。
    """

    def test_season_map_exists_and_is_documented_as_engine_convention(self):
        src = g._SEASON_BY_BRANCH
        self.assertEqual(len(src), 12)
        self.assertEqual(src["寅"], "春")
        self.assertEqual(src["午"], "夏")

    def test_season_map_is_not_in_original_text(self):
        """原典**没有**引擎所用的「月份→四季」逐月划分表。

        原典确实用「春月/夏月/秋月/冬月」（如「己午人夏生得离」「丁酉人秋生得兑」）
        也有「寅卯属木 / 巳午属火 / 申酉属金 / 辰戌丑未属土」的**纳音五行**分组
        —— 但那是纳音，不是「寅卯辰属春」这种月份四季表。
        故：判据的**方向**有原典依据，**具体的逐月划分**是引擎口径。
        """
        text = _text()
        for frag in ("寅卯辰春", "寅卯辰为春", "巳午未夏", "申酉戌秋", "亥子丑冬"):
            self.assertNotIn(frag, text,
                             f"若原典有此月份划分「{frag}」，本断言须重新评估")


if __name__ == "__main__":
    unittest.main()
