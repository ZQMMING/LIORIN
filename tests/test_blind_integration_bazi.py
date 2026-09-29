# -*- coding: utf-8 -*-
"""盲派引擎接入八字排盘引擎的端到端集成验证。

验证链路：八字排盘引擎 BaziEngine.compute(birth, gender)
        → BaziChart（四柱/日主/干支）
        → 盲派引擎 BlindBaziEngine.compute 消费 chart 全部字段
        → BlindBaziResult（宾主/体用/做功/强弱/功神/制尽/信号）

案例：1980-06-22 10:00 男 广州 → 庚申 壬午 丙寅 癸巳（日主丙）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import unittest

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine

BIRTH = (1980, 6, 22, 10)


def gz(p) -> str:
    return p.heavenly_stem + p.earthly_branch


class TestBlindBaziIntegration(unittest.TestCase):
    """八字排盘 → 盲派引擎 端到端。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.chart = BaziEngine().compute(BIRTH, gender="male")
        cls.blind = BlindBaziEngine().compute(BIRTH, gender="male")

    # ── ① 八字排盘层（消费源）──
    def test_01_four_pillars_from_bazi_engine(self) -> None:
        """八字排盘引擎输出用户案例四柱与日主。"""
        self.assertEqual(gz(self.chart.year_pillar), "GENGSHEN")
        self.assertEqual(gz(self.chart.month_pillar), "RENWU")
        self.assertEqual(gz(self.chart.day_pillar), "BINGYIN")
        self.assertEqual(gz(self.chart.hour_pillar), "GUISI")
        self.assertEqual(self.chart.day_master, "BING")

    # ── ② 盲派层消费一致性 ──
    def test_02_binke_position_registration(self) -> None:
        """主位支 ⊆ {日支,时支}；宾位支 ⊆ {年支,月支}（位置归位，不越位）。"""
        main_pos = {self.chart.day_pillar.earthly_branch,
                    self.chart.hour_pillar.earthly_branch}
        guest_pos = {self.chart.year_pillar.earthly_branch,
                     self.chart.month_pillar.earthly_branch}
        self.assertTrue(self.blind.main_branches <= main_pos)
        self.assertTrue(self.blind.guest_branches <= guest_pos)

    def test_03_ti_yong_consistent_with_hidden_stems(self) -> None:
        """体用支必须来自命局四支（不引入四柱之外的支）。"""
        four_branches = {self.chart.year_pillar.earthly_branch,
                         self.chart.month_pillar.earthly_branch,
                         self.chart.day_pillar.earthly_branch,
                         self.chart.hour_pillar.earthly_branch}
        self.assertTrue(self.blind.ti_branches <= four_branches)
        self.assertTrue(self.blind.yong_branches <= four_branches)

    def test_04_zuogong_methods_from_chart(self) -> None:
        """做功方法非空且可溯源（案例：食伤生财/制杀/比劫制财链）。"""
        self.assertTrue(self.blind.zuo_gong)
        self.assertTrue(self.blind.zuo_gong_methods)
        self.assertIn("食伤生财", self.blind.zuo_gong_methods)

    def test_05_enum_fields_resolved(self) -> None:
        """强弱/结构/等级/制尽/功神 均为枚举且已裁决（非 UNDETERMINED 兜底全空）。"""
        self.assertNotEqual(self.blind.work_efficiency, "UNDETERMINED")
        self.assertIn(self.blind.control_completeness,
                      {"CLEAN", "PARTIAL", "UNDETERMINED"})   # V3.2 制尽三态
        self.assertIn(self.blind.work_level,
                      {"LARGE_NOBLE", "MEDIUM_NOBLE", "SMALL_NOBLE",
                       "ORDINARY", "POOR", "UNDETERMINED"})
        if self.blind.zuo_gong:
            self.assertTrue(self.blind.gong_shen)

    def test_06_workchain_signals_present(self) -> None:
        """做功链信号由命局结构派生（合财→WEALTH_GAIN、合官→CAREER_PROMOTION）。"""
        event_types = {s.event_type for s in self.blind.signals}
        self.assertIn("WEALTH_GAIN", event_types)
        self.assertIn("CAREER_PROMOTION", event_types)
        # 泛化信号不得出现（§30/§33/§58）
        self.assertNotIn("WEALTH_ACTIVE", event_types)
        self.assertNotIn("CAREER_ACTIVE", event_types)
        self.assertNotIn("JOB_CHANGE", event_types)

    def test_07_no_numeric_work_fields(self) -> None:
        """零数字化（BLIND-ARCH-006）：强弱/制尽/等级均为字符串枚举。"""
        for field in ("work_efficiency", "structure_clarity",
                      "work_level", "control_completeness"):
            val = getattr(self.blind, field)
            self.assertIsInstance(val, str)
            self.assertNotIn(".", val)
            self.assertNotIn("%", val)


class TestBlindBaziIntegrationMulti(unittest.TestCase):
    """多日主案例接入回归（不同日主/结构均不崩溃且位置归位正确）。"""

    CASES = [
        ("甲日主", (1985, 10, 15, 14), "female"),
        ("辛日主", (1978, 3, 8, 6), "male"),
        ("壬日主", (1992, 12, 1, 20), "female"),
        ("己日主", (1990, 7, 7, 8), "male"),
    ]

    def test_multi_cases_end_to_end(self) -> None:
        be, bl = BaziEngine(), BlindBaziEngine()
        for name, birth, gender in self.CASES:
            with self.subTest(case=name):
                chart = be.compute(birth, gender=gender)
                blind = bl.compute(birth, gender=gender)
                main_pos = {chart.day_pillar.earthly_branch,
                            chart.hour_pillar.earthly_branch}
                guest_pos = {chart.year_pillar.earthly_branch,
                             chart.month_pillar.earthly_branch}
                self.assertTrue(blind.main_branches <= main_pos, "主位越位")
                self.assertTrue(blind.guest_branches <= guest_pos, "宾位越位")
                self.assertIsInstance(blind.work_efficiency, str)
                self.assertIn(blind.control_completeness,
                              {"CLEAN", "PARTIAL", "UNDETERMINED"})   # V3.2 制尽三态
                # 有做功时信号必须存在
                if blind.zuo_gong:
                    self.assertTrue(blind.signals, "做功案例必须有信号")


if __name__ == "__main__":
    unittest.main()
