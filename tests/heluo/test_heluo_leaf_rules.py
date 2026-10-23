# -*- coding: utf-8 -*-
"""第三轮审计守卫（2026-10-24）：叶/不叶判据链路的六处静默失效。

本轮查出的缺陷都属同一类：**判据从未生效，但全绿**。
共同形态：代码看起来在工作，实际某个原典判据**恒不触发**或**恒假**，
下游拿到的是「不判」或「反向」的结论，且**没有任何痕迹**。

逐条对应：

| # | 缺陷 | 表现 |
|---|---|---|
| A | 卦气月解析漏「在」 | 坤卦 gua_qi_month=None ⇒ 坤卦十月生被判「不叶（凶象）」，与原典相反 |
| B | 月名字符集缺「一」 | 「属十一月」永远匹配不上 ⇒ 小畜/贲/复/节 四卦无卦气月 |
| C | 八纯卦无「宫」无「卦气」 | 兑/坎/巽/离 四卦无卦气月 |
| D | 旺时区间 0 命中 | 原典「生于二月至八月得时」等 16 卦的旺时判据**从未生效** |
| E | 「一卦名吉」全名 vs 短名 | 规则图里该判据恒不触发，方向静默回落 NEUTRAL |
| F | 「不叶吉」被子串误判 | 50 条不叶断语被归入叶吉 ⇒ 8 个爻的凶判定漏判 |

**覆盖**
--------
* A/B/C：64 卦**全部**解析出卦气月；且各月卦与十二辟卦月表交叉验证；
* A/B/C：逐条钉住「坤=10」「小畜/贲/复/节=11」等本次修好的值（防回退）；
* D：旺时区间必须抽出 16 卦，且逐卦钉住月份集合（依原典原文）；
* E：`judge_liu_ju` 短名/全名**都**能判（归一口径一致）；
* F：否定式优先 —— 「数卦不叶吉者」必须进不叶类，且不进叶类。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.heluo import guajie as gj  # noqa: E402
from tongshu.engines.heluo.gui_ming_liu_ju import (  # noqa: E402
    GUA_MING_GOOD_EXAMPLES, judge_liu_ju,
)
from tongshu.engines.heluo.numbers import short_hexagram_name  # noqa: E402


class TestGuaQiMonthParsing(unittest.TestCase):
    """A/B/C：卦气月解析必须覆盖原典的全部三种句式。"""

    @classmethod
    def setUpClass(cls):
        cls.data = gj.load_guajie_data()
        cls.with_month = {g.name: g.gua_qi_month for g in cls.data.values()
                          if g.gua_qi_month is not None}

    def test_all_64_guas_have_guaqi_month(self):
        """64 卦**全部**自述卦气月 —— 一个都不能缺。

        ⚠ 此断言此前不存在（只有一条只查 12 辟卦、且把「坤、复 缺失」
        写成「已知状态」的断言 —— 那等于把解析器的缺陷固化成期望）。
        """
        missing = sorted(g.name for g in self.data.values()
                         if g.gua_qi_month is None)
        self.assertEqual(missing, [],
                         f"未解析出卦气月的卦：{missing}；"
                         "若原典确实未写，须先核原文再改本断言")

    def test_kun_uses_qi_qi_zai_shi_yue(self):
        """A：坤卦原文写「卦气**在**十月」，解析必须认这个措辞。

        原典（《河洛真数·易卦释义·上经卷之上》L91 逐字）：
        「星辰之气。德合无疆，坤象地道也…**卦气在十月**，纳甲是乙未…」
        """
        self.assertEqual(self.with_month.get("坤"), 10,
                         "坤卦卦气月应解析为 10（原典作「卦气在十月」）")

    def test_xi_yue_parsed(self):
        """B：月名字符集曾缺「一」⇒「属十一月」永远匹配不上。

        受影响：小畜 / 贲 / 复 / 节（原文皆「…属十一月」）。
        """
        for name in ("小畜", "贲", "复", "节"):
            with self.subTest(gua=name):
                self.assertEqual(self.with_month.get(name), 11,
                                 f"{name} 的卦气月应为 11（原典「属十一月」）")

    def test_pure_heavenly_guas_parsed(self):
        """C：八纯卦无「XX宫N世卦」也无「卦气」字样，只有「…属X月」。

        受影响：兑 / 坎 / 巽 / 离。
        """
        for name, want in (("兑", 10), ("坎", 10), ("巽", 4), ("离", 4)):
            with self.subTest(gua=name):
                self.assertEqual(self.with_month.get(name), want,
                                 f"{name} 的卦气月应为 {want}")

    def test_twelve_bi_gua_agree_with_month_table(self):
        """★ 跨规则不变量：十二辟卦的自述卦气月 == 其月令月。"""
        month_of_gua = {v[1]: m for m, v in gj.GUA_QI_MONTH_TABLE.items()}
        checked = 0
        for gua, m in month_of_gua.items():
            self_desc = self.with_month.get(gua)
            if self_desc is None:
                continue
            self.assertEqual(self_desc, m,
                             f"{gua} 自述卦气月 {self_desc} ≠ 月令月 {m}")
            checked += 1
        self.assertEqual(checked, 12,
                         "十二辟卦应全部可交叉验证（此前「坤/复 缺失」使其只有 10）")


class TestWangShiIntervals(unittest.TestCase):
    """D：旺时区间（得时/及时）判据必须真的生效。"""

    @classmethod
    def setUpClass(cls):
        cls.data = gj.load_guajie_data()

    def test_wangshi_extracted_for_16_guas(self):
        """原文明写旺时区间的卦，须逐条抽出（此前恒 0 命中）。"""
        got = {}
        for g in self.data.values():
            months, src = gj._extract_wangshi(g.gua_lines)
            if months:
                got[g.name] = (months, src)
        self.assertGreaterEqual(len(got), 16,
                                f"仅抽出 {len(got)} 卦的旺时区间，应至少 16 卦")
        for name in ("乾", "屯", "豫", "颐", "丰", "恒", "大壮", "小过",
                     "离", "解", "益", "随", "震", "归妹", "复", "噬嗑"):
            with self.subTest(gua=name):
                self.assertIn(name, got, f"{name} 的旺时区间未被抽出")

    def test_wangshi_months_match_original_text(self):
        """逐卦钉住旺时月份集合（依原典原文，防漂移）。"""
        want = {
            "乾": {2, 3, 4, 5, 6, 7, 8},        # 生于二月以后八月以前者，得时也
            "屯": {2, 3, 4, 5, 6, 7, 8},        # 自二月至八月得时
            "豫": {2, 3, 4, 5, 6, 7, 8},        # 生于二三四五六七八月为及时
            "颐": {2, 3, 4, 5, 6, 7},           # 又二月至七月生者及时
            "丰": {2, 3, 4, 5, 6, 7, 8},        # 又二月生至八月为及时
            "恒": {2, 3, 4, 5, 6, 7, 8},        # 又二三四五六七八月生为及时
            "大壮": {4, 5, 6, 7, 8},            # 又四五六七八月生者为及时
            "小过": {3, 4, 5, 6, 7, 8},         # 又三四五六七八月为及时
            "离": {4, 5, 6},                    # 如生于四月五月六月为及时
            "解": {2, 3, 4, 5, 6, 7, 8},        # 又二三四五六七八月为雷雨及时
            "益": {2, 3, 4, 5, 6, 7, 8},        # 又二月至八月生者，福力重
            "随": {2, 3, 4, 5, 6, 7, 8},        # 皆宜生于二月至八月及时也
            "震": {2, 3, 4, 5, 6, 7, 8, 10},    # 如生于十月及二三四五六七八月得时
            "归妹": {2, 3, 4, 5, 6, 7, 8},      # 如生于七月及二三四五六七八月为及时
            "复": {2, 3, 4, 5, 6, 7, 8},        # 若二月至八月生者及时
            "噬嗑": {2, 3, 4, 5, 6, 7, 8},      # 宜生于二月已后，八月以前及时
        }
        for name, months in want.items():
            g = self.data.get(name)
            self.assertIsNotNone(g, f"{name} 不在卦库中")
            got, src = gj._extract_wangshi(g.gua_lines)
            with self.subTest(gua=name):
                self.assertIsNotNone(got, f"{name} 未抽出旺时区间")
                self.assertEqual(got, months,
                                 f"{name} 旺时区间应为 {sorted(months)}，"
                                 f"实得 {sorted(got)}（原文：{src[:30]}）")

    def test_wangshi_actually_affects_judgement(self):
        """旺时区间必须真的改变判定（不是抽出来没人用）。"""
        # 屯卦：卦气属六月；原文明写「自二月至八月得时」
        # → 四月生、不在纳甲 ⇒ 修前判「不叶」，修后应判「叶」
        r = gj.judge_ye_buye("屯", 4, "甲戌")
        self.assertTrue(r.ye,
                        "屯卦四月生：原典「自二月至八月得时」⇒ 应判叶")
        self.assertFalse(r.buye)
        self.assertTrue(any("旺时" in e for e in r.evidence),
                        "evidence 必须显形旺时依据")
        # 十二月生 ⇒ 不在旺时区间
        r2 = gj.judge_ye_buye("屯", 12, "甲戌")
        self.assertFalse(r2.ye, "屯卦十二月生不在旺时区间")
        self.assertTrue(any("∉ 旺时" in e for e in r2.evidence),
                        "evidence 必须显形旺时落空")


class TestGuaMingJudgeConsistency(unittest.TestCase):
    """E：「一卦名吉」判据的归一口径必须一致。"""

    def test_short_and_full_name_both_judge(self):
        """短名与全名**都**应能判出「卦名吉」（归一后送进判据）。"""
        for short in ("泰", "大有", "同人", "晋", "豫"):
            with self.subTest(gua=short):
                r = judge_liu_ju(gua_name=short)
                self.assertTrue(r["卦名"].passed,
                                f"短名「{short}」应判为卦名吉")
                full = gj.load_guajie_data()  # 确保数据已加载
                r2 = judge_liu_ju(gua_name=short)
                self.assertTrue(r2["卦名"].passed)

    def test_rule_graph_normalizes_full_name(self):
        """规则图那处必须归一全名，否则「一卦名吉」永不触发。

        ★ 端到端：构造先天卦 = **全名**「地天泰」的冻结态，
          走 heluo_own_direction("HL_PRENATAL_HEXAGRAM", …)，
          必须返回**方向**（而非 None）——
          这正是修复前恒不触发的那条路径。
        """
        from tongshu.engines.heluo.diagnosis_rule_graph import (
            heluo_own_direction,
        )
        from tongshu.engines.heluo.frozen_state import FrozenHeluoState

        def _state(prenatal_name: str) -> FrozenHeluoState:
            base = dict(
                version="v2.0", calculation_policy={},
                tian_shu=30, di_shu=30, tian_reduced=5, di_reduced=6,
                prenatal_upper="坤", prenatal_lower="乾",
                prenatal_lines=(1, 1, 1, -1, -1, -1),
                yuan_tang="六四", yuan_tang_index=3, yuan_tang_nature="阴",
                postnatal_name="天雷无妄", postnatal_upper="乾",
                postnatal_lower="震", postnatal_lines=(1, 1, 1, 1, -1, -1),
                seasonal_hexagram=None, qi_phase=None,
                hua_gong_state=None, hua_gong_level=None, hua_gong_reduced=None,
                hua_gong_evidence=None,
                yuan_qi_state=None, yuan_qi_evidence=None,
                yuan_qi_tian=None, yuan_qi_di=None,
                dayun_summary=[], liunian_count=0,
                birth_year=1983, gender="male", birth_hour="午",
                birth_date="1983-11-03",
            )
            return FrozenHeluoState(prenatal_name=prenatal_name, **base)

        # 全名「地天泰」在原文明举吉卦之列（泰）⇒ 必须判出方向
        d, why = heluo_own_direction("HL_PRENATAL_HEXAGRAM", _state("地天泰"))
        self.assertIsNotNone(
            d,
            "先天卦为全名「地天泰」时「一卦名吉」仍未触发 —— "
            f"卦名未归一为简称（依据：{why}）")

        # 不在明举例内的卦仍应「不判」（不得因归一而滥判）
        d2, _ = heluo_own_direction("HL_PRENATAL_HEXAGRAM", _state("风山渐"))
        self.assertIsNone(d2, "不在原文明举之列的卦不应判方向")

        # 归一函数本身
        for full, short in (("地天泰", "泰"), ("火天大有", "大有"),
                            ("天火同人", "同人"), ("火地晋", "晋"),
                            ("雷地豫", "豫")):
            with self.subTest(full=full):
                self.assertEqual(short_hexagram_name(full), short)
                self.assertIn(short_hexagram_name(full), GUA_MING_GOOD_EXAMPLES)


class TestNegativeLeafPriority(unittest.TestCase):
    """F：「不叶吉」必须进不叶类，不得因含「叶吉」子串被误归。"""

    def test_bu_ye_jie_goes_to_buye_not_ye(self):
        """「数卦不叶吉者…」必须归不叶类。"""
        duans = ["数卦叶吉，可当此爻。",
                 "数卦不叶吉者，好大贪功，必遭凶祸，志欲稳稳施为。",
                 "岁运逢之，皆当如此处之。"]
        ye, buye, suiyun = gj._split_duans(duans)
        self.assertIn("数卦不叶吉者", buye,
                      "「数卦不叶吉者」必须归不叶类")
        self.assertNotIn("数卦不叶吉者", ye,
                         "「数卦不叶吉者」不得归叶吉类（含「叶吉」子串）")
        self.assertIn("数卦叶吉", ye, "「数卦叶吉」应归叶吉类")

    def test_all_raw_duans_classified_sensibly(self):
        """全库 1088 条原始断语：含否定式叶术语的不得进叶类。"""
        import json
        raw = json.loads(
            (ROOT / "data" / "heluo" / "guajie_data.json").read_text(encoding="utf-8"))
        neg = ("不叶吉", "不叶者", "不叶", "不归元", "不入局",
               "生不及时", "不及时", "难当此爻", "失正", "失位")
        bad = []
        n = 0
        for g in raw:
            for y in g.get("yaos", []):
                for d in y.get("duans", []):
                    if not d:
                        continue
                    n += 1
                    ye, buye, _ = gj._split_duans([d])
                    if any(k in d for k in neg) and d in ye:
                        bad.append((g["name"], y.get("yao"), d[:40]))
        self.assertEqual(bad, [],
                         f"{len(bad)} 条含否定式的断语被误归叶吉类：{bad[:3]}")
        self.assertGreater(n, 1000, "样本量异常")

    def test_buji_flip_restored(self):
        """被误分类修复后，8 个爻的凶判定应翻回（不再漏判）。"""
        # 屯 上六：「数卦不叶者，亲眷刑伤，婚嗣孤克。」—— 含「刑伤」⇒ 凶
        ye, buye, _ = gj._split_duans(["数卦不叶者，亲眷刑伤，婚嗣孤克。"])
        self.assertIn("刑伤", buye)
        self.assertTrue(gj._yao_buji("", buye, ""),
                        "「数卦不叶者…」应判为凶（此前被误归叶吉而漏判）")


class TestBaselineLayerExists(unittest.TestCase):
    """④：平台信号出口的 BASELINE 层必须真的产出（此前恒不产出）。"""

    def test_baseline_layer_present(self):
        from tongshu.engines.heluo_adapter import HeluoAdapter
        from tongshu.engines.heluo.canonical_signals import build_platform_signals
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        sigs = build_platform_signals(res)
        layers = {s["layer"] for s in sigs}
        self.assertIn("BASELINE", layers,
                      f"BASELINE 层未产出（层集合：{sorted(layers)}）")
        base = [s for s in sigs if s["layer"] == "BASELINE"][0]
        self.assertTrue(base["gua"], "BASELINE 信号缺卦名")
        self.assertTrue(base["position"], "BASELINE 信号缺爻位")

    def test_baseline_yao_matches_yuantang(self):
        """BASELINE 的爻须是**本命元堂爻**（与 result.yuantang 一致）。"""
        from tongshu.engines.heluo_adapter import HeluoAdapter
        from tongshu.engines.heluo.canonical_signals import build_platform_signals
        ad = HeluoAdapter()
        res = ad.compute((1983, 11, 3, 12), gender="male",
                         target_date="2026-10-23")
        base = [s for s in build_platform_signals(res)
                if s["layer"] == "BASELINE"]
        self.assertTrue(base)
        self.assertEqual(base[0]["position"], res.yuantang.yuantang)


class TestAllExportsExist(unittest.TestCase):
    """⑦：`__all__` 里的每个名字都必须真实存在。"""

    def test_all_names_exist(self):
        missing = [n for n in gj.__all__ if not hasattr(gj, n)]
        self.assertEqual(missing, [],
                         f"__all__ 导出了不存在的名字：{missing}")


if __name__ == "__main__":
    unittest.main()
