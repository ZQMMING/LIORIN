# -*- coding: utf-8 -*-
"""禄命法引擎 (Luming) Oracle 测试。

目的:
- 验证 from_bazi_chart 唯一构造路径 + provenance 门
- 验证年本三元立极 (干禄/支命/纳音身 + 旺衰) 输出 = 手算期望
- 验证禄马视图 (互见/同宫)
- 验证天乙贵人 (年干/日干双查, 昼夜分治)
- 验证化气判定 (五行精纪口径):
    天干五合成立 (局月+次月 / 妒合不化)
    地支六合 = 合气助力 (非独立化气)
    三合成局 (局全即成, 附得令/透干)
- 验证岁运消费透传

架构约束:
- 只消费 BaziChart, 不重算排盘事实 (MUST NOT recompute)
- 不修改任何既有引擎
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.bazi_engine import (
    BaziEngine, BaziChart, Pillar, attach_p2_fields,
)
from tongshu.luming.engine import LumingEngine, from_bazi_chart, query_year
from tongshu.luming.types import LumingChart, assert_luming_gate


def _make_chart(stems_branches):
    """手动构造四柱 (合法 60 甲子对) + attach 全字段."""
    pillars = [Pillar(s, b) for s, b in stems_branches]
    chart = BaziChart(
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        day_master=pillars[2].heavenly_stem,
        luck_pillars=[],
        gender="male",
    )
    return attach_p2_fields(chart)


def _make_chart_luck(stems_branches, luck, birth=None):
    """手动构造四柱 + 大运 (岁运消费测试)."""
    import datetime as _dt
    pillars = [Pillar(s, b) for s, b in stems_branches]
    lucks = [Pillar(s, b) for s, b in luck]
    chart = BaziChart(
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        day_master=pillars[2].heavenly_stem,
        luck_pillars=lucks,
        gender="male",
        birth_datetime=birth or _dt.datetime(2000, 1, 1, 12),
    )
    return attach_p2_fields(chart)


class TestProvenanceGate(unittest.TestCase):
    """唯一构造路径 + provenance 门."""

    def test_01_from_bazi_chart_registers_provenance(self):
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart)
        self.assertIsInstance(lm, LumingChart)
        self.assertTrue(lm.provenance == "from_bazi_chart")

    def test_02_direct_construction_fails_gate(self):
        """直接实例化 LumingChart 不得通过 gate (MUST NOT recompute)."""
        direct = LumingChart()
        with self.assertRaises(ValueError):
            assert_luming_gate(direct)

    def test_03_engine_compute_equivalent(self):
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm1 = from_bazi_chart(chart)
        lm2 = LumingEngine().compute(chart)
        self.assertEqual(lm1.to_dict(), lm2.to_dict())


class TestSanYuanRealCharts(unittest.TestCase):
    """年本三元立极 (真实命例)."""

    def setUp(self):
        self.engine = BaziEngine()

    def test_10_case_a_19900101(self):
        """1990-01-01 12:00 男: 己巳 丙子 丙寅 甲午. 月支子(冬,水旺)."""
        lm = from_bazi_chart(self.engine.compute((1990, 1, 1, 12), gender="male"))
        sy = lm.san_yuan
        # 干禄: 己禄午(临) + 己对四支十二宫 (禄命法天干长生: 己卯长生顺)
        self.assertEqual(sy["lu"]["stem"], "JI")
        self.assertEqual(sy["lu"]["lu_branch"], "WU")
        self.assertTrue(sy["lu"]["present"])
        self.assertEqual(sy["lu"]["growth"],
                         {"year": "冠带", "month": "绝", "day": "养", "hour": "临官"})
        # 支命: 巳火在冬 = 死 (冬水旺, 火死)
        self.assertEqual(sy["ming"]["branch"], "SI")
        self.assertEqual(sy["ming"]["element"], "FIRE")
        self.assertEqual(sy["ming"]["season"], "WINTER")
        self.assertEqual(sy["ming"]["month_wang_shuai"], "死")
        # 纳音身: 大林木(木)在冬 = 相 (水旺木相)
        self.assertEqual(sy["shen"]["nayin"], "大林木")
        self.assertEqual(sy["shen"]["element"], "WOOD")
        self.assertEqual(sy["shen"]["month_wang_shuai"], "相")

    def test_11_case_b_20000815(self):
        """2000-08-15 12:00 男: 庚辰 甲申 乙巳 壬午. 月支申(秋,金旺)."""
        lm = from_bazi_chart(self.engine.compute((2000, 8, 15, 12), gender="male"))
        sy = lm.san_yuan
        self.assertEqual(sy["lu"]["stem"], "GENG")
        self.assertEqual(sy["lu"]["lu_branch"], "SHEN")
        self.assertTrue(sy["lu"]["present"])
        self.assertEqual(sy["lu"]["growth"],
                         {"year": "养", "month": "临官", "day": "长生", "hour": "沐浴"})
        # 支命: 辰土在秋 = 休
        self.assertEqual(sy["ming"]["branch"], "CHEN")
        self.assertEqual(sy["ming"]["element"], "EARTH")
        self.assertEqual(sy["ming"]["season"], "AUTUMN")
        self.assertEqual(sy["ming"]["month_wang_shuai"], "休")
        # 纳音身: 白蜡金(金)在秋 = 旺
        self.assertEqual(sy["shen"]["nayin"], "白蜡金")
        self.assertEqual(sy["shen"]["element"], "METAL")
        self.assertEqual(sy["shen"]["month_wang_shuai"], "旺")

    def test_12_zagi_month_earth_season(self):
        """杂气月 (丑月) → 土旺四季月. 甲子年己丑月: 年支子(水)在四季土月=死."""
        chart = _make_chart([("JIA", "ZI"), ("JI", "CHOU"), ("BING", "YIN"), ("WU", "WU")])
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.san_yuan["ming"]["season"], "EARTH_SEASON")
        self.assertEqual(lm.san_yuan["ming"]["branch"], "ZI")
        self.assertEqual(lm.san_yuan["ming"]["element"], "WATER")
        self.assertEqual(lm.san_yuan["ming"]["month_wang_shuai"], "死")   # 水在四季土月=死
        # 纳音身: 甲子=海中金(金) 在四季土月 = 相
        self.assertEqual(lm.san_yuan["shen"]["nayin"], "海中金")
        self.assertEqual(lm.san_yuan["shen"]["element"], "METAL")
        self.assertEqual(lm.san_yuan["shen"]["month_wang_shuai"], "相")
        # 干禄: 甲禄在寅 (四支 子丑寅午 含寅 → 临)
        self.assertEqual(lm.san_yuan["lu"]["lu_branch"], "YIN")
        self.assertTrue(lm.san_yuan["lu"]["present"])


class TestLuMa(unittest.TestCase):
    """禄马视图."""

    def test_20_case_a_lu_present_ma_absent(self):
        """1990-01-01: 己禄午临(真), 巳酉丑驿马在亥(不临)."""
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.lu_ma["lu"]["lu_branch"], "WU")
        self.assertTrue(lm.lu_ma["lu"]["present"])
        self.assertEqual(lm.lu_ma["ma"]["branch"], "HAI")
        self.assertFalse(lm.lu_ma["ma"]["present"])
        self.assertFalse(lm.lu_ma["lu_ma_both_present"])
        self.assertFalse(lm.lu_ma["lu_ma_same_branch"])

    def test_21_case_b_ma_absent(self):
        """2000-08-15: 庚禄申临(真), 申子辰驿马在寅(不临)."""
        chart = BaziEngine().compute((2000, 8, 15, 12), gender="male")
        lm = from_bazi_chart(chart)
        self.assertTrue(lm.lu_ma["lu"]["present"])
        self.assertEqual(lm.lu_ma["ma"]["branch"], "YIN")
        self.assertFalse(lm.lu_ma["ma"]["present"])

    def test_22_lu_ma_same_branch(self):
        """禄马同宫: 甲子年 (甲禄寅, 申子辰马在寅) 寅时临. 手动构造四支含寅."""
        chart = _make_chart([("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN"), ("GENG", "WU")])
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.lu_ma["lu"]["lu_branch"], "YIN")
        self.assertEqual(lm.lu_ma["ma"]["branch"], "YIN")
        self.assertTrue(lm.lu_ma["lu"]["present"])
        self.assertTrue(lm.lu_ma["ma"]["present"])
        self.assertTrue(lm.lu_ma["lu_ma_both_present"])
        self.assertTrue(lm.lu_ma["lu_ma_same_branch"])


class TestGuiRen(unittest.TestCase):
    """天乙贵人 (年干为主, 日干辅助, 昼夜分治)."""

    def test_30_case_a_day_gui_ren(self):
        """1990-01-01 午时(昼): 己年旦贵在子(临), 丙日旦贵在亥(不临)."""
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart)
        gr = lm.gui_ren
        self.assertEqual(gr["day_night"], "day")
        self.assertEqual(gr["by_year"]["stem"], "JI")
        self.assertEqual(gr["by_year"]["gui_ren_branch"], "ZI")   # 乙己旦子暮申
        self.assertTrue(gr["by_year"]["present"])                  # 子在四支
        self.assertEqual(gr["by_day"]["stem"], "BING")
        self.assertEqual(gr["by_day"]["gui_ren_branch"], "HAI")   # 丙丁旦亥暮酉
        self.assertFalse(gr["by_day"]["present"])                  # 亥不在四支

    def test_31_case_b_night_gui_ren(self):
        """2000-08-15 午时(昼): 庚年旦贵在丑(不临), 乙日旦贵在子(不临)."""
        chart = BaziEngine().compute((2000, 8, 15, 12), gender="male")
        lm = from_bazi_chart(chart)
        gr = lm.gui_ren
        self.assertEqual(gr["day_night"], "day")
        self.assertEqual(gr["by_year"]["gui_ren_branch"], "CHOU")  # 甲戊庚旦丑暮未
        self.assertFalse(gr["by_year"]["present"])
        self.assertEqual(gr["by_day"]["gui_ren_branch"], "ZI")     # 乙己旦子暮申
        self.assertFalse(gr["by_day"]["present"])

    def test_32_night_birth_uses_night_gui_ren(self):
        """亥时(夜)生: 甲戊庚用暮贵人未. 手动构造甲子年 + 亥时."""
        chart = _make_chart([("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN"), ("YI", "HAI")])
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.gui_ren["day_night"], "night")
        # 年干甲, 暮贵: 甲戊庚→未
        self.assertEqual(lm.gui_ren["by_year"]["gui_ren_branch"], "WEI")
        self.assertFalse(lm.gui_ren["by_year"]["present"])   # 四支无未
        # 日干戊, 暮贵: 甲戊庚→未 (同样为未)
        self.assertEqual(lm.gui_ren["by_day"]["gui_ren_branch"], "WEI")


class TestHuaQi(unittest.TestCase):
    """化气判定 (五行精纪口径)."""

    def test_40_wuhe_not_deling(self):
        """甲己合土, 月支子(非土局月) → 未得令 → 不化."""
        chart = _make_chart([("JI", "CHOU"), ("JIA", "ZI"), ("WU", "YIN"), ("BING", "WU")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("wuhe:JIA-JI", {})
        self.assertEqual(item.get("element"), "EARTH")
        self.assertFalse(item.get("de_ling"))      # 子月不在辰戌丑未亥
        self.assertFalse(item.get("du_he"))
        self.assertFalse(item.get("transformed"))

    def test_41_wuhe_transformed(self):
        """甲己合土 + 辰月(土局月) + 无乙 → 真化."""
        chart = _make_chart([("BING", "ZI"), ("JIA", "CHEN"), ("WU", "YIN"), ("JI", "SI")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("wuhe:JIA-JI", {})
        self.assertEqual(item.get("element"), "EARTH")
        self.assertTrue(item.get("de_ling"))       # 辰月 ∈ 辰戌丑未亥
        self.assertFalse(item.get("du_he"))        # 无乙
        self.assertTrue(item.get("transformed"))

    def test_42_wuhe_duhe_blocked(self):
        """甲己合土 + 辰月 + 乙干透 → 妒合不化."""
        chart = _make_chart([("YI", "CHOU"), ("JIA", "CHEN"), ("WU", "YIN"), ("JI", "SI")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("wuhe:JIA-JI", {})
        self.assertTrue(item.get("de_ling"))       # 辰月得令
        self.assertTrue(item.get("du_he"))         # 乙为妒合干
        self.assertFalse(item.get("transformed"))  # 妒合不化

    def test_43_real_case_b_wuhe_geng_yi(self):
        """2000-08-15 庚辰 甲申 乙巳 壬午: 乙庚合金, 申月(金局月) → 真化."""
        chart = BaziEngine().compute((2000, 8, 15, 12), gender="male")
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("wuhe:YI-GENG", {})
        self.assertEqual(item.get("element"), "METAL")
        self.assertTrue(item.get("de_ling"))       # 申月 ∈ 巳酉丑申
        self.assertFalse(item.get("du_he"))        # 无丙
        self.assertTrue(item.get("transformed"))

    def test_44_liuhe_is_zhuli_not_huaqi(self):
        """2000-08-15 巳申合水 → 六合为助力, 不独立判化气."""
        chart = BaziEngine().compute((2000, 8, 15, 12), gender="male")
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("liuhe:SHEN-SI", {})
        self.assertEqual(item.get("element"), "WATER")
        self.assertEqual(item.get("role"), "助力")
        self.assertFalse(item.get("transformed"))

    def test_45_sanhe_chengju_always_transformed(self):
        """申子辰三合水局: 三支全即成局 (得令透干与否不影响成局)."""
        chart = _make_chart([("JIA", "ZI"), ("BING", "SHEN"), ("WU", "CHEN"), ("GENG", "WU")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("sanhe:CHEN-SHEN-ZI", {})
        self.assertEqual(item.get("element"), "WATER")
        self.assertTrue(item.get("transformed"))   # 局全即成
        self.assertFalse(item.get("de_ling"))      # 申月非水旺月
        self.assertFalse(item.get("tou_gan"))      # 四干无壬癸

    def test_46_sanhe_with_deling_tougan(self):
        """申子辰三合水 + 亥月(水月) + 壬透 → 成局且得令透干.

        构造: 甲申 乙亥 壬子 戊辰 (四支 申亥子辰 → 三合全, 月支亥水月, 日干壬透).
        """
        chart = _make_chart([("JIA", "SHEN"), ("YI", "HAI"), ("REN", "ZI"), ("WU", "CHEN")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("sanhe:CHEN-SHEN-ZI", {})
        self.assertTrue(item.get("transformed"))
        self.assertTrue(item.get("de_ling"))       # 亥月 ∈ 亥子丑
        self.assertTrue(item.get("tou_gan"))       # 壬透


class TestShenSha(unittest.TestCase):
    """禄命法神煞视图 (年支查)."""

    def test_60_case_a_shen_sha(self):
        """1990-01-01 己巳年: 巳酉丑 → 将星酉/华盖丑/劫煞寅/亡神申, 桃花午.
        四支[巳,子,寅,午]: 劫煞寅临, 桃花午临, 余不临."""
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        ss = from_bazi_chart(chart).shen_sha
        self.assertEqual(ss["jiang_xing"]["branch"], "YOU")
        self.assertFalse(ss["jiang_xing"]["present"])
        self.assertEqual(ss["hua_gai"]["branch"], "CHOU")
        self.assertFalse(ss["hua_gai"]["present"])
        self.assertEqual(ss["jie_sha"]["branch"], "YIN")
        self.assertTrue(ss["jie_sha"]["present"])
        self.assertEqual(ss["wang_shen"]["branch"], "SHEN")
        self.assertFalse(ss["wang_shen"]["present"])
        self.assertEqual(ss["tao_hua"]["branch"], "WU")
        self.assertTrue(ss["tao_hua"]["present"])
        # 孤辰寡宿: 巳午未 → (申, 辰); 申辰均不临
        self.assertEqual(ss["gu_chen"]["branch"], "SHEN")
        self.assertFalse(ss["gu_chen"]["present"])
        self.assertEqual(ss["gu_su"]["branch"], "CHEN")
        self.assertFalse(ss["gu_su"]["present"])


class TestLuckScope(unittest.TestCase):
    """岁运消费."""

    def test_50_luck_pillars_passthrough(self):
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.luck_scope["start_age"], chart.start_age)
        self.assertEqual(lm.luck_scope["luck_pillars"][0], ("YI", "HAI"))
        self.assertEqual(lm.luck_scope["xiaoyun"], "")

    def test_51_nayin_passthrough(self):
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.nayin["year"], "大林木")
        self.assertEqual(lm.nayin_five_element["year"], "WOOD")

    def test_52_xiaoyun_consumed_with_current_datetime(self):
        """提供 current_datetime 时消费小运 (古法固定起: 男丙寅顺, 1岁起本身).
        2026-10-21 口径统一: 运层/流年层小运一律古法 (壬申逆/丙寅顺), 弃醉醒子从时起."""
        from datetime import datetime
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        lm = from_bazi_chart(chart, current_datetime=datetime(2026, 10, 18))
        xy = lm.luck_scope["xiaoyun"]
        # 1990 男 1岁丙寅; 2026 虚岁=37 → 丙寅+36=壬寅 (序号2+36=38)
        self.assertEqual(xy, "RENYIN")
        self.assertEqual(lm.luck_scope["xiaoyun_zhi"], "YIN")


class TestClassicInstances(unittest.TestCase):
    """《五行精纪》真实命例 ground truth (L2)."""

    def test_70_fengjing_mu_wang_yu_mao(self):
        """冯京: 辛酉年 辛卯月 癸丑日 辛酉时 (五行精纪卷·五行一字).
        原文评: '木旺于卯' — 年纳音辛酉=石榴木, 卯月木旺 → 引擎须输出 旺."""
        chart = _make_chart([("XIN", "YOU"), ("XIN", "MAO"), ("GUI", "CHOU"), ("XIN", "YOU")])
        lm = from_bazi_chart(chart)
        self.assertEqual(lm.san_yuan["shen"]["nayin"], "石榴木")
        self.assertEqual(lm.san_yuan["shen"]["element"], "WOOD")
        self.assertEqual(lm.san_yuan["shen"]["season"], "SPRING")
        self.assertEqual(lm.san_yuan["shen"]["month_wang_shuai"], "旺")   # 木旺于卯

    def test_71_zhenqi_jiaohu_wu_gui(self):
        """真气交互格: 戊戌年 癸亥月 丁巳日 辛亥时 (五行精纪·真气交互格, 宰相命例).
        合气往来存在 (wuhe:WU-GUI), 但亥月非戊癸化火之月 → 化气未成 (合与化分离)."""
        chart = _make_chart([("WU", "XU"), ("GUI", "HAI"), ("DING", "SI"), ("XIN", "HAI")])
        lm = from_bazi_chart(chart)
        item = lm.hua_qi.get("wuhe:WU-GUI", {})
        self.assertEqual(item.get("element"), "FIRE")
        self.assertFalse(item.get("du_he"))          # 四干无己
        self.assertFalse(item.get("de_ling"))        # 亥月 ∉ 寅午戌巳
        self.assertFalse(item.get("transformed"))    # 合而不化 (真气往来≠月令化气)


class TestVerdicts(unittest.TestCase):
    """结构化断语 (确定性事实 → 原文断语)."""

    def _ids(self, lm):
        return [v["rule_id"] for v in lm.verdicts]

    def test_80_case_b_huaqi_and_huagai(self):
        """2000-08-15: 乙庚真化(LM-V08) + 华盖辰临(LM-V10)."""
        chart = BaziEngine().compute((2000, 8, 15, 12), gender="male")
        ids = self._ids(from_bazi_chart(chart))
        self.assertIn("LM-V08", ids)   # 乙庚合金申月真化
        self.assertIn("LM-V10", ids)   # 华盖辰临
        self.assertNotIn("LM-V01", ids)  # 支命辰土秋=休, 三元非皆旺

    def test_81_case_a_tao_hua(self):
        """1990-01-01: 桃花午临 → LM-V11; 三元非全旺/全死 → 无 V01/V02."""
        chart = BaziEngine().compute((1990, 1, 1, 12), gender="male")
        ids = self._ids(from_bazi_chart(chart))
        self.assertIn("LM-V11", ids)
        self.assertNotIn("LM-V01", ids)
        self.assertNotIn("LM-V02", ids)

    def test_82_san_yuan_all_qi(self):
        """三元皆旺 → LM-V01: 丙寅年(炉中火相) 寅月(支命木旺) 丙禄巳临."""
        chart = _make_chart([("BING", "YIN"), ("JIA", "YIN"), ("WU", "WU"), ("XIN", "SI")])
        lm = from_bazi_chart(chart)
        ids = self._ids(lm)
        self.assertIn("LM-V01", ids)
        self.assertNotIn("LM-V02", ids)

    def test_82b_fengjing_huagai_only(self):
        """冯京(辛酉年): 华盖丑临(LM-V10); 支命酉金在春=囚 → 三元非皆旺."""
        chart = _make_chart([("XIN", "YOU"), ("XIN", "MAO"), ("GUI", "CHOU"), ("XIN", "YOU")])
        ids = self._ids(from_bazi_chart(chart))
        self.assertIn("LM-V10", ids)
        self.assertNotIn("LM-V01", ids)

    def test_83_duhe_verdict(self):
        """甲己合土带乙(妒合) → LM-V09."""
        chart = _make_chart([("YI", "CHOU"), ("JIA", "CHEN"), ("WU", "YIN"), ("JI", "SI")])
        ids = self._ids(from_bazi_chart(chart))
        self.assertIn("LM-V09", ids)

    def test_84_lu_ma_same_verdict(self):
        """甲子年寅时: 禄马同宫 → LM-V03."""
        chart = _make_chart([("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN"), ("GENG", "WU")])
        ids = self._ids(from_bazi_chart(chart))
        self.assertIn("LM-V03", ids)


class TestEvidenceRegistration(unittest.TestCase):
    """证据链单源: luming.EVIDENCE_IDS == bazi_facts 主登记 LM_* 条目."""

    def test_90_evidence_single_source(self):
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        from tongshu.luming.facts import EVIDENCE_IDS as LM
        main_lm = {k: v for k, v in MAIN.items() if k.startswith("LM_")}
        self.assertEqual(dict(LM), main_lm)

    def test_91_evidence_ids_verified(self):
        """证据卷次已核原文 (E-WXJ: 章=五行精纪正文卷标记)."""
        from tongshu.luming.facts import EVIDENCE_IDS as LM
        self.assertEqual(LM["LM_WANG_XIANG"], "E-WXJ-007-001")   # L1410 卷七
        self.assertEqual(LM["LM_SAN_YUAN"], "E-WXJ-009-001")     # L1598 卷九
        self.assertEqual(LM["LM_HUA_QI"], "E-WXJ-004-001")       # L814 卷四
        self.assertEqual(LM["LM_GUI_REN"], "E-WXJ-014-001")      # L2183 卷十四
        self.assertEqual(LM["LM_YI_MA"], "E-WXJ-016-001")        # L2308 卷十六
        self.assertEqual(LM["LM_TAO_HUA"], "E-WXJ-026-001")      # L3523 卷廿六
        self.assertEqual(LM["LM_HUA_GAI"], "E-WXJ-020-001")      # L2802 卷二十
        self.assertEqual(LM["LM_WXJ_SHOU_YAO"], "E-WXJ-031-001~006")  # 论寿夭
        self.assertEqual(LM["LM_LT_ESHA"], "E-LT-008-002~008")       # 兰台中篇恶煞
        self.assertEqual(LM["LM_WXJ_HUNYU"], "E-WXJ-029-001~008")    # 论夫妇/论子息


    def test_92_cross_reference_smth(self):
        """互证登记: 每条规则都有互证出处 (SMTH 主源↔WXJ/兰台, 或 WXJ 主源↔SMTH), 结论字段非空."""
        from tongshu.luming.facts import CROSS_REFERENCES, EVIDENCE_IDS as LM
        self.assertEqual(set(CROSS_REFERENCES), set(LM.keys()))
        for k, rec in CROSS_REFERENCES.items():
            self.assertTrue(rec["smth"]["ref"], k)
            self.assertTrue(rec["smth"]["verdict"], k)
            self.assertTrue(rec["smth"]["detail"], k)

    def test_93_cross_reference_key_points(self):
        """互证关键点: 妒合异文/土月水死/岁运依据 均已登记."""
        from tongshu.luming.facts import CROSS_REFERENCES
        self.assertIn("异文", CROSS_REFERENCES["LM_HUA_QI"]["smth"]["verdict"])
        self.assertIn("一致", CROSS_REFERENCES["LM_WANG_XIANG"]["smth"]["verdict"])
        self.assertIn("岁运", CROSS_REFERENCES["LM_GUI_REN"]["smth"]["detail"])
        self.assertIn("岁运", CROSS_REFERENCES["LM_YI_MA"]["smth"]["detail"])

    # --- 神煞交叉组合断语 (V12-V15) ---

    def test_94_verdict_gui_ren_jie_sha_same_branch(self):
        """LM-V12 贵人并劫煞同支: 丙寅年 劫煞亥=贵人亥."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("BING", "YIN"), ("JI", "HAI"), ("JIA", "ZI"), ("BING", "ZI")])
        lm = from_bazi_chart(chart)
        self.assertIn("LM-V12", {v["rule_id"] for v in lm.verdicts})

    def test_95_verdict_tao_hua_gui_lu(self):
        """LM-V13 桃花并贵人: 丙申年 桃花酉=贵人酉(丙夜贵酉)."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("BING", "SHEN"), ("JI", "HAI"), ("REN", "WU"), ("XIN", "YOU")])
        lm = from_bazi_chart(chart)
        self.assertIn("LM-V13", {v["rule_id"] for v in lm.verdicts})

    def test_96_verdict_liuhe_tao_hua(self):
        """LM-V15 六合并桃花: 戊戌年 卯戌六合, 寅午戌桃花在卯."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("WU", "XU"), ("YI", "MAO"), ("JIA", "ZI"), ("BING", "YIN")])
        lm = from_bazi_chart(chart)
        self.assertIn("LM-V15", {v["rule_id"] for v in lm.verdicts})

    def test_97_verdict_hua_gai_gu_su_parallel(self):
        """LM-V14 华盖孤寡面与 V10 聪明面并存 (同事实两书角度)."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("WU", "CHEN"), ("BING", "CHEN"), ("JIA", "ZI"), ("BING", "ZI")])
        lm = from_bazi_chart(chart)
        ids = {v["rule_id"] for v in lm.verdicts}
        self.assertIn("LM-V10", ids)
        self.assertIn("LM-V14", ids)

    def test_98_evidence_combined_ids_registered(self):
        """组合断语证据 ID 已注册进主登记 (单源)."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        for k in ("LM_GUI_REN_JIE_SHA", "LM_HE_XIAN_CHI", "LM_XIAN_CHI_GUI_LU"):
            self.assertIn(k, MAIN)
        self.assertEqual(MAIN["LM_GUI_REN_JIE_SHA"], "E-WXJ-014-002")
        self.assertEqual(MAIN["LM_HE_XIAN_CHI"], "E-WXJ-018-001")
        self.assertEqual(MAIN["LM_XIAN_CHI_GUI_LU"], "E-WXJ-026-002")

    # --- 岁运消费 (V16-V22) ---

    def test_99_luck_pillar_view_shape(self):
        """运柱视图: 每柱含三元+见神煞字段, 值为确定性类型."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "YIN"), ("BING", "CHEN"), ("JI", "WEI"), ("XIN", "YOU")],
        )
        lm = from_bazi_chart(chart)
        ps = lm.luck_scope["pillars"]
        self.assertEqual(len(ps), 4)
        for pv in ps:
            for k in ("stem", "branch", "nayin", "element", "dry_lu_branch",
                      "sees_gui_ren", "sees_lu", "sees_ma", "sees_hua_gai",
                      "sees_tao_hua", "lu_ma_same", "gui_ren_ma_same"):
                self.assertIn(k, pv)
            self.assertIsInstance(pv["sees_gui_ren"], bool)
        self.assertEqual(ps[0]["nayin"], "大溪水")   # 甲寅纳音

    def test_100_luck_verdicts_trigger(self):
        """岁运断语触发: 甲子年(马寅/禄寅/贵丑未/华盖辰/桃花酉) 大运含对应支.

        甲寅柱 → 见禄+见马+禄马同位 (V17/V18/V21)
        丙辰柱 → 见华盖 (V19)    己未柱 → 见贵人 (V16)   辛酉柱 → 见咸池 (V20)
        """
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "YIN"), ("BING", "CHEN"), ("JI", "WEI"), ("XIN", "YOU")],
        )
        lm = from_bazi_chart(chart)
        ids = {v["rule_id"] for v in lm.verdicts}
        for rid in ("LM-V16", "LM-V17", "LM-V18", "LM-V19", "LM-V20", "LM-V21"):
            self.assertIn(rid, ids)

    def test_101_luck_verdict_no_ma_same_no_trigger(self):
        """未触发场景: 大运不含本命禄马贵人华盖桃花 → 无 V16~V22."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("DING", "MAO"), ("WU", "CHEN")],   # 卯/辰: 非马寅非禄寅非贵丑未非桃花酉; 辰是华盖→V19 会触发
        )
        lm = from_bazi_chart(chart)
        ids = {v["rule_id"] for v in lm.verdicts}
        # 丁卯柱无任何本命神煞命中; 戊辰柱辰=华盖 → 只有 V19
        self.assertNotIn("LM-V16", ids)
        self.assertNotIn("LM-V17", ids)
        self.assertNotIn("LM-V18", ids)
        self.assertNotIn("LM-V20", ids)
        self.assertNotIn("LM-V21", ids)
        self.assertIn("LM-V19", ids)

    def test_102_luck_evidence_registered(self):
        """岁运证据 ID 已注册 (E-WXJ-033/034)."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        self.assertEqual(MAIN["LM_ER_YUN_GUI_REN"], "E-WXJ-034-001")
        self.assertEqual(MAIN["LM_ER_YUN_XIAN_CHI"], "E-WXJ-034-002")
        self.assertEqual(MAIN["LM_DA_YUN_LU_MA"], "E-WXJ-033-001")
        self.assertEqual(MAIN["LM_DA_YUN_GUI_SHEN"], "E-WXJ-033-002")

    # --- 二运喜会/厄会 + 伏吟返吟 + 太岁 (V23~V30) ---

    def test_103_growth_stage_tool(self):
        """十二宫工具: 木长生亥 → 亥长生/卯帝旺/午死/未墓/申绝."""
        from tongshu.luming.engine import _growth_stage
        self.assertEqual(_growth_stage("WOOD", "HAI"), "长生")
        self.assertEqual(_growth_stage("WOOD", "MAO"), "帝旺")
        self.assertEqual(_growth_stage("WOOD", "WU"), "死")
        self.assertEqual(_growth_stage("WOOD", "WEI"), "墓")
        self.assertEqual(_growth_stage("WOOD", "SHEN"), "绝")
        self.assertEqual(_growth_stage("WATER", "SHEN"), "长生")   # 水长生申
        self.assertEqual(_growth_stage("EARTH", "SHEN"), "长生")   # 土长生申

    def test_104_verdict_fu_yin(self):
        """V25 伏吟: 甲子年, 大运首柱支子=本命支 (current age<10)."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2002, 6, 1, 12))
        self.assertIn("LM-V25", {v["rule_id"] for v in lm.verdicts})

    def test_105_verdict_tai_sui_ru_zhai(self):
        """V26 太岁入宅: 甲子年宅巳, 2025 乙巳年太岁=巳."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2025, 6, 1, 12))
        self.assertIn("LM-V26", {v["rule_id"] for v in lm.verdicts})

    def test_106_verdict_zhuang_ming(self):
        """V27 撞命杀: 日柱庚子, 2020 庚子年太岁=日柱."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("GENG", "ZI"), ("BING", "YIN")],
            [("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2020, 6, 1, 12))
        self.assertIn("LM-V27", {v["rule_id"] for v in lm.verdicts})

    def test_107_verdict_xi_hui_jiu(self):
        """V23 喜会⑨: 癸丑男命古法小运(丙寅顺) 2010虚岁10=乙亥 + 大运丙亥 → 禄命旺乡{子亥巳午}."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("GUI", "CHOU"), ("DING", "SI"), ("GENG", "ZI"), ("BING", "ZI")],
            [("JIA", "YIN"), ("BING", "HAI"), ("WU", "CHEN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2010, 7, 1, 12))  # 虚岁10 → 小运乙亥(亥∈旺乡) + 大运丙亥
        self.assertIn("LM-V23", {v["rule_id"] for v in lm.verdicts})

    def test_108_verdict_e_hui_chong(self):
        """V24 厄会③: 大运子冲小运午 (age≈5 → 首柱子 + 小运午)."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2005, 7, 1, 12))  # age≈5 → 首柱子 + 小运午(冲子)
        self.assertIn("LM-V24", {v["rule_id"] for v in lm.verdicts})

    def test_109_xiaoyun_and_liunian_view(self):
        """luck_scope 新字段: xiaoyun_zhi / liu_nian 视图齐全."""
        import datetime as _dt
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart_luck(
            [("JIA", "ZI"), ("GENG", "WU"), ("JIA", "XU"), ("BING", "YIN")],
            [("JIA", "ZI"), ("BING", "YIN")],
            birth=_dt.datetime(2000, 1, 1, 12),
        )
        lm = from_bazi_chart(chart, _dt.datetime(2025, 6, 1, 12))
        lv = lm.luck_scope
        self.assertTrue(lv["xiaoyun_zhi"])
        self.assertEqual(lv["liu_nian"]["branch"], "SI")   # 2025 乙巳
        for k in ("sees_gui_ren", "sees_lu", "sees_ma", "in_zhai",
                  "zhuang_ming", "xing_dayun"):
            self.assertIsInstance(lv["liu_nian"][k], bool)

    def test_110_new_evidence_registered(self):
        """V23~V29 证据已注册 (单源)."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        self.assertEqual(MAIN["LM_ER_YUN_XI_HUI"], "E-WXJ-034-003")
        self.assertEqual(MAIN["LM_ER_YUN_E_HUI"], "E-WXJ-034-004")
        self.assertEqual(MAIN["LM_FU_YIN_FAN_YIN"], "E-WXJ-033-003")
        self.assertEqual(MAIN["LM_TAI_SUI_ZHAI"], "E-WXJ-034-005")
        self.assertEqual(MAIN["LM_ZHUANG_MING"], "E-WXJ-034-006")
        self.assertEqual(MAIN["LM_TAI_SUI_XING_DAYUN"], "E-WXJ-034-007")
        self.assertEqual(MAIN["LM_TAI_SUI_GU_SU"], "E-WXJ-034-008")

    def test_111_lu_growth_luming_parity(self):
        """干禄旺衰用禄命法天干十二长生 (广信集 L2234), 非五行寄生非子平表.

        癸(阴水) 卯长生逆行: 在亥=帝旺 / 戌=衰 / 未=墓 / 午=绝.
        (广信集癸卯逆布 与 子平表癸 一致; 分歧仅在戊己两干。)
        """
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("GUI", "HAI"), ("REN", "XU"), ("YI", "WEI"), ("REN", "WU")])
        lm = from_bazi_chart(chart)
        g = lm.san_yuan["lu"]["growth"]
        self.assertEqual(g, {"year": "帝旺", "month": "衰", "day": "墓", "hour": "绝"})

    def test_112_lu_growth_jia_zi(self):
        """甲(阳木) 亥长生顺行: 在子=沐浴 / 辰=衰 / 午=死 / 申=绝."""
        from tongshu.luming.engine import from_bazi_chart
        chart = _make_chart([("JIA", "ZI"), ("BING", "YIN"), ("WU", "CHEN"), ("GENG", "SHEN")])
        lm = from_bazi_chart(chart)
        g = lm.san_yuan["lu"]["growth"]
        self.assertEqual(g["year"], "沐浴")
        self.assertEqual(g["day"], "衰")     # 辰
        self.assertEqual(g["hour"], "绝")    # 申

    def test_113_lu_growth_wu_ji_guangxiji(self):
        """广信集关键分歧: 戊申长生逆 / 己卯长生顺 (与子平表戊寅/己酉不同)."""
        from tongshu.luming.engine import _growth_stage_stem, _stage_branch_stem
        self.assertEqual(_growth_stage_stem("WU", "SI"), "临官")
        self.assertEqual(_growth_stage_stem("WU", "WU"), "冠带")
        self.assertEqual(_growth_stage_stem("WU", "ZI"), "墓")
        self.assertEqual(_growth_stage_stem("JI", "WU"), "临官")
        self.assertEqual(_growth_stage_stem("JI", "SI"), "冠带")
        self.assertEqual(_growth_stage_stem("JI", "ZI"), "绝")
        self.assertEqual(_growth_stage_stem("JI", "WEI"), "帝旺")
        # 反查
        self.assertEqual(_stage_branch_stem("WU", "临官"), "SI")
        self.assertEqual(_stage_branch_stem("JI", "临官"), "WU")
        self.assertEqual(_stage_branch_stem("GUI", "帝旺"), "HAI")
        self.assertEqual(_stage_branch_stem("GUI", "绝"), "WU")

    def test_114_gap_batch3_case_19831103(self):
        """缺口第三批 oracle: 1983-11-3 午时坤造 癸亥 壬戌 乙未 壬午.

        原局三刑(恃势戌未; 亥/午单支非自刑——自刑须同支重逢 L3399/L3401)/
        六害(无)/纳音链(日金生我·时木我生·胎木我生·
        命宫木我生·身宫土克我)/文昌癸→丑不临/拱贵(亥未拱卯)/运柱(卯运见将星·
        乙丑运刑月日柱·丙寅三合寅午戌·丁卯合戌/三合亥卯未)/断语 V31~V41.
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1983, 11, 3, 12), gender="female",
                                     birth_datetime=_dt.datetime(1983, 11, 3, 12, 0))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        d = lm.to_dict()
        # 原局三刑
        types = sorted(s["type"] for s in d["san_xing"])
        self.assertEqual(types, ["恃势刑"])  # 单支亥/午非自刑 (2026-10-19 修正)
        sx_b = {s["type"]: s["branches"] for s in d["san_xing"]}
        self.assertEqual(set(sx_b["恃势刑"]), {"WEI", "XU"})
        # 六害无
        self.assertEqual(d["liu_hai"], [])
        # 纳音链
        nc = d["nayin_chain"]
        self.assertEqual(nc["year_nayin"], "大海水")
        pos = {p["pos"]: p for p in nc["positions"]}
        self.assertEqual(pos["日柱"]["relation"], "生我")   # 沙中金生大海水
        self.assertEqual(pos["时柱"]["relation"], "我生")   # 杨柳木泄水
        self.assertEqual(nc["tai_yuan"]["relation"], "我生")  # 桑柘木
        self.assertEqual(nc["gong"]["ming"]["relation"], "我生")  # 命宫癸丑桑柘木
        self.assertEqual(nc["gong"]["shen"]["relation"], "克我")  # 身宫丙辰沙中土
        # 文昌 (WXJ 年干表): 癸→丑, 不临
        self.assertEqual(d["wen_chang"]["branch"], "CHOU")
        self.assertFalse(d["wen_chang"]["present"])
        # 拱: 亥卯未缺卯 → 拱贵 (卯=癸年贵人)
        self.assertEqual([g["name"] for g in d["gong"]["sanhe"]], ["拱贵"])
        # 运柱消费
        pv = {p["stem"] + p["branch"]: p for p in d["luck_scope"]["pillars"]}
        self.assertTrue(pv["DINGMAO"]["sees_jiang_xing"])      # 卯=将星
        self.assertEqual(pv["YICHOU"]["xing_with"], "月柱、日柱")  # 丑刑戌未
        self.assertEqual(pv["JIAZI"]["clash_with"], "时柱")    # 子午冲
        self.assertEqual(pv["JIAZI"]["harm_with"], "日柱")     # 子未害
        self.assertEqual(pv["BINGYIN"]["sanhe_with"], "YINWUXU")
        self.assertEqual(pv["DINGMAO"]["sanhe_with"], "MAOWEIHAI")
        # 断语
        rids = [v["rule_id"] for v in d["verdicts"]]
        self.assertEqual(rids.count("LM-V31"), 1)  # 恃势刑 1 条 (单支自刑已剔除)
        self.assertIn("LM-V33", rids)
        self.assertIn("LM-V34", rids)
        self.assertIn("LM-V36", rids)
        self.assertIn("LM-V37", rids)
        self.assertIn("LM-V38", rids)
        self.assertIn("LM-V39", rids)
        self.assertIn("LM-V40", rids)
        self.assertIn("LM-V41", rids)
        # 新证据已注册 (单源)
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        self.assertEqual(MAIN["LM_NAYIN_QI_SHU"], "E-WXJ-008-001")
        self.assertEqual(MAIN["LM_WEN_CHANG"], "E-WXJ-013-001")
        self.assertEqual(MAIN["LM_SAN_XING"], "E-WXJ-025-001")
        self.assertEqual(MAIN["LM_LIU_HAI"], "E-WXJ-025-002")

    def test_115_evidence_cross_reference_complete(self):
        """LM 证据 33 条 ↔ bazi_facts 主登记 ↔ CROSS_REFERENCES 33 条 全对齐."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS as MAIN
        from tongshu.luming.facts import CROSS_REFERENCES, VERDICT_RULES, EVIDENCE_IDS as LM_EV
        lm_keys = {k for k in MAIN if k.startswith("LM_")}
        self.assertEqual(lm_keys, set(CROSS_REFERENCES))
        self.assertEqual(lm_keys, set(LM_EV))
        # 每条规则都有证据
        for r in VERDICT_RULES:
            self.assertIn(r["evidence"], {v for v in LM_EV.values()})
        self.assertEqual(len(VERDICT_RULES), 161)  # 160 + LM-F01~F06 岁运发用登记(2026-10-21, 引擎直生族)

    def test_116_tone_scope_case_19831103(self):
        """吉凶分级 oracle: 1983-11-3 坤造.

        原局 吉2/凶4/平4 (V33生我吉·V36拱贵吉; V02/V14/V31×1/V34身宫克我凶;
        V10/V33我生×2/V34命宫我生平); 当前丁卯运=偏吉(V16贵人+V37将星+V38合);
        overall 吉25 凶18 平22=偏吉; 乙丑运偏凶(V39冲+V40害+V41刑).
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1983, 11, 3, 12), gender="female",
                                     birth_datetime=_dt.datetime(1983, 11, 3, 12, 0))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        ts = lm.tone_scope
        orig = ts["layers"]["原局"]
        self.assertEqual((orig["吉"], orig["凶"], orig["平"]), (2, 1, 13))  # 2026-10-21: (3,1,12)→V85子星日主立极修正吉-1、V85-B食伤藏支平+1、V31H得印降V31H-L(凶转平)、V14华盖孤寡亲缘计入凶+1(原continue不计)、元辰口径修正(用户裁决阴女冲后=辰)后时支午非元辰→V108时带元辰不触发平-1; 2026-10-20: (2,2,6)+V85子星得力吉+1、V81火受亏平、V82水太过平、V84夫星不现平、V106时冲年平、V108时带煞平、V110狡害平 (健康/性情/六亲/婚育维度不扰方向); V02三元十二宫修正(癸亥三元皆旺) 凶-1
        # 当前运 (2026 时 43 虚岁 → 丁卯运): 偏吉
        cur = ts["current"]
        self.assertEqual(cur["pillar"], "DINGMAO")
        self.assertEqual(cur["verdict"], "偏吉")
        self.assertEqual(cur["counts"]["凶"], 2)   # V44 运支卯=大海水之死乡(凶) + F04 财化鬼(炉中火=财, 柱有土转克水, 2026-10-21 纳音口径)
        # overall (2026-10-20 限运切片: V126运到羊刃平+1、V124天罗壬戌癸亥凶+2、V125大小耗丙辰凶+1;
        #   喜忌覆盖: 癸亥运 V42 比和吉 → 犯忌降平 → 吉-1平+1;
        #   贵人年干口径: 甲子/壬申两运日干贵人(乙贵子申/庚贵)误判移除 → 吉-2;
        #   V02 三元十二宫口径: 癸亥禄(子)临官/命(亥)帝旺/身(癸亥)临官 皆不死绝 → 原局凶-1)
        self.assertEqual(ts["overall"]["counts"],
                         {"吉": 36, "动": 0, "平": 56, "滞": 2, "凶": 20})  # 2026-10-21 发用层(LM-F)入主展示计数(纳音主判: 丙寅/丁卯炉中火财化鬼F04, 庚午路旁土/己巳干土鬼化气F05); 发用不参与吉凶算术(year_power过滤)与大运定基调(净verdict); 2026-10-21: 原局 V85吉-1(日主立极)、V85-B食伤藏支平+1、V31H→V31H-L 凶-1平+1、V14亲缘凶+1、元辰口径修正(阴女冲后=辰)时支午非元辰→V108不触发平-1、羊刃口径修正(蠡海集阴干不立)乙丑运V126平-1 → 净 吉-1 平+0; 2026-10-20 V42比和分流: 癸亥运比和(年命临官太过)吉→凶 → 吉-1凶+1
        self.assertEqual(ts["overall"]["verdict"], "偏吉")
        # 乙丑运偏凶
        yichou = next(p for p in ts["pillars"] if p["target"] == "YICHOU")
        self.assertEqual(yichou["verdict"], "偏凶")
        self.assertIn("LM-V41", yichou["rules"])
        # 每条断语带 tone/scope (五级: 吉/动/平/滞/凶; V44 沐浴/衰/病=滞 L4274)
        for v in lm.verdicts:
            self.assertIn(v["tone"], ("吉", "动", "平", "滞", "凶"))
            self.assertIn(v["scope"], ("原局", "运", "太岁"))
        # V33/V34 动态 tone
        v33 = [v for v in lm.verdicts if v["rule_id"] == "LM-V33"]
        tones33 = {v["tone"] for v in v33}
        self.assertEqual(tones33, {"吉", "平"})   # 生我吉 + 我生平
        v34 = {v["tone"] for v in lm.verdicts if v["rule_id"] == "LM-V34"}
        self.assertEqual(v34, {"平"})       # 2026-10-20 克我(官星乘旺)凶→平

    def test_117_case_19871028_kui_gang(self):
        """第四批 oracle: 1987-10-28 辰时坤造 丁卯 庚戌 庚戌 庚辰.

        排盘: 四柱/纳音(炉中火·钗钏金·钗钏金·白蜡金)/胎元辛丑壁上土/
        大运辛亥→庚申 纳音 与批文全一致.
        魁罡双见(日庚戌+时庚辰) 批文核心; 文昌丁→辰临时支; 六害卯辰;
        自刑辰; 厄会②'禄命无气'按命支卯木败衰病死墓绝六位(子辰巳午未申)
        → 甲寅运(D=YIN∉wq) 不误判凶; 大运纳音逐柱 V42.
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1987, 10, 28, 8), gender="female",
                                     birth_datetime=_dt.datetime(1987, 10, 28, 8, 0))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        d = lm.to_dict()
        # 排盘
        self.assertEqual(d["four_pillars"],
                         [["DING", "MAO"], ["GENG", "XU"], ["GENG", "XU"], ["GENG", "CHEN"]])
        self.assertEqual(d["nayin"]["hour"], "白蜡金")
        self.assertEqual(d["nayin_chain"]["tai_yuan"]["nayin"], "壁上土")
        # 魁罡: 月庚戌+日庚戌+时庚辰 三柱 (批文仅举日时双见, 月柱庚戌同为魁罡日,
        # 三柱魁罡重叠更合 SMTH'魁罡聚众发福非常'/'叠叠相逢掌大权')
        kg = d["shen_sha"]["kui_gang"]
        self.assertEqual(kg["days"], ["月", "日", "时"])
        self.assertTrue(kg["present"])
        # 文昌 (WXJ 年干表 丁→辰) 临时支
        self.assertEqual(d["wen_chang"]["branch"], "CHEN")
        self.assertTrue(d["wen_chang"]["present"])
        # 六害辰害卯 (害方在前, L3421 单向); 无自刑 (原局仅一辰, 自刑须同支重逢 L3399/L3401)
        self.assertEqual(d["liu_hai"], [["CHEN", "MAO"]])
        self.assertEqual(d["san_xing"], [])
        # 大运序列 + 纳音
        self.assertEqual([p[0] + p[1] for p in d["luck_pillars"]][:7],
                         ["XINHAI", "RENZI", "GUICHOU", "JIAYIN", "YIMAO", "BINGCHEN", "DINGSI"])
        pv = {p["stem"] + p["branch"]: p for p in d["luck_scope"]["pillars"]}
        # 大运纳音关系 (火命: 金=我克平 / 木=生我吉 / 水=克我凶 / 土=我生平 / 火=比和吉)
        self.assertEqual(pv["XINHAI"]["nayin_relation"], "我克")
        self.assertEqual(pv["RENZI"]["nayin_relation"], "生我")
        self.assertEqual(pv["JIAYIN"]["nayin_relation"], "克我")
        self.assertEqual(pv["BINGCHEN"]["nayin_relation"], "我生")
        # 甲寅运: 无厄会②误判 (命卯木败衰病死墓绝={子辰巳午未申}, YIN∉)
        v24 = [v for v in lm.verdicts if v["rule_id"] == "LM-V24"]
        self.assertTrue(all("YIN" not in v["detail"] for v in v24))
        # 辛亥运见贵人 (亥=丁年贵人) + 乙卯运将星/卯戌合
        self.assertTrue(pv["XINHAI"]["sees_gui_ren"])
        self.assertTrue(pv["YIMAO"]["sees_jiang_xing"])
        self.assertEqual(pv["YIMAO"]["he_with"], "与XU")
        # 断语含 V42/V43
        rids = {v["rule_id"] for v in lm.verdicts}
        self.assertIn("LM-V42", rids)
        self.assertIn("LM-V43", rids)
        v42_jiayin = next(v for v in lm.verdicts
                          if v["rule_id"] == "LM-V42" and v["target"] == "JIAYIN")
        self.assertEqual(v42_jiayin["tone"], "凶")     # 大溪水克炉中火 → 凶多
        v43 = next(v for v in lm.verdicts if v["rule_id"] == "LM-V43")
        self.assertEqual(v43["tone"], "平")

    def test_118_rule_engine_coverage(self):
        """规则引擎覆盖断言: VERDICT_RULES(45登记) ↔ LUMING_RULES(66条可执行展开)
        ↔ COVERAGE_MATRIX(判定空间) 三方全对齐.

        硬性要求: 每条登记规则至少 1 条可执行规则; 每条可执行规则落在判定矩阵;
        矩阵每格非空; design-out 显式声明; 谓词语法自检; 运行时 verdicts 无幽灵 id.
        """
        from tongshu.luming.facts import VERDICT_RULES
        from tongshu.luming.rules import (LUMING_RULES, COVERAGE_MATRIX,
                                          COVERAGE_DESIGN_OUT)

        def _walk_cond(c):
            self.assertIn("op", c)
            op = c["op"]
            if op in ("eq", "in", "not_empty", "gte", "contains_any"):
                self.assertIn("k", c)
            elif op in ("and", "or"):
                self.assertIn("conds", c)
                for cc in c["conds"]:
                    _walk_cond(cc)
            elif op == "not":
                self.assertIn("cond", c)
                _walk_cond(c["cond"])
            else:
                self.fail(f"未知谓词: {op}")

        v_ids = {r["id"] for r in VERDICT_RULES}
        l_ids = {r["id"] for r in LUMING_RULES}
        # 1) 登记 ↔ 可执行: 双向覆盖 (73 条展开规则, 52 个 id)
        self.assertEqual(v_ids, l_ids)
        self.assertEqual(len(VERDICT_RULES), 161)  # 160 + LM-F01~F06 岁运发用登记(2026-10-21, 引擎直生族)
        self.assertGreaterEqual(len(LUMING_RULES), 45)
        # 2) 每条可执行规则 id 都落在判定矩阵, 且矩阵每格非空
        matrix_ids = set()
        for cell, ids in COVERAGE_MATRIX.items():
            self.assertTrue(ids, f"矩阵空格未显式处理: {cell}")
            matrix_ids.update(ids)
        self.assertEqual(matrix_ids, l_ids)
        # 3) design-out 显式声明
        self.assertTrue(COVERAGE_DESIGN_OUT)
        self.assertTrue(any("小运" in d[0] for d in COVERAGE_DESIGN_OUT))
        # 4) 规则结构合法 (必需字段 + when 谓词语法自检)
        for r in LUMING_RULES:
            for k in ("id", "mode", "scope", "tone", "when", "out", "evidence"):
                self.assertIn(k, r)
            self.assertIn(r["mode"], ("scalar", "per_pillar", "per_list"))
            if r["mode"] == "per_list":
                self.assertIn("list_key", r)
            _walk_cond(r["when"])
        # 5) 运行时: 两案例 verdicts 的 rule_id 全部来自规则表 (无幽灵 id)
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        for args, gender in (((1983, 11, 3, 12), "female"), ((1987, 10, 28, 8), "female")):
            chart = BaziEngine().compute(args, gender=gender,
                                         birth_datetime=_dt.datetime(*args))
            lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
            rids = {v["rule_id"] for v in lm.verdicts}
            self.assertTrue(rids <= l_ids)

    def test_119_conditional_rules_reachable(self):
        """条件性规则可达性验证 (深度审计发现 V29 在固定流年下 0 命中, 须证明可达).

        数学事实: 天乙贵人与干禄十干零交集 → 旧 V05'贵人支=禄支'口径不可达, 已按
        玉霄宝鉴/广录上下文改为'贵人支五行得月令旺相'(V05)/囚死(V07).
        V29 太岁孤寡: 巳午未年生人, 逢辰年(寡宿)必触发 → 定向构造验证.
        V23/V24 喜会/厄会: 依赖小运支(需 birth_datetime), 2106 案例×合成运审计已见命中.
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        # 2026 丙午年生 (午属巳午未组: 孤辰申/寡宿辰), 流年 2024 甲辰 → 太岁=寡宿位
        chart = BaziEngine().compute((2026, 5, 1, 12), gender="male",
                                     birth_datetime=_dt.datetime(2026, 5, 1, 12))
        lm = from_bazi_chart(chart, _dt.datetime(2024, 3, 15, 12))
        v29 = [v for v in lm.verdicts if v["rule_id"] == "LM-V29"]
        self.assertTrue(v29, "巳午未年生人逢辰年(寡宿)应触发 V29")
        self.assertTrue(all(v["tone"] == "凶" for v in v29))
        # 对照: 同一命盘逢不同流年(如 2025 乙巳) 不触发 V29 (条件性)
        lm2 = from_bazi_chart(chart, _dt.datetime(2025, 6, 15, 12))
        v29b = [v for v in lm2.verdicts if v["rule_id"] == "LM-V29"]
        self.assertFalse(v29b, "巳年(午生人不临孤寡)不应触发 V29")

    def test_132_kong_wang_natal_rule(self):
        """原局空亡接线 (五行精纪 L3483 林开五命'论空亡止以年日所在';
        L3484 广集'冲破不为祸反为福; 同类冲最毒')."""
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        # 甲子年 1984-2-10 巳时男: 甲子旬空亡=戌亥, 日支戌临空亡 → LM-V49-KW 平
        chart = BaziEngine().compute((1984, 2, 10, 10), gender="male",
                                     birth_datetime=_dt.datetime(1984, 2, 10, 10))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        kw = [v for v in lm.verdicts if v["rule_id"] == "LM-V49-KW"]
        self.assertTrue(kw, "日支戌在甲子旬空亡(戌亥)应触发")
        self.assertEqual(kw[0]["tone"], "平")

        # 甲戌年 1994-8-8 午时男: 甲戌旬空亡=申酉, 月支申临空亡且被日支寅冲
        #   → LM-V49-KW 平 + LM-V49-KWC 吉 (L3483: 冲破不为祸反为福)
        chart2 = BaziEngine().compute((1994, 8, 8, 12), gender="male",
                                      birth_datetime=_dt.datetime(1994, 8, 8, 12))
        lm2 = from_bazi_chart(chart2, _dt.datetime(2026, 10, 19, 12))
        kws = {v["rule_id"] for v in lm2.verdicts}
        self.assertIn("LM-V49-KW", kws)
        self.assertIn("LM-V49-KWC", kws)
        self.assertNotIn("LM-V49-KTC", kws)   # 申被寅冲, 非同类干支冲(壬申/壬寅同干才同类)

        # 癸亥年 1983-11-3 午时男: 空亡=寅卯辰巳, 四柱亥戌未午无命中 → 不触发
        chart3 = BaziEngine().compute((1983, 11, 3, 12), gender="male",
                                      birth_datetime=_dt.datetime(1983, 11, 3, 12))
        lm3 = from_bazi_chart(chart3, _dt.datetime(2026, 10, 19, 12))
        kw3 = [v for v in lm3.verdicts if v["rule_id"].startswith("LM-V49-KW")]
        self.assertFalse(kw3, "本案例无空亡临支, 不应触发原局空亡")

    def test_133_zang_tou_kong_wang(self):
        """藏头空亡 (五行精纪 L3485 广集: 戊子戊午己丑己未戊申戊寅
        己酉己卯戊辰戊戌己巳己亥 本是祸反为福, 戊己人带之大好)."""
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        # 2008 戊子年: 年柱 WUZI ∈ 藏头名单 → LM-V49-CT 吉
        chart = BaziEngine().compute((2008, 6, 1, 12), gender="male",
                                     birth_datetime=_dt.datetime(2008, 6, 1, 12))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        ct = [v for v in lm.verdicts if v["rule_id"] == "LM-V49-CT"]
        self.assertTrue(ct, "戊子年柱应触发藏头空亡")
        self.assertEqual(ct[0]["tone"], "吉")
        # 反例: 1983 癸亥年 四柱无名单干支 → 不触发
        chart2 = BaziEngine().compute((1983, 11, 3, 12), gender="male",
                                      birth_datetime=_dt.datetime(1983, 11, 3, 12))
        lm2 = from_bazi_chart(chart2, _dt.datetime(2026, 10, 19, 12))
        ct2 = [v for v in lm2.verdicts if v["rule_id"] == "LM-V49-CT"]
        self.assertFalse(ct2)

    def test_134_xu_sheng_sha_and_yuan_chen(self):
        """虚声杀 (L3484: 空亡被日时或运冲刑, 反为虚声杀士人飞声走誉)
        与 元辰犯运 (L3345 阳男阴女冲前一位; L4271 元辰犯运)."""
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        # 1984-2-10 巳时男 甲子: 空亡戌亥(日支戌临); 顺排大运 戊辰支辰冲戌 → 虚声杀
        chart = BaziEngine().compute((1984, 2, 10, 10), gender="male",
                                     birth_datetime=_dt.datetime(1984, 2, 10, 10))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        xs = [v for v in lm.verdicts if v["rule_id"] == "LM-V49-XS"]
        self.assertTrue(any(v["target"] == "WUCHEN" for v in xs), "戊辰运支辰冲戌(空亡)应触发虚声杀")
        self.assertTrue(all(v["tone"] == "吉" for v in xs))
        # 元辰: 甲子阳男 → 冲午前一位=未 (L3348 甲子生男乙未为正); 辛未运支未=元辰 → 犯运凶
        from tongshu.luming.engine import _calc_yuan_chen
        self.assertEqual(_calc_yuan_chen(chart), "WEI")
        yc = [v for v in lm.verdicts if v["rule_id"] == "LM-V49-YC"]
        self.assertTrue(any(v["target"] == "XINWEI" for v in yc), "辛未运支未=元辰应触发元辰犯运")
        self.assertTrue(all(v["tone"] == "凶" for v in yc))
        # 反例: 1983 癸亥男(阴男) 元辰=辰(亥冲巳后一位), 四柱无辰临? 仅验证取值
        chart2 = BaziEngine().compute((1983, 11, 3, 12), gender="male",
                                      birth_datetime=_dt.datetime(1983, 11, 3, 12))
        self.assertEqual(_calc_yuan_chen(chart2), "CHEN")

    def test_120_report_layer_view_only(self):
        """报告层验收: 纯视图 (不新增断语) + 中文化 + 结构与 tone_scope 一致.

        - build_report 全部内容来自 verdicts/tone_scope/to_dict;
        - render_markdown 无英文干支/五行残留;
        - current/overall 与 tone_scope 完全一致 (case1: 丁卯偏吉 / 总体吉25凶20平22).
        """
        import datetime as _dt
        import re
        from tongshu.engines.bazi_engine import BaziEngine
        from tongshu.luming.report import build_report, render_markdown
        chart = BaziEngine().compute((1983, 11, 3, 12), gender="female",
                                     birth_datetime=_dt.datetime(1983, 11, 3, 12))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        rep = build_report(lm)
        md = render_markdown(rep, gender="坤造")
        # 1) 结构字段齐全
        self.assertEqual(len(rep["paiban"]["four"]), 4)
        self.assertTrue(rep["paiban"]["tai_yuan"])
        self.assertTrue(rep["paiban"]["ming_gong"])
        self.assertTrue(rep["paiban"]["shen_gong"])
        self.assertTrue(rep["yuan_ju"])
        self.assertEqual(len(rep["luck"]), len(lm.luck_pillars))
        # 2) 纯视图: 报告断语 = lm.verdicts 全集的子集且不新增 (分组顺序不同, 按集合比)
        rep_verdicts = (
            [(v["tone"], v["out"], v["detail"]) for v in rep["yuan_ju"]]
            + [(v["tone"], v["out"], v["detail"]) for r in rep["luck"] for v in r["verdicts"]]
            + [(v["tone"], v["out"], v["detail"]) for v in rep["er_yun"]]
            + [(v["tone"], v["out"], v["detail"]) for v in rep["tai_sui"]])
        lm_verdicts = [(v["tone"], v["out"], v["detail"]) for v in lm.verdicts]
        self.assertEqual(len(rep_verdicts), len(lm_verdicts))
        self.assertEqual(set(rep_verdicts), set(lm_verdicts))  # 双向覆盖, 无新增无丢失
        # 3) 中文化: markdown 无英文干支/五行 token
        en_left = re.findall(r"(?<![A-Z])(?:JIA|YI|BING|DING|WU|JI|GENG|XIN|REN|GUI|"
                             r"ZI|CHOU|YIN|MAO|CHEN|SI|WEI|SHEN|YOU|XU|HAI|"
                             r"WOOD|FIRE|EARTH|METAL|WATER)(?![A-Z])", md)
        self.assertEqual(en_left, [], f"markdown 残留英文: {en_left[:5]}")
        # 4) 汇总与 tone_scope 一致 (case1 oracle)
        hz = rep["hui_zong"]
        self.assertEqual(hz["current_pillar"], "DINGMAO")
        self.assertEqual(hz["current_verdict"], "偏吉")
        self.assertEqual(hz["current_counts"]["吉"], 5)  # 发用层 F03 贵人入丁卯(2026-10-21)
        self.assertEqual(hz["current_counts"]["凶"], 2)  # V44 死乡 + F04 财化鬼(2026-10-21 纳音口径)
        self.assertEqual(hz["overall_counts"],
                         {"吉": 36, "动": 0, "平": 56, "滞": 2, "凶": 20})  # 2026-10-21 发用层(LM-F)入主展示计数(纳音主判: 庚午/己巳由F04改F05鬼化气); 发用不参与吉凶算术与大运定基调; 原 V85日主立极吉-1、V85-B食伤藏支平+1、V31H→V31H-L凶-1平+1、V14亲缘凶+1、元辰口径修正(阴女冲后=辰)时支午非元辰→V108不触发平-1、羊刃口径修正(阴干不立)乙丑运V126平-1 → 净吉-1平+0; 2026-10-20 限运切片+喜忌覆盖癸亥V42降平+贵人年干口径+V02三元十二宫修正+比和分流吉-1凶+1
        self.assertEqual(hz["overall_verdict"], "偏吉")
        self.assertIn("当前大运: 丁卯", md)
        self.assertIn("总体: 吉 36 · 凶 20 · 平 56 · 滞 2 → 吉", md)  # 2026-10-21 同步 (发用入主计数)

    def test_F04_F05_transformation_oracle(self):
        """岁运发用·五行转化 oracle (渊海子平卷三《论大运》/五行精纪卷33 同文).

        原文: "凡水命四柱有土, 至火运本是财运, 却反为鬼者, 以火生土, 土克水,
                是财化为鬼, 转福成祸. 四柱有金至土运是鬼运, 却反为吉者,
                以土生金, 金生水, 是化鬼为助气, 反祸为福. 五行俱以此为例."
        口径 (2026-10-21 深挖定案, 多维取证补全):
          运侧判定序 = 运纳音 → 运干 → 运支 (先中者定局, 单柱单链,
                防混合柱如庚午(纳音土=鬼, 干支午火=财)双判冲突 — 卷33"皆以生年
                太岁纳音推之"纳音为宗); 柱侧 = 四柱干支 ∪ 四柱纳音
                (渊海"柱中有寅午戌, 或纳音火"互证);
          转化链三段全成立才触发: 运生柱、柱克/生命.
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1983, 11, 3, 12), gender="female",
                                     birth_datetime=_dt.datetime(1983, 11, 3, 12))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        # 运层触发: 丁卯运 纳音炉中火 = 水命之财(我克) → 柱有土(戌未午干支) → 土克水 → F04
        dingmao = next(p for p in lm.tone_scope["pillars"] if p["target"] == "DINGMAO")
        self.assertIn("LM-F04", [x[0] for x in dingmao["counts"]["items"]],
                      "丁卯运(炉中火=财, 柱有土)应触发财化鬼F04")
        # 混合柱纳音主判: 庚午运 纳音路旁土=克水命(鬼) → 柱有金(沙中金) → 金生水 → F05
        #   (旧并集口径判干支午火=财→F04, 现按"以纳音推之"纠正为F05)
        gengwu = next(p for p in lm.tone_scope["pillars"] if p["target"] == "GENGWU")
        self.assertIn("LM-F05", [x[0] for x in gengwu["counts"]["items"]],
                      "庚午运(纳音路旁土=鬼, 柱有金通关)应触发鬼化气F05, 纳音主判压过干支午火=财")
        # 运层反例: 癸亥运 纳音大海水=比和, 非财非鬼 → 无 F04/F05
        guihai = next(p for p in lm.tone_scope["pillars"] if p["target"] == "GUIHAI")
        self.assertFalse([x[0] for x in guihai["counts"]["items"]
                          if x[0] in ("LM-F04", "LM-F05")],
                         "癸亥运比和不应触发五行转化")
        # 太岁触发: 2020 庚子 纳音壁上土 = 克水命(鬼) → 柱有金(沙中金) → 金生水 → F05
        r20 = query_year(chart, 2020, lm=lm)
        self.assertIn("LM-F05", [v["rule_id"] for v in r20["verdicts"]],
                      "庚子(壁上土=鬼, 柱有金通关)应触发鬼化气F05")
        # 2024 甲辰 纳音佛灯火 = 水命之财 → 柱有土 → 土克水 → F04; tone 不受发用扰动仍凶
        r24 = query_year(chart, 2024, lm=lm)
        self.assertIn("LM-F04", [v["rule_id"] for v in r24["verdicts"]],
                      "甲辰(佛灯火=财, 柱有土)应触发财化鬼F04")
        self.assertEqual(r24["tone"], "凶", "2024 元辰重凶, 发用F04不参与算术不扰动tone")

    def test_F04_F05_all_five_elements(self):
        """五行转化全展开 oracle: 五命(木火土金水) × 两链(财化鬼/鬼化气) = 十链.

        "五行俱以此为例" (渊海/五行精纪卷33同文). 手填四柱 (年柱纳音定命五行),
        直调 _build_fayong_verdicts 验证触发; 每命附比和反例(不触发).

        链表 (命M / 财C=我克 / 财化鬼媒介G=运生且克我 / 鬼K=克我 / 鬼化气通关H=运生且生我):
          M=水: C=火(媒介土→克水)  K=土(通关金→生水)   ← 原著原例
          M=木: C=土(媒介金→克木)  K=金(通关水→生木)
          M=火: C=金(媒介水→克火)  K=水(通关木→生火)
          M=土: C=水(媒介木→克土)  K=木(通关火→生土)
          M=金: C=木(媒介火→克金)  K=火(通关土→生金)
        """
        from tongshu.luming.engine import _build_fayong_verdicts
        # (命五行, 年柱干支[纳音定命], 四柱其余三柱(月/日/时), 财化鬼运柱, 鬼化气运柱, 比和反例运柱)
        # 链表 (命M / 财C=我克 / 财化鬼媒介G=C生且克M / 鬼K=克我 / 鬼化气通关H=K生且生M):
        #   M=水: C=火(媒介土→克水)  K=土(通关金→生水)   ← 原著原例
        #   M=木: C=土(媒介金→克木)  K=金(通关水→生木)
        #   M=火: C=金(媒介水→克火)  K=水(通关木→生火)
        #   M=土: C=水(媒介木→克土)  K=木(通关火→生土)
        #   M=金: C=木(媒介火→克金)  K=火(通关土→生金)
        cases = [
            # 水命 癸亥(大海水): 柱含土(庚子壁上土+未戌支)与金(乙未沙中金)
            ("WATER", ("GUI", "HAI"), [("REN", "XU"), ("YI", "WEI"), ("GENG", "ZI")],
             ("DING", "MAO"), ("GENG", "ZI"), ("GUI", "HAI")),
            # 木命 戊辰(大林木): 柱含金(甲子海中金, 媒介)与水(丙子涧下水, 通关)
            ("WOOD", ("WU", "CHEN"), [("JIA", "ZI"), ("BING", "ZI"), ("WU", "XU")],
             ("GENG", "ZI"), ("JIA", "ZI"), ("REN", "WU")),
            # 火命 戊子(霹雳火): 柱含水(丙子涧下水, 媒介)与木(戊辰大林木, 通关)
            ("FIRE", ("WU", "ZI"), [("BING", "ZI"), ("WU", "CHEN"), ("JIA", "YIN")],
             ("GENG", "XU"), ("BING", "ZI"), ("DING", "MAO")),
            # 土命 戊寅(城头土): 柱含木(戊辰大林木, 媒介)与火(丙寅炉中火, 通关)
            ("EARTH", ("WU", "YIN"), [("WU", "CHEN"), ("BING", "YIN"), ("REN", "XU")],
             ("REN", "XU"), ("WU", "CHEN"), ("DING", "SI")),
            # 金命 庚辰(白蜡金): 柱含火(丙午干支火, 媒介)与土(戊寅/辛未, 通关)
            ("METAL", ("GENG", "CHEN"), [("BING", "WU"), ("WU", "YIN"), ("XIN", "WEI")],
             ("WU", "XU"), ("WU", "WU"), ("GENG", "CHEN")),
        ]
        for _el, _y, _others, _f04_gz, _f05_gz, _bie_gz in cases:
            chart = self._mk_gu_chart((_y, _others[0], _others[1], _others[2]))
            self.assertEqual(
                (chart.nayin_five_element or {}).get("year", ""), _el,
                f"{_y[0]}{_y[1]} 年命纳音应属{_el}")
            # 财化鬼链: 运纳音=我克(财) → 命中 F04
            v04 = _build_fayong_verdicts(
                chart, _f04_gz[0], _f04_gz[1], "运", _f04_gz[0] + _f04_gz[1],
                None, None, None)
            self.assertIn("LM-F04", [x["rule_id"] for x in v04],
                          f"{_el}命 运{_f04_gz[0]}{_f04_gz[1]}=财(我克), 柱有媒介→应F04")
            # 鬼化气链: 运纳音=克我(鬼) → 命中 F05
            v05 = _build_fayong_verdicts(
                chart, _f05_gz[0], _f05_gz[1], "运", _f05_gz[0] + _f05_gz[1],
                None, None, None)
            self.assertIn("LM-F05", [x["rule_id"] for x in v05],
                          f"{_el}命 运{_f05_gz[0]}{_f05_gz[1]}=鬼(克我), 柱有通关→应F05")
            # 比和反例: 运纳音=同命五行 且 干支无财无鬼 → 无 F04/F05
            v0 = _build_fayong_verdicts(
                chart, _bie_gz[0], _bie_gz[1], "运", _bie_gz[0] + _bie_gz[1],
                None, None, None)
            self.assertFalse([x["rule_id"] for x in v0
                              if x["rule_id"] in ("LM-F04", "LM-F05")],
                             f"{_el}命 运{_bie_gz[0]}{_bie_gz[1]}=比和→不应触发转化")

    # ============ 根治层: 古籍命例 oracle (独立于案例批文与自裁定) ============
    def _mk_gu_chart(self, yb):
        """手填四柱 BaziChart (不依赖历法/时区), 供古籍命例直接对照."""
        import datetime as _dt
        from tongshu.engines.bazi_engine import (BaziChart, Pillar,
                                                 calc_ming_gong, calc_shen_gong,
                                                 calc_lu, calc_nayin, calc_shensha)
        from tongshu.facts.bazi_facts import NAYIN_FIVE_ELEMENT as _NFE, NAYIN_60
        stems = ["JIA","YI","BING","DING","WU","JI","GENG","XIN","REN","GUI"]
        brs = ["ZI","CHOU","YIN","MAO","CHEN","SI","WU","WEI","SHEN","YOU","XU","HAI"]
        def _n(s, k): return stems[(stems.index(s) + k) % 10]
        def _nb(b, k): return brs[(brs.index(b) + k) % 12]
        y, m, d, h = yb
        chart = BaziChart(
            year_pillar=Pillar(y[0], y[1]), month_pillar=Pillar(m[0], m[1]),
            day_pillar=Pillar(d[0], d[1]), hour_pillar=Pillar(h[0], h[1]),
            day_master=d[0], gender="female", start_age=0.0, luck_pillars=[],
            birth_datetime=_dt.datetime(2000, 1, 1, 12),
            tai_yuan={"stem": _n(m[0], 1), "branch": _nb(m[1], 3), "chinese": "",
                      "nayin": NAYIN_60.get((_n(m[0], 1), _nb(m[1], 3)), ""),
                      "nayin_element": ""})
        for f, v in (("ming_gong", calc_ming_gong(chart)),
                     ("shen_gong", calc_shen_gong(chart)),
                     ("lu", calc_lu(chart)), ("nayin", calc_nayin(chart)),
                     ("shensha", calc_shensha(chart))):
            object.__setattr__(chart, f, v)
        _ny = chart.nayin
        object.__setattr__(chart, "nayin_five_element",
                           {k: _NFE.get(_ny.get(k, ""), "")
                            for k in ("year", "month", "day", "hour")})
        return chart

    def _lm_gu(self, yb):
        import datetime as _dt
        return from_bazi_chart(self._mk_gu_chart(yb), _dt.datetime(2026, 10, 19, 12))

    def test_121_gu_oracle_mingli(self):
        """古籍命例 oracle (六部经典原文实例 → 引擎事实逐条对照).

        独立于案例批文与引擎自裁定, 原文断语为唯一权威:
        L3417 吴二郎 癸未辛酉己酉癸酉 → 三酉自刑 (五十后枯右目丧子)
        L3419 丙午壬辰癸亥丙辰 → 辰辰自刑 (官居殿阁四十三岁临法而终)
        L3406 癸巳戊寅戊寅庚申 → 寅巳申无恩刑 (三刑全掌兵刑之任)
        L2404 甲子金命 → 马在寅 (甲子人马在寅, 又逢禄)
        L3043 己未己巳己未己巳 → 马在巳·禄在午 (己贵在申)
        L3382 庚午乙酉乙酉甲申 → 马在申·禄在申 (庚禄在申, 羊刃在酉)
        L1372 癸酉癸亥庚子辛巳 → 主水厄 (年剑锋金, 月大海水=我生泄)
        L1397 甲子丁丑丁卯辛丑 → 五行全 (海中金/涧下水/炉中火/壁上土/大林木胎)
        L3511 丙午...壬子 → 子午冲 (支干皆冲)
        L2168 壬寅...甲寅 → 壬贵在卯/巳 (昼夜双口径)
        """
        def _sx(lm):
            return [(s["type"], tuple(sorted(s["branches"]))) for s in lm.to_dict()["san_xing"]]
        # 1) 三酉自刑
        lm = self._lm_gu([("GUI","WEI"),("XIN","YOU"),("JI","YOU"),("GUI","YOU")])
        self.assertIn(("自刑", ("YOU",)), _sx(lm))
        # 2) 辰辰自刑
        lm = self._lm_gu([("BING","WU"),("REN","CHEN"),("GUI","HAI"),("BING","CHEN")])
        self.assertIn(("自刑", ("CHEN",)), _sx(lm))
        # 3) 寅巳申无恩刑
        lm = self._lm_gu([("GUI","SI"),("WU","YIN"),("WU","YIN"),("GENG","SHEN")])
        self.assertIn(("无恩刑", ("SHEN","SI","YIN")), _sx(lm))
        # 4) 甲子马在寅
        lm = self._lm_gu([("JIA","ZI"),("BING","YIN"),("XIN","CHOU"),("DING","MAO")])
        self.assertEqual(lm.to_dict()["lu_ma"]["ma"]["branch"], "YIN")
        # 5) 己未马巳禄午
        lm = self._lm_gu([("JI","WEI"),("JI","SI"),("JI","WEI"),("JI","SI")])
        d = lm.to_dict()
        self.assertEqual(d["lu_ma"]["ma"]["branch"], "SI")
        self.assertEqual(d["lu_ma"]["lu"]["lu_branch"], "WU")
        # 6) 庚午马申禄申
        lm = self._lm_gu([("GENG","WU"),("YI","YOU"),("YI","YOU"),("JIA","SHEN")])
        d = lm.to_dict()
        self.assertEqual(d["lu_ma"]["ma"]["branch"], "SHEN")
        self.assertEqual(d["lu_ma"]["lu"]["lu_branch"], "SHEN")
        # 7) 癸酉金命 月大海水=我生 (水厄)
        lm = self._lm_gu([("GUI","YOU"),("GUI","HAI"),("GENG","ZI"),("XIN","SI")])
        nc = lm.to_dict()["nayin_chain"]
        self.assertEqual(nc["year_nayin"], "剑锋金")
        self.assertEqual({p["pos"]: p["relation"] for p in nc["positions"]}["月柱"], "我生")
        # 8) 五行全纳音
        lm = self._lm_gu([("JIA","ZI"),("DING","CHOU"),("DING","MAO"),("XIN","CHOU")])
        nc = lm.to_dict()["nayin_chain"]
        pos = {p["pos"]: p for p in nc["positions"]}
        self.assertEqual(nc["year_nayin"], "海中金")
        self.assertEqual(pos["月柱"]["nayin"], "涧下水")
        self.assertEqual(pos["日柱"]["nayin"], "炉中火")
        self.assertEqual(pos["时柱"]["nayin"], "壁上土")
        self.assertEqual(nc["tai_yuan"]["nayin"], "大林木")
        # 9) 子午冲
        from tongshu.luming.engine import _is_clash
        self.assertTrue(_is_clash("WU", "ZI"))
        # 10) 壬贵人卯/巳 (昼夜双口径, L2168 李虚中卯 vs L2193 昼夜巳)
        lm = self._lm_gu([("REN","YIN"),("JIA","YIN"),("JIA","YIN"),("JIA","YIN")])
        self.assertIn(lm.to_dict()["gui_ren"]["by_year"]["gui_ren_branch"], ("MAO", "SI"))

    def test_131_gu_oracle_direction(self):
        """古籍命例方向 oracle (五行精纪三刑论原文断吉凶 → 引擎 tone 方向).

        2026-10-20 方向对照根因修复后落盘:
        - L3406 癸巳戊寅戊寅庚申: 三刑全+年柱带贵人(巳=癸昼贵), 原文"掌兵刑之任"
          贵格 → V31 分流吉 (麒麟窟"三刑遇昼夜贵人"); 原局凶=0.
        - L3419 丙午壬辰癸亥丙辰: 辰辰自刑无贵人, 原文"四十三岁临法而终"凶
          → 原局偏凶.
        - L3417 吴二郎 癸未辛酉己酉癸酉: 三酉自刑无贵人, 原文"五十后枯右目丧子"
          → V31 tone 凶 (应期灾象断语保留, 不压贵贱总分).
        """
        # 1) 三刑+贵人 → 贵格吉 (麒麟窟分流在 tone_scope 层, verdicts 保留规则原始 tone)
        #    2026-10-20 更新: 本命日时冲(寅申)触发短命杀因子(L4132), 贵格下降级×1;
        #    癸巳水自坐绝(巳)+两土(戊寅戊寅)触发鬼印因子(L2726), 贵格(三刑+贵人掌兵刑之任)
        #    亦降级×1 (L2726"支干有交涉者使官印") → 原局凶=2 (短命1+鬼印1, 均贵格降级)
        lm = self._lm_gu([("GUI","SI"),("WU","YIN"),("WU","YIN"),("GENG","SHEN")])
        v31 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V31" and v.get("scope") == "原局"]
        self.assertEqual(len(v31), 1)
        o = lm.tone_scope["layers"]["原局"]
        self.assertEqual(o["凶"], 3)                       # 2026-10-21: 亲缘 V32原局六害(寅巳害)计入凶+1(原continue不计) → 短命1+鬼印1+六害1; 2026-10-20 注释: 三刑+贵人有气 → 分流为吉; 短命×1+鬼印×1 (贵格降级); V81金0不现不判受亏
        self.assertIn("LM-V31", o["rules"])
        self.assertIn("LM-V31A", o["rules"])               # 日时冲短命因子 (贵格降级)
        self.assertIn("LM-V31C", o["rules"])               # 癸巳绝中逢鬼因子 (贵格降级)
        self.assertTrue(any(v.get("rule_id") == "LM-V05" and v.get("tone") == "吉"
                            for v in lm.verdicts))          # 贵人临命有气 (将相之征)
        # 2) 辰辰自刑 (L3419 官居殿阁临法而终) → 原局贵(吉), 凶终为岁运应期
        #    V31 辰辰自刑非"四字足"(辰午酉亥缺酉) → 平化 (L3419 恒凶需四字足+年月阳日时阴+羊刃);
        #    凶=1 来自 V07 年干贵人亥无气(死)虽有如无
        lm = self._lm_gu([("BING","WU"),("REN","CHEN"),("GUI","HAI"),("BING","CHEN")])
        v31 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V31" and v.get("scope") == "原局"]
        self.assertEqual(len(v31), 1)
        o = lm.tone_scope["layers"]["原局"]
        self.assertEqual(o["凶"], 1)  # V07贵人无气凶×1; V31辰辰自刑平化(非四字足); 短命杀不现
        # 3) 三酉自刑 (L3417 吴二郎 五十后枯右目丧子) → 寿夭/带疾维度凶, 贵贱方向平
        #    V31 三酉自刑非四字足 → 平化; 原局凶=0 (带疾断语映射层呈现)
        lm = self._lm_gu([("GUI","WEI"),("XIN","YOU"),("JI","YOU"),("GUI","YOU")])
        v31 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V31" and v.get("scope") == "原局"]
        self.assertEqual(len(v31), 3)      # 三酉自刑重逢 → 3 条 (count 展开加重)
        o = lm.tone_scope["layers"]["原局"]
        self.assertEqual(o["凶"], 1)   # 2026-10-21: 亲缘 V14华盖孤寡(未=年支华盖坐命)计入凶+1(原continue不计); V31×3 自刑平化(非四字足) → 方向中平
        self.assertFalse(any(v.get("rule_id") == "LM-V05" for v in lm.verdicts))

    def test_132_shensha_lookup_mode_switch(self):
        """神煞查法口径开关 (lookup_mode): 默认年干查 (oracle 基准) vs 日干查 (渊海子平系).

        坤造 甲戌辛未庚子丁亥: 日干庚 → 文昌亥/太极贵寅亥 (批断口径);
        年干甲 → 文昌巳/太极贵子午.
        - year 默认: V74 太极贵子临, V35 文昌不触发, 原局 吉6 凶1
        - day 口径:  V74 太极贵亥临 + V35 日干文昌临亥, 原局 吉7 凶1
        - 非法值报 ValueError
        """
        from tongshu.luming.engine import from_bazi_chart
        chart = self._mk_gu_chart([("JIA","XU"),("XIN","WEI"),("GENG","ZI"),("DING","HAI")])
        import datetime as _dt
        _QT = _dt.datetime(2026, 10, 19, 12)
        # 1) 默认 year: 年干甲太极贵=子午→子临; V35 文昌(甲年=巳, 原局无巳)不触发
        lm = from_bazi_chart(chart, _QT)
        v74 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V74" and v.get("scope") == "原局"]
        self.assertEqual(len(v74), 1)
        self.assertIn("子", v74[0].get("detail", ""))
        self.assertNotIn("日干", v74[0].get("detail", ""))
        self.assertFalse(any(v.get("rule_id") == "LM-V35" for v in lm.verdicts))
        o_year = lm.tone_scope["layers"]["原局"]
        # 2) day 口径: 日干庚太极贵=寅亥→亥临 + V35 日干文昌(庚→亥)触发; 吉数+1 且凶数不变
        lm = from_bazi_chart(chart, _QT, lookup_mode="day")
        v74 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V74" and v.get("scope") == "原局"]
        v35 = [v for v in lm.verdicts if v.get("rule_id") == "LM-V35" and v.get("scope") == "原局"]
        self.assertEqual(len(v74), 1)
        self.assertIn("亥", v74[0].get("detail", ""))
        self.assertIn("日干", v74[0].get("detail", ""))
        self.assertEqual(len(v35), 1)
        self.assertIn("亥", v35[0].get("detail", ""))
        self.assertIn("日干", v35[0].get("detail", ""))
        o_day = lm.tone_scope["layers"]["原局"]
        self.assertEqual(o_day["凶"], o_year["凶"])          # 查法切换不改变凶线
        self.assertEqual(o_day["吉"], o_year["吉"] + 1)      # 仅新增 V35 文昌吉线
        # 3) 非法值
        with self.assertRaises(ValueError):
            from_bazi_chart(chart, _QT, lookup_mode="foo")
        # 4) 默认口径对 oracle 基准不变: 癸亥阴年男 1983 样例文昌仍按年干 (癸→丑)
        lm = self._lm_gu([("GUI","HAI"),("REN","XU"),("YI","WEI"),("REN","WU")])
        self.assertFalse(any(v.get("rule_id") == "LM-V35" for v in lm.verdicts))

    def test_122_fact_layer_orthogonal(self):
        """事实层正交穷举 (数学性质验证, 不依赖任何案例).

        每个事实函数按原文穷举其判定空间, 防止"案例修一次"式补丁:
        - 三刑: 自刑=同支重逢(≥2); 无礼子卯; 无恩寅巳申; 恃势丑戌未
        - 六害单向 (害与被害 12×12 全表)
        - 六合/冲 全表
        - 纳音 60 甲子全表
        - 贵人/文昌/干禄/驿马 表完整性
        """
        from tongshu.facts.bazi_facts import (NAYIN_60, BRANCH_HARM, LU_BY_STEM,
                                              SHEN_SHA_BY_SANHE)
        from tongshu.luming.facts import (SAN_XING_GROUPS, WEN_CHANG_BY_YEAR,
                                          TIAN_YI_GUI_REN_DAY, TIAN_YI_GUI_REN_NIGHT)
        from tongshu.luming.engine import _is_xing, _is_clash
        from tongshu.engines.bazi_engine import HEAVENLY_STEMS, EARTHLY_BRANCHES
        BR = EARTHLY_BRANCHES
        # 1) 三刑两两判定 (12×12 穷举): 只有三种成对刑 + 自刑(同支) 才为刑
        expected_pairs = {frozenset({"ZI","MAO"}), frozenset({"YIN","SI"}), frozenset({"SI","SHEN"}),
                          frozenset({"SHEN","YIN"}), frozenset({"CHOU","XU"}), frozenset({"XU","WEI"}),
                          frozenset({"WEI","CHOU"})}
        for i, b1 in enumerate(BR):
            for b2 in BR:
                if b1 == b2:
                    self.assertEqual(_is_xing(b1, b2), b1 in SAN_XING_GROUPS["自刑"][0],
                                     f"自刑同支 {b1}")
                elif frozenset({b1, b2}) in expected_pairs:
                    self.assertTrue(_is_xing(b1, b2), f"成对刑 {b1}-{b2}")
                else:
                    self.assertFalse(_is_xing(b1, b2), f"误判刑 {b1}-{b2}")
        # 2) 六害全表 (12×12): WXJ L3421-3422 明言单向 —— 未害子/午害丑/巳害寅/
        #    辰害卯/亥害申/戌害酉; "子人见未则为害, 未人见子不为害" (被害方见害方才有害).
        #    bazi 层 BRANCH_HARM 为子平双向表; 禄命层 HARM_DIRECTION 单向化 (害方→被害方).
        from tongshu.luming.engine import HARM_DIRECTION
        self.assertEqual(set(HARM_DIRECTION), {"WEI", "WU", "SI", "CHEN", "HAI", "XU"}, "害方六支")
        self.assertEqual(set(HARM_DIRECTION.values()),
                         {"ZI", "CHOU", "YIN", "MAO", "SHEN", "YOU"}, "被害方六支")
        for k, v in HARM_DIRECTION.items():
            self.assertNotEqual(k, v, "六害无自害")
            self.assertEqual(BRANCH_HARM.get(k), v, "与 bazi 双向表同源")
        # 3) 冲全表: 6 对冲
        for i in range(6):
            self.assertTrue(_is_clash(BR[i], BR[i + 6]))
        self.assertFalse(_is_clash("ZI", "CHOU"))
        # 4) 纳音 60 全表
        self.assertEqual(len(NAYIN_60), 60)
        for i in range(60):
            s = HEAVENLY_STEMS[i % 10]
            b = EARTHLY_BRANCHES[i % 12]
            self.assertIn((s, b), NAYIN_60)
        # 5) 贵人/文昌/干禄/驿马 表完整性
        self.assertEqual(set(TIAN_YI_GUI_REN_DAY), set(TIAN_YI_GUI_REN_NIGHT))
        self.assertEqual(len(TIAN_YI_GUI_REN_DAY), 10)
        self.assertEqual(len(LU_BY_STEM), 10)
        self.assertEqual(len(WEN_CHANG_BY_YEAR), 10)
        for grp in SHEN_SHA_BY_SANHE.values():
            self.assertTrue(grp.get("YI_MA"), f"驿马缺 {grp}")
        # 6) 贵人昼夜表与 WXJ L2193 逐字一致
        self.assertEqual(TIAN_YI_GUI_REN_DAY["JIA"], "CHOU")   # 甲戊庚旦丑
        self.assertEqual(TIAN_YI_GUI_REN_NIGHT["JIA"], "WEI")  # 暮未
        self.assertEqual(TIAN_YI_GUI_REN_DAY["YI"], "ZI")      # 乙己旦子
        self.assertEqual(TIAN_YI_GUI_REN_NIGHT["YI"], "SHEN")  # 暮申
        self.assertEqual(TIAN_YI_GUI_REN_DAY["REN"], "SI")     # 壬癸旦巳
        self.assertEqual(TIAN_YI_GUI_REN_NIGHT["REN"], "MAO")  # 暮卯
        self.assertEqual(TIAN_YI_GUI_REN_DAY["XIN"], "WU")     # 六辛旦午
        self.assertEqual(TIAN_YI_GUI_REN_NIGHT["XIN"], "YIN")  # 暮寅
        # 7) 文昌 WXJ L2010 口诀 (甲蛇乙猪丙狗丁龙戊向猴己午庚寅辛未壬卯癸丑)
        self.assertEqual(WEN_CHANG_BY_YEAR,
                         {"JIA": "SI", "YI": "HAI", "BING": "XU", "DING": "CHEN",
                          "WU": "SHEN", "JI": "WU", "GENG": "YIN", "XIN": "WEI",
                          "REN": "MAO", "GUI": "CHOU"})

    def test_123_minggong_shengong_oracle(self):
        """命宫/身宫 oracle: 六部经典原文算法 + 三命通会原例 (防口径漂移).

        - 五行精纪 L3736 起命宫例: 正月太阳在子, 二月在亥, 一月一移;
          以本生时加太阳顺数见卯为命宫. 身宫=太阴坐宫 (求太阴星约法 L3737-3739).
        - 三命通会 L2679 原例: 甲子年三月(辰月)戌时生 → 命宫丁卯.
        - 验证: 命宫 12 月 × 12 时 全空间不越界, 干支由五虎遁推出.
        """
        def _mg(y_stem, m_br, h_br):
            from tongshu.engines.bazi_engine import BaziChart, Pillar, calc_ming_gong
            chart = BaziChart(
                year_pillar=Pillar(y_stem, "ZI"), month_pillar=Pillar("JIA", m_br),
                day_pillar=Pillar("JIA", "ZI"), hour_pillar=Pillar("JIA", h_br),
                day_master="JIA", gender="male", start_age=0.0, luck_pillars=[])
            return calc_ming_gong(chart)
        # 1) 三命通会原例: 甲子年三月(辰月)戌时 → 丁卯
        g = _mg("JIA", "CHEN", "XU")
        self.assertEqual(g["stem"], "DING")
        self.assertEqual(g["branch"], "MAO")
        # 2) 五行精纪口诀: 正月(寅月)太阳在子 → 寅月子时命宫 = 太阳处+生时(子) = ?
        #    寅月子时: month_count=1, L=0(子), h=0, branch=(0+3)%12=3=卯; 甲年干 → 丁卯
        g2 = _mg("JIA", "YIN", "ZI")
        self.assertEqual((g2["stem"], g2["branch"]), ("DING", "MAO"))
        # 3) 全空间: 12 月 × 12 时 命宫支必为合法地支且干支不越界
        from tongshu.facts.bazi_facts import HEAVENLY_STEMS, EARTHLY_BRANCHES
        for mb in EARTHLY_BRANCHES:
            for hb in EARTHLY_BRANCHES:
                gg = _mg("JIA", mb, hb)
                self.assertIn(gg["stem"], HEAVENLY_STEMS)
                self.assertIn(gg["branch"], EARTHLY_BRANCHES)
                self.assertTrue(gg["chinese"])

    def test_124_shensha_tables_orthogonal(self):
        """神煞表正交穷举 (按原文口诀逐组核对, 数学性质验证).

        - 驿马: 申子辰马在寅/寅午戌马在申/巳酉丑马在亥/亥卯未马在巳 (三命钤 L2404)
        - 华盖: 三合库墓位 (申子辰华盖辰…)
        - 将星: 三合中位 (SMTH L1127)
        - 劫煞: 三合五行长生之绝地 (申子辰水长生申绝巳…)
        - 亡神: 劫煞对冲
        - 桃花: 咸池三合旺地 (寅午戌卯/巳酉丑午/申子辰酉/亥卯未子, WXJ L3524)
        - 孤辰寡宿: 三会方顺数 (亥子丑→寅/戌…)
        - 魁罡: 四魁罡日 (SMTH L2735 庚辰壬辰戊戌庚戌)
        """
        from tongshu.facts.bazi_facts import (SHEN_SHA_BY_SANHE, GU_CHEN_GU_SU_BY_YEAR)
        from tongshu.engines.bazi_engine import (PEACH_BLOSSOM_BY_YEAR,
                                                 HEAVENLY_STEMS, EARTHLY_BRANCHES)
        from tongshu.luming.engine import _is_clash
        # 1) 驿马/华盖/将星/劫煞/亡神 四组逐字核对
        expect = {
            frozenset({"SHEN", "ZI", "CHEN"}): {"YI_MA": "YIN", "HUA_GAI": "CHEN",
                                                "JIANG_XING": "ZI", "JIE_SHA": "SI", "WANG_SHEN": "HAI"},
            frozenset({"YIN", "WU", "XU"}):     {"YI_MA": "SHEN", "HUA_GAI": "XU",
                                                 "JIANG_XING": "WU", "JIE_SHA": "HAI", "WANG_SHEN": "SI"},
            frozenset({"SI", "YOU", "CHOU"}):   {"YI_MA": "HAI", "HUA_GAI": "CHOU",
                                                 "JIANG_XING": "YOU", "JIE_SHA": "YIN", "WANG_SHEN": "SHEN"},
            frozenset({"HAI", "MAO", "WEI"}):   {"YI_MA": "SI", "HUA_GAI": "WEI",
                                                 "JIANG_XING": "MAO", "JIE_SHA": "SHEN", "WANG_SHEN": "YIN"},
        }
        self.assertEqual(SHEN_SHA_BY_SANHE, expect)
        # 2) 亡神 = 劫煞对冲 (数学性质)
        for grp in SHEN_SHA_BY_SANHE.values():
            self.assertTrue(_is_clash(grp["WANG_SHEN"], grp["JIE_SHA"]), f"亡神=劫煞冲 {grp}")
        # 3) 将星 = 三合中位 (SMTH L1127: 申子辰将星子/寅午戌午/巳酉丑酉/亥卯未卯)
        mid_expect = {frozenset({"SHEN", "ZI", "CHEN"}): "ZI",
                      frozenset({"YIN", "WU", "XU"}): "WU",
                      frozenset({"SI", "YOU", "CHOU"}): "YOU",
                      frozenset({"HAI", "MAO", "WEI"}): "MAO"}
        for grp, t in SHEN_SHA_BY_SANHE.items():
            self.assertEqual(t["JIANG_XING"], mid_expect[grp], f"将星=三合中位 {grp}")
        # 4) 桃花 12 支全表
        self.assertEqual(len(PEACH_BLOSSOM_BY_YEAR), 12)
        self.assertEqual(PEACH_BLOSSOM_BY_YEAR,
                         {"YIN": "MAO", "WU": "MAO", "XU": "MAO",
                          "SI": "WU", "YOU": "WU", "CHOU": "WU",
                          "SHEN": "YOU", "ZI": "YOU", "CHEN": "YOU",
                          "HAI": "ZI", "MAO": "ZI", "WEI": "ZI"})
        # 5) 孤辰寡宿 四组逐字核对 (亥子丑→寅戌 寅卯辰→巳丑 巳午未→申辰 申酉戌→亥未)
        self.assertEqual(GU_CHEN_GU_SU_BY_YEAR,
                         {frozenset({"HAI", "ZI", "CHOU"}): ("YIN", "XU"),
                          frozenset({"YIN", "MAO", "CHEN"}): ("SI", "CHOU"),
                          frozenset({"SI", "WU", "WEI"}): ("SHEN", "CHEN"),
                          frozenset({"SHEN", "YOU", "XU"}): ("HAI", "WEI")})
        # 6) 魁罡四日全表
        from tongshu.luming.engine import _build_shen_sha
        from tongshu.engines.bazi_engine import BaziChart, Pillar
        for s, b in (("GENG", "CHEN"), ("REN", "CHEN"), ("WU", "XU"), ("GENG", "XU")):
            ch = BaziChart(year_pillar=Pillar(s, b), month_pillar=Pillar("JIA", "ZI"),
                           day_pillar=Pillar(s, b), hour_pillar=Pillar("JIA", "ZI"),
                           day_master=s, gender="male", start_age=0.0, luck_pillars=[])
            ss = _build_shen_sha(ch)
            self.assertIn("日", ss["kui_gang"]["days"], f"魁罡日 {s}{b}")

    def test_125_suiyun_gu_oracle(self):
        """岁运层古籍命例 oracle (五行精纪原文实例 → 引擎事实逐条对照).

        - L4286 (广信集 大运专例六条): 丁丑→丁未 将凡入圣(比和) / 甲申→丙寅 力停相冲(克我+寅申冲) /
          丙戌→辛卯 钝滞(克我) / 丙子→壬寅 破财(生我) / 戊寅→丁丑 济化(克我) / 庚辰→乙酉 鸳鸯刃(我生)
        - L3671 凶会例: 癸亥人己卯岁运 — 己卯城头土克大海水, 水死于卯 (土克水+十二宫死)
        - L2398: 甲子人驿马在寅, 太岁至亥与寅合 → 迁官得禄 (太岁合马)
        - L4020: 大小二运与岁命六合主有孕 (太岁与原局六合事实)
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import (BaziChart, Pillar,
                                                 calc_lu, calc_nayin, calc_shensha)
        from tongshu.facts.bazi_facts import NAYIN_60, NAYIN_FIVE_ELEMENT as _NFE
        from tongshu.luming.engine import from_bazi_chart, _growth_stage, _he_partner

        def _chart(y, luck):
            chart = BaziChart(
                year_pillar=Pillar(y[0], y[1]), month_pillar=Pillar("JIA", "ZI"),
                day_pillar=Pillar("JIA", "ZI"), hour_pillar=Pillar("JIA", "ZI"),
                day_master="JIA", gender="male", start_age=1.0,
                luck_pillars=[Pillar(*luck)], birth_datetime=_dt.datetime(2000, 1, 1, 12))
            for f, v in (("lu", calc_lu(chart)), ("nayin", calc_nayin(chart)),
                         ("shensha", calc_shensha(chart))):
                object.__setattr__(chart, f, v)
            _ny = chart.nayin
            object.__setattr__(chart, "nayin_five_element",
                               {k: _NFE.get(_ny.get(k, ""), "") for k in ("year", "month", "day", "hour")})
            return chart

        def _luck_view(y, luck, cur):
            return from_bazi_chart(_chart(y, luck), cur).to_dict()["luck_scope"]

        # 1) L4286 六例: 运柱纳音与年命生克关系 (事实层)
        cases = [
            (("DING", "CHOU"), ("DING", "WEI"), "比和", "年柱"),    # 涧下水 见 天河水 + 丑未冲
            (("JIA", "SHEN"), ("BING", "YIN"), "我克", "年柱"),  # 泉中水 见 炉中火(水克火) + 寅申冲
            (("BING", "XU"),  ("XIN", "MAO"), "克我", ""),      # 屋上土 见 松柏木
            (("BING", "ZI"),  ("REN", "YIN"), "生我", ""),      # 涧下水 见 金箔金
            (("WU", "YIN"),   ("DING", "CHOU"), "我克", ""),      # 城头土 见 涧下水(土克水)
            (("GENG", "CHEN"), ("YI", "YOU"), "我生", ""),      # 白蜡金 见 泉中水
        ]
        for y, luck, rel, clash in cases:
            lv = _luck_view(y, luck, _dt.datetime(2026, 10, 19, 12))
            p = lv["pillars"][0]
            self.assertEqual(p["nayin_relation"], rel, f"{y}行{luck}运 纳音生克")
            if clash:
                self.assertEqual(p["clash_with"], clash, f"{y}行{luck}运 冲")
            else:
                self.assertEqual(p["clash_with"], "", f"{y}行{luck}运 无冲")
        # 2) L3671 凶会: 己卯土克大海水 + 水死于卯 (函数级 oracle, 不受公历太岁映射限制)
        self.assertEqual(NAYIN_60[("JI", "MAO")], "城头土")
        self.assertEqual(_NFE.get("城头土"), "EARTH")   # bazi 表五行用英文枚举
        self.assertEqual(_growth_stage("WATER", "MAO"), "死")  # bazi 表五行用英文枚举
        # 3) L2398: 甲子人马在寅, 太岁亥与马寅六合
        self.assertEqual(_he_partner("HAI"), "YIN")
        # 4) L4020: 太岁与原局/运六合事实在 liu_nian 层可见 (见马合)
        lv = _luck_view(("JIA", "ZI"), ("JIA", "ZI"), _dt.datetime(15, 1, 1, 12))
        self.assertEqual(lv["liu_nian"]["branch"], "HAI")          # 公元15年太岁乙亥
        self.assertTrue(lv["liu_nian"]["sees_ma_he"], "太岁亥与甲子人马寅六合 (L2398)")
        # 5) 太岁纳音纲+宫位纲 字段存在且有值 (L3671 消费链)
        lv2 = _luck_view(("GUI", "HAI"), ("JIA", "ZI"), _dt.datetime(2026, 10, 19, 12))
        self.assertTrue(lv2["liu_nian"]["nayin"])
        self.assertTrue(lv2["liu_nian"]["growth"])

    def test_126_pillar_risk_correction(self):
        """大运柱吉凶·局部凶信号优先 (BaziQA 200题方向审计校正, 2026-10-19).

        背景: 运支与原局的六害/三刑 (V40/V41 凶断语) 在净计数中被
        吉信号(贵人/禄/马/华盖/将星/合/纳音生/十二宫旺)淹没,
        "吉期出凶事"系统性反向. 校正: risk 信号单独计入凶方并优先上报.
        oracle 案例 1987-10-28 坤造 (丁卯 庚戌 庚戌 庚辰):
          - 乙卯运: 卯辰六害(日柱) → risk=["六害日柱"], 净计数吉凶相当→偏凶
          - 甲寅运: 寅亥六合(年柱), 与原局无冲/害/刑 → risk=[], verdict 偏吉
          - 乙丑运 (1983-11-3 案例): 丑午害+丑戌未刑+丑未冲 → risk 非空, 仍偏凶
        """
        import datetime as _dt
        from tongshu.engines.bazi_engine import BaziEngine
        from tongshu.luming.engine import from_bazi_chart

        chart = BaziEngine().compute((1987, 10, 28, 8), gender="female",
                                     birth_datetime=_dt.datetime(1987, 10, 28, 8, 0))
        lm = from_bazi_chart(chart, _dt.datetime(2026, 10, 19, 12))
        pv = {p["target"]: p for p in lm.tone_scope["pillars"]}
        # 乙卯运: 卯辰六害 (原局辰在时柱, 辰害卯 → harm_with=时柱) 局部凶信号
        yimao = pv["YIMAO"]
        self.assertIn("六害时柱", yimao["risk"])
        self.assertIn("LM-V40", yimao["rules"])
        # 甲寅运: 寅亥六合(年柱亥) 无冲害刑 → risk 空, 吉信号主导
        jiayin = pv["JIAYIN"]
        self.assertEqual(jiayin["risk"], [])
        self.assertEqual(jiayin["verdict"], "偏吉")

        # 1983-11-3 坤造: 乙丑运 丑午害(时柱)+丑戌未三刑+丑未冲
        chart2 = BaziEngine().compute((1983, 11, 3, 12), gender="female",
                                      birth_datetime=_dt.datetime(1983, 11, 3, 12, 0))
        lm2 = from_bazi_chart(chart2, _dt.datetime(2026, 10, 19, 12))
        pv2 = {p["target"]: p for p in lm2.tone_scope["pillars"]}
        yichou = pv2["YICHOU"]
        self.assertTrue(yichou["risk"])          # 六害/三刑 至少其一
        self.assertEqual(yichou["verdict"], "偏凶")


if __name__ == "__main__":
    unittest.main()
