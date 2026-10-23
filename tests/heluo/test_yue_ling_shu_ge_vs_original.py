"""阴阳二数多寡随时吉凶论（起例卷之中 L31–L105）——与原典逐条对拍

**本文件所有期望值一律硬编码自原典原文，不调用被测函数求期望值。**

三条纪律：
1. 原文逐字断言先行——规则进代码之前先证明原典真这么写；
2. 每条数格都测**边界内**与**边界外**两侧，防止区间写开/写闭；
3. 原典自相矛盾处（L56 与 L83 重叠）断言「必须显式披露冲突」，
   而非断言某一边正确——本仓无权替原典裁。
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))

_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))
_TRANSCRIPT = _ROOT / "src" / "heluo_engine" / "orig" / "河洛真数_起例卷之中.txt"


def _orig() -> str:
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        return f.read()


def _transcript() -> str:
    if not _TRANSCRIPT.exists():
        raise unittest.SkipTest(f"转录不在预期路径：{_TRANSCRIPT}")
    with io.open(_TRANSCRIPT, encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════
# 一、原典原文必须在场（逐字）
# ═══════════════════════════════════════════════════════════════════

ORIGINAL_FRAGMENTS = (
    # L42 正数
    "天数二十五为正",
    "论九是阳之一策",
    # L50/L53
    "孤阳不偶　天数二十六以上，至四十以下，余偶数",
    "孤阳自偶　天数三十一至四十一、五十一，余奇数",
    # L56 / L58
    "阳数偏少　天数二十有五，只得四、五、六至二十四，地数三十是也",
    "以强伏弱　如天数三十、四十、五十之类，地数三十或至十二以下是也",
    # L65 / L70 / L71 / L72
    "地数至弱　地数三十，只得八、九、十、十一、十二数者，是谓至弱",
    "地数不足　地数三十，只得十八者，是谓之不足",
    "地数得中　地数三十，得三十二至四十五以下，皆谓得中",
    "地数太过　地数三十，如得五六十以上者，皆谓太过",
    # L74/L77/L80
    "孤阴背阳　地数三十至五十、六十，余偶数",
    "孤阴向阳　天数二十五，地数得四十至六十以下，余奇数",
    "阴数偏少　地数十八至二十八，天数二十五是也",
    # L83/L90/L93
    "以弱敌强　地数三十至四十、五十、六十以上，天数只得二十四以下是也",
    "天地俱羸　天数二十四以下，地数二十九以下",
    "阴阳相战　盖阳数多，阴数少，或阴阳二数俱多",
    # L100/L101
    "阳弱而余二四六八者，谓之援阴",
    "阳弱而余一三七九者，谓之援阳",
    "九者阳之亢也，其卦为离",
    # L34/L61/L95/L105
    "自十一月冬至后，至四月终，宜阳数，喜阳爻，利男子，不利女人也",
    "自五月一阴生，至十月阴胜极，利女人不利男子也",
    "但阳月令男命阳不足谓之无阳，阴月令女命阴不足谓之无阴",
    "凡数得三十六为老阳之禄数，二十八为少阳之禄数，利男不利女",
    "二十四为老阴之禄，三十二为少阴之禄，利女不利男",
)


class TestOriginalTextPresent(unittest.TestCase):
    def test_all_fragments_in_full_original(self):
        orig = _orig()
        missing = [f for f in ORIGINAL_FRAGMENTS if f not in orig]
        self.assertEqual(missing, [], f"全库原著缺失片段：{missing}")

    def test_all_fragments_in_transcript(self):
        """转录件也须逐字命中——防止只对着一个来源写实现。"""
        t = _transcript()
        missing = [f for f in ORIGINAL_FRAGMENTS if f not in t]
        self.assertEqual(missing, [], f"转录缺失片段：{missing}")


# ═══════════════════════════════════════════════════════════════════
# 二、每条数格的区间（边界内 + 边界外）
# ═══════════════════════════════════════════════════════════════════

class TestShuGeTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import SHU_GE_TABLE, classify_shu_ge
        cls.TABLE = SHU_GE_TABLE
        # 用 staticmethod 包一层：直接挂到类上的函数会变成绑定方法，
        # self 会被当成第一个实参传进去。
        cls._classify = staticmethod(classify_shu_ge)

    def names(self, t: int, d: int) -> set[str]:
        return {r.name for r in self._classify(t, d)}

    def test_table_covers_every_named_pattern_in_original(self):
        names = {r.name for r in self.TABLE}
        for must in ("孤阳不偶", "孤阳自偶", "阳数偏少", "以强伏弱", "地数至弱",
                     "地数得中", "地数太过", "孤阴背阳", "孤阴向阳", "阴数偏少",
                     "以弱敌强", "安和自宁", "天地俱羸", "阴阳相战"):
            self.assertIn(must, names, f"数格表缺「{must}」")

    # ── 余数奇偶 ──
    def test_gu_yang_bu_ou_even_yu(self):
        """L50：天数 26–40 余偶 且 地数 30。"""
        for t in range(26, 41):
            if (t - 25) % 2 == 0:
                self.assertIn("孤阳不偶", self.names(t, 30), f"天数{t}")

    def test_gu_yang_zi_ou_odd_yu(self):
        """L53：同区间而余奇 → 孤阳自偶，与上条互斥。"""
        for t in range(26, 41):
            if (t - 25) % 2 == 1:
                self.assertIn("孤阳自偶", self.names(t, 30), f"天数{t}")
                self.assertNotIn("孤阳不偶", self.names(t, 30), f"天数{t}")

    def test_no_yu_excludes_zero(self):
        """余 0 是「无余」不是「余偶」：(25,30) 只能命中安和自宁。"""
        self.assertEqual(self.names(25, 30), {"安和自宁"})

    def test_gu_yin_bei_yang_even_yu(self):
        """L74：天数 25、地数 30–60 余偶 → 孤阴背阳。"""
        hits = [d for d in range(32, 61) if (d - 30) % 2 == 0
                and "孤阴背阳" in self.names(25, d)]
        self.assertTrue(hits, "无余偶用例，测试数据有问题")
        for d in hits:
            self.assertNotIn("孤阴向阳", self.names(25, d), f"地数{d} 两命名互撞")

    def test_gu_yin_xiang_yang_odd_yu(self):
        """L77：天数 25、地数 40–60 余奇 → 孤阴向阳。"""
        hits = [d for d in range(40, 61) if (d - 30) % 2 == 1
                and "孤阴向阳" in self.names(25, d)]
        self.assertTrue(hits, "无余奇用例，测试数据有问题")

    # ── 纯数值档 ──
    def test_yang_shu_pian_shao_band(self):
        """L56：天数 4–24 且地数 30。"""
        for t in (4, 12, 24):
            self.assertIn("阳数偏少", self.names(t, 30), f"天数{t}")
        for t in (3, 25, 26):
            self.assertNotIn("阳数偏少", self.names(t, 30), f"天数{t} 越界")

    def test_yi_qiang_fu_ruo_band(self):
        """L58：天数 ≥30（原典举 30/40/50「之类」），地数 30 或 ≤12。"""
        for t in (30, 40, 50, 60):
            for d in (30, 12, 5):
                self.assertIn("以强伏弱", self.names(t, d), f"({t},{d})")
        # 地数 13–29 原典未言 → 不得命中
        for d in (13, 20, 29):
            self.assertNotIn("以强伏弱", self.names(30, d), f"地数{d} 原典未言却命中")
        # 天数 <30 不属本条
        self.assertNotIn("以强伏弱", self.names(29, 30), "天数29 不属以强伏弱")

    def test_di_shu_zhi_ruo_band(self):
        """L65：地数 8–12。"""
        for d in range(8, 13):
            self.assertIn("地数至弱", self.names(25, d), f"地数{d}")
        for d in (7, 13):
            self.assertNotIn("地数至弱", self.names(25, d), f"地数{d} 越界")

    def test_di_shu_de_zhong_band(self):
        """L71：地数 32–45。"""
        for d in (32, 38, 45):
            self.assertIn("地数得中", self.names(25, d), f"地数{d}")
        for d in (31, 46):
            self.assertNotIn("地数得中", self.names(25, d), f"地数{d} 越界")

    def test_di_shu_tai_guo_band(self):
        """L72：地数 ≥50。"""
        for d in (50, 60, 90):
            self.assertIn("地数太过", self.names(25, d), f"地数{d}")
        for d in (46, 49):
            self.assertNotIn("地数太过", self.names(25, d), f"地数{d} 越界")

    def test_yin_shu_pian_shao_band(self):
        """L80：天数 25、地数 18–28。"""
        for d in (18, 22, 28):
            self.assertIn("阴数偏少", self.names(25, d), f"地数{d}")
        for d in (17, 29):
            self.assertNotIn("阴数偏少", self.names(25, d), f"地数{d} 越界")

    def test_yin_shu_pian_shao_requires_tian_25(self):
        """**天数=25 是本条不可去的前提**，丢了就会把地数 18–28 一网打尽。"""
        for t in (20, 26, 30, 40):
            self.assertNotIn("阴数偏少", self.names(t, 22), f"天数{t} 不该命中")

    def test_tian_di_ju_lei_band(self):
        """L90：天数 ≤24 且地数 ≤29。"""
        for t, d in ((24, 29), (10, 12), (1, 1)):
            self.assertIn("天地俱羸", self.names(t, d), f"({t},{d})")
        for t, d in ((25, 29), (24, 30)):
            self.assertNotIn("天地俱羸", self.names(t, d), f"({t},{d}) 越界")

    def test_yin_yang_xiang_zhan(self):
        """L93：阳数多（>25）且地数 ≠30（少或俱多）。"""
        self.assertIn("阴阳相战", self.names(30, 25), "阳多阴少")
        self.assertIn("阴阳相战", self.names(40, 60), "阴阳俱多")
        self.assertNotIn("阴阳相战", self.names(25, 25), "天数不足不属阳数多")
        self.assertNotIn("阴阳相战", self.names(40, 30), "地数无余不属于少/俱多")

    def test_an_he_zi_ning(self):
        """L87：天数 25、地数 30。"""
        self.assertEqual(self.names(25, 30), {"安和自宁"})


# ═══════════════════════════════════════════════════════════════════
# 三、原典自相矛盾处：必须披露，不得静默择一
# ═══════════════════════════════════════════════════════════════════

class TestOriginalConflictMustBeDisclosed(unittest.TestCase):
    """L56 阳数偏少 vs L83 以弱敌强：在 (天数≤24, 地数=30) 处重叠且判语相反。

    本仓**无权**替原典裁先后，但**必须**把冲突摊开。
    """

    def setUp(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import shu_ge_conflicts
        self._c = shu_ge_conflicts

    def test_conflict_is_reported(self):
        """须报出重叠，且措辞必须是**更正后**的「同向不同severity」。

        2026-10-07 此前写作「判语相反」——经全库取证证伪：
        L995「阴令得之犹可喜，若生阳月必孤睽」
        L1076「阴令忧危浅，阳月有大殃」
        两条诗断同向（阴月令较轻、阳月令较重），仅以弱敌强判词更重。
        此断言锁死更正后的措辞，防止旧错误复发。
        """
        c = self._c(24, 30)
        self.assertTrue(c, "(24,30) 须报出原典重叠")
        joined = " ".join(c)
        self.assertIn("阳数偏少", joined)
        self.assertIn("以弱敌强", joined)
        self.assertIn("同向", joined, "重叠关系必须表述为「同向」，不得回退为「相反」")
        self.assertIn("更重", joined)
        self.assertIn("阴令得之犹可喜", joined, "须直引 L995 诗断原文")
        self.assertIn("阴令忧危浅", joined, "须直引 L1076 诗断原文")
        self.assertNotIn("判语相反", joined, "「判语相反」已被证伪，不得复现")

    def test_both_rules_actually_match(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import classify_shu_ge
        names = {r.name for r in classify_shu_ge(24, 30)}
        self.assertIn("阳数偏少", names)
        self.assertIn("以弱敌强", names)

    def test_no_conflict_outside_overlap(self):
        """(天数20, 地数40) 不重叠，不该报冲突。"""
        self.assertEqual(self._c(20, 40), ())


# ═══════════════════════════════════════════════════════════════════
# 四、禄数（L105）
# ═══════════════════════════════════════════════════════════════════

class TestLuShu(unittest.TestCase):
    def test_four_values(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import judge_lu_shu
        self.assertEqual(
            [(h.value, h.name) for h in judge_lu_shu(36, 30)],
            [(36, "老阳之禄")])
        self.assertEqual(
            [(h.value, h.name) for h in judge_lu_shu(28, 30)],
            [(28, "少阳之禄")])
        self.assertEqual(
            [(h.value, h.name) for h in judge_lu_shu(25, 24)],
            [(24, "老阴之禄")])
        self.assertEqual(
            [(h.value, h.name) for h in judge_lu_shu(25, 32)],
            [(32, "少阴之禄")])

    def test_gender_direction(self):
        """L105：36/28 利男不利女；24/32 利女不利男。"""
        from heluo_engine.engines.heluo.yue_ling_shu_ge import judge_lu_shu
        self.assertEqual(judge_lu_shu(36, 30, "male")[0].xing_bie, "利男不利女")
        self.assertTrue(judge_lu_shu(36, 30, "male")[0].gender_fit)
        self.assertFalse(judge_lu_shu(36, 30, "female")[0].gender_fit)
        self.assertEqual(judge_lu_shu(25, 24, "female")[0].xing_bie, "利女不利男")
        self.assertTrue(judge_lu_shu(25, 24, "female")[0].gender_fit)
        self.assertFalse(judge_lu_shu(25, 24, "male")[0].gender_fit)

    def test_no_gender_means_no_verdict(self):
        """性别未给时必须 gender_fit=None，不得按默认性别强判。"""
        from heluo_engine.engines.heluo.yue_ling_shu_ge import judge_lu_shu
        for h in judge_lu_shu(36, 30):
            self.assertIsNone(h.gender_fit)

    def test_both_sides_reported_without_picking(self):
        """原典未指明天数还是地数 → 两数各自比对，归属如实标记。"""
        from heluo_engine.engines.heluo.yue_ling_shu_ge import judge_lu_shu
        hits = judge_lu_shu(36, 36)
        self.assertEqual(len(hits), 2)
        self.assertEqual({h.which for h in hits}, {"天", "地"})


# ═══════════════════════════════════════════════════════════════════
# 五、援阴／援阳（L100–L101）
# ═══════════════════════════════════════════════════════════════════

class TestYouYinYang(unittest.TestCase):
    def setUp(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import judge_you_yin_yang
        self.j = judge_you_yin_yang

    def test_jue_yang_when_tian_is_nine(self):
        """L101「九者阳之亢也，其卦为离」——天数 9 → 援阳/离。"""
        r = self.j(9, 30)
        self.assertEqual(r["name"], "援阳")
        self.assertEqual(r["gua"], "离")

    def test_jue_yin_numbers(self):
        for t, gua in ((2, "坤"), (4, "巽"), (6, "乾"), (8, "艮")):
            r = self.j(t, 30)
            self.assertEqual(r["name"], "援阴", f"天数{t}")
            self.assertEqual(r["gua"], gua, f"天数{t}")

    def test_others_have_no_name(self):
        """不在 2/4/6/8 与 1/3/7/9 内者，原典未言 → 不得硬套。

        注意 5 属 1/3/5/7/9 之列（L101「五为艮」），7 亦然，故不能拿它们当反例。
        """
        for t in (10, 11, 16, 20, 24):
            self.assertEqual(self.j(t, 30)["name"], "", f"天数{t} 不该有援名")

    def test_not_weak_gives_no_name(self):
        """天数不弱时原典未立此名。"""
        self.assertEqual(self.j(30, 30)["name"], "")
        self.assertFalse(self.j(30, 30)["tian_weak"])

    def test_di_weak_symmetric(self):
        """L101：阴弱援二四六八 → 先贱后贵；援一三七九 → 弱而又弱。"""
        self.assertEqual(self.j(25, 4)["di_jie"], "先贱后贵")
        self.assertEqual(self.j(25, 3)["di_jie"], "弱而又弱")
        self.assertEqual(self.j(25, 20)["di_jie"], "")


# ═══════════════════════════════════════════════════════════════════
# 六、性别向背与命无阴阳
# ═══════════════════════════════════════════════════════════════════

class TestXingBeiAndMingWuYinYang(unittest.TestCase):
    def setUp(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import (
            judge_ming_wu_yin_yang, xingbie_xiang_bei)
        self.xb = xingbie_xiang_bei
        self.mwy = judge_ming_wu_yin_yang

    def test_yang_yue_ling_favors_male(self):
        """L34：阳月令（11,12,1~4）利男子。"""
        for m in (1, 2, 3, 4, 11, 12):
            r = [x for x in self.xb(30, 30, m, "male") if x.rule == "L34"]
            self.assertTrue(r and r[0].applies, f"{m}月 阳月令 L34 应适用")

    def test_yin_yue_ling_favors_female(self):
        """L61：阴月令（5~10）利女人。"""
        for m in range(5, 11):
            r = [x for x in self.xb(25, 40, m, "female") if x.rule == "L61"]
            self.assertTrue(r and r[0].applies, f"{m}月 阴月令 L61 应适用")

    def test_no_gender_means_nothing_applies(self):
        for x in self.xb(30, 30, 11, ""):
            self.assertFalse(x.applies, f"{x.rule} 未给性别却判了")

    def test_ming_wu_yin_yang_male_in_yang_month(self):
        """L95：阳月令男命阳不足 → 无阳 → 凶。"""
        _, xiong = self.mwy(20, 30, 11, "male")
        self.assertTrue(xiong)
        _, xiong2 = self.mwy(30, 30, 11, "male")
        self.assertIsNone(xiong2, "阳未不足则本条不成立")

    def test_ming_wu_yin_yang_female_in_yin_month(self):
        """L95：阴月令女命阴不足 → 无阴 → 凶。"""
        _, xiong = self.mwy(30, 20, 6, "female")
        self.assertTrue(xiong)

    def test_ming_wu_yin_yang_cross_pair_is_none(self):
        """阴月令男命阳不足不在 L95 的组合内 → 不判。"""
        _, xiong = self.mwy(20, 30, 6, "male")
        self.assertIsNone(xiong)

    def test_ming_wu_yin_yang_no_gender(self):
        _, xiong = self.mwy(20, 30, 11, "")
        self.assertIsNone(xiong)


# ═══════════════════════════════════════════════════════════════════
# 七、与生产链路 judge_shu_xiong 的集成
# ═══════════════════════════════════════════════════════════════════

class TestJudgeShuXiongIntegration(unittest.TestCase):
    def setUp(self):
        from heluo_engine.engines.heluo.guajie import judge_shu_xiong
        self.j = judge_shu_xiong

    def test_gender_is_optional_backward_compatible(self):
        """三参调用必须仍然可用（既有消费方不许被打破）。"""
        r = self.j(27, 30, 11)
        self.assertEqual(r.pattern, "孤阳不偶")

    def test_yi_qiang_fu_ruo_direction_is_reversed(self):
        """L58 与 L1073 方向相反：阳月令「不妨」，阴月令「恃势致凶」。

        取天数 45 避开与 L53 孤阳自偶（天数 26–40 且地数 30）的重叠。
        """
        self.assertFalse(self.j(45, 30, 1).shu_xiong, "阳月令应不妨")
        self.assertTrue(self.j(45, 30, 6).shu_xiong, "阴月令应致凶")
        self.assertEqual(self.j(45, 30, 6).pattern, "以强伏弱")

    def test_weak_strong_keeps_l1073_direction(self):
        """L1073：阴月令尚庶几，阳月令灭顶之凶。"""
        self.assertTrue(self.j(20, 40, 1).shu_xiong, "阳月令应凶")
        self.assertFalse(self.j(20, 40, 6).shu_xiong, "阴月令尚庶几")

    def test_matched_lists_all_hits(self):
        r = self.j(24, 30, 11)
        self.assertIn("阳数偏少", r.matched)
        self.assertIn("以弱敌强", r.matched)

    def test_conflicts_are_carried_on_result(self):
        r = self.j(24, 30, 11)
        self.assertTrue(r.conflicts, "冲突须随结果外传")

    def test_gender_flows_into_evidence(self):
        r = self.j(20, 30, 11, "male")
        joined = " ".join(r.evidence)
        self.assertIn("male命", joined)

    def test_lu_shu_carried_on_result(self):
        r = self.j(36, 30, 11, "male")
        self.assertEqual([h.value for h in r.lu_shu], [36])

    def test_ming_wu_yin_yang_carried_on_result(self):
        r = self.j(20, 30, 11, "male")
        self.assertTrue(r.ming_wu_yin_yang[1])

    def test_no_gender_still_produces_result(self):
        """性别未给时三性判一律不判，但不得崩。"""
        r = self.j(36, 30, 11)
        self.assertEqual(r.pattern, "孤阳自偶")   # 余 11 奇
        self.assertTrue(all(h.gender_fit is None for h in r.lu_shu))
        self.assertIsNone(r.ming_wu_yin_yang[1])


# ═══════════════════════════════════════════════════════════════════
# 八、拒算登记必须诚实
# ═══════════════════════════════════════════════════════════════════

class TestRefusalRegistry(unittest.TestCase):
    def setUp(self):
        from heluo_engine.engines.heluo.yue_ling_shu_ge import REFUSED
        self.R = REFUSED

    def test_registry_non_empty_and_well_formed(self):
        self.assertTrue(self.R)
        for clause, why, need in self.R:
            self.assertTrue(clause.strip(), "拒算条目缺原典条款")
            self.assertTrue(why.strip(), f"{clause[:20]}… 缺拒算理由")
            self.assertTrue(need.strip(), f"{clause[:20]}… 缺解封条件")

    def test_registry_covers_known_gaps(self):
        """拒算登记不是装饰：清空或大幅缩水必须让测试变红。"""
        self.assertGreaterEqual(
            len(self.R), 10,
            f"拒算登记只剩 {len(self.R)} 条，多半是被清空了；"
            f"已知缺口至少十余条（见 yue_ling_shu_ge.REFUSED 的 docstring）")
        clauses = " ".join(c for c, _, _ in self.R)
        for must in ("L36", "L38", "L45", "L47", "L49", "L99", "L100", "L105",
                     "L110", "L114"):
            self.assertIn(must, clauses, f"拒算登记缺 {must}")

    def test_tian_shu_zhi_ruo_contradiction_is_registered(self):
        """L38「天数一十有五」与 L42「天数二十五为正」矛盾，必须登记。"""
        joined = " ".join(c + w for c, w, _ in self.R)
        self.assertIn("一十有五", joined)
        self.assertIn("天数二十五为正", joined)

    def test_lu_shu_ownership_uncertainty_registered(self):
        """L105 未指明天数还是地数——须登记，不得替原典指定。"""
        joined = " ".join(c for c, _, _ in self.R)
        self.assertIn("三十六", joined)

    def test_hexagram_dependent_rules_registered(self):
        """需卦爻入参的规则须登记，而不是静默漏掉。"""
        joined = " ".join(c + w for c, w, _ in self.R)
        self.assertIn("L49", joined)
        self.assertIn("L110", joined)


# ═══════════════════════════════════════════════════════════════════
# 九、性别贯通端到端（compose_guajie / build_guajie_from_result）
#
# 2026-10-07 变异验证实测：只测 judge_shu_xiong 模块函数**抓不到**
# 「compose_guajie 不传 gender」「build_guajie_from_result 漏传 gender」
# 这两类断链——两者都仍全绿。故必须补真实调用链的断言。
# ═══════════════════════════════════════════════════════════════════

class TestGenderPlumbingEndToEnd(unittest.TestCase):
    def _compose(self, gender: str):
        from heluo_engine.engines.heluo.guajie import compose_guajie
        return compose_guajie(
            prenatal_name="乾", postnatal_name="坤", yuantang_yao="九三",
            birth_month=11, tian_shu=20, di_shu=30, gender=gender,
        )

    def test_compose_guajie_forwards_gender(self):
        r = self._compose("male")
        self.assertIn("male命", " ".join(r.evidence))

    def test_compose_guajie_without_gender_is_silent(self):
        """未给性别时不得出现任何性别向背断言。"""
        r = self._compose("")
        joined = " ".join(r.evidence)
        self.assertNotIn("male命", joined)
        self.assertNotIn("female命", joined)

    def test_compose_guajie_default_arg_exists(self):
        """gender 必须有默认值，旧的三参调用不许被打断。"""
        import inspect
        from heluo_engine.engines.heluo.guajie import compose_guajie
        sig = inspect.signature(compose_guajie)
        self.assertIn("gender", sig.parameters)
        self.assertEqual(sig.parameters["gender"].default, "")

    def test_build_guajie_from_result_reads_input_gender(self):
        """端到端：result.input.gender → judge_shu_xiong 的证据。"""
        from types import SimpleNamespace
        from heluo_engine.engines.heluo.guajie import build_guajie_from_result
        res = SimpleNamespace(
            input=SimpleNamespace(gender="male"),
            prenatal=SimpleNamespace(hexagram_name="乾"),
            postnatal=SimpleNamespace(hexagram_name="坤"),
            yuantang=SimpleNamespace(yuantang="九三"),
            numbers=SimpleNamespace(tian_shu=20, di_shu=30),
            timeline=None,
        )
        out = build_guajie_from_result(res)
        self.assertNotIn("error", out, f"build_guajie_from_result 报错：{out.get('error')}")
        joined = " ".join(out.get("evidence", []))
        self.assertIn("male命", joined, "性别未从 result.input 贯通到数凶判定")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
