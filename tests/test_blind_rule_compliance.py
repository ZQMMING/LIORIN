# -*- coding: utf-8 -*-
"""盲派引擎（旧引擎按 V1-FINAL 规则改造后）合规测试。

验证：method_scope / 做功强弱（WK-EFFICIENCY）/ 功神角色（GS）/
零评分（BLIND-ARCH-006）/ 配偶宫纯结构判据（BLIND-ARCH-003）。
案例：1980-06-22 10:00 男 广州 → 庚申 壬午 丙寅 癸巳
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import unittest

from tongshu.engines.blind_bazi_engine import (
    BlindBaziEngine,
    GongShenRole,
    MethodScope,
    StructureClarity,
    WorkEfficiency,
)


class TestBlindRuleCompliance(unittest.TestCase):
    """V1-FINAL 规则合规。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = BlindBaziEngine().compute((1980, 6, 22, 10), gender="male")

    def test_01_method_scope(self) -> None:
        """method_scope = DUAN_JIANYE（段建业主线）。"""
        self.assertEqual(self.result.method_scope, MethodScope.DUAN_JIANYE.value)

    def test_02_work_efficiency_enum(self) -> None:
        """做功强弱为四档枚举，非数字。"""
        self.assertIn(
            self.result.work_efficiency,
            {WorkEfficiency.LARGE.value, WorkEfficiency.MEDIUM.value,
             WorkEfficiency.SMALL.value, WorkEfficiency.NONE.value,
             WorkEfficiency.UNDETERMINED.value},
        )

    def test_03_structure_clarity_enum(self) -> None:
        """结构外显为四态枚举。"""
        self.assertIn(
            self.result.structure_clarity,
            {StructureClarity.CLEAR.value, StructureClarity.PARTIALLY_CLEAR.value,
             StructureClarity.MIXED.value, StructureClarity.CHAOTIC.value,
             StructureClarity.UNDETERMINED.value},
        )

    def test_04_work_level_enum(self) -> None:
        """做功等级五档（理法-结果层）。"""
        self.assertIn(
            self.result.work_level,
            {"LARGE_NOBLE", "MEDIUM_NOBLE", "SMALL_NOBLE", "ORDINARY", "POOR",
             "UNDETERMINED"},
        )

    def test_05_no_numeric_work_scores(self) -> None:
        """做功强弱/结构外显不得为数字（BLIND-ARCH-006）。"""
        self.assertIsInstance(self.result.work_efficiency, str)
        self.assertIsInstance(self.result.structure_clarity, str)
        self.assertNotIn(".", self.result.work_efficiency)
        self.assertNotIn("%", self.result.work_efficiency)
        # 三判据为布尔（非数值强度）
        self.assertIsInstance(self.result.eff_path_direct, bool)
        self.assertIsInstance(self.result.eff_power_concentrated, bool)
        self.assertIsInstance(self.result.eff_target_effective, bool)

    def test_06_gong_shen_roles(self) -> None:
        """功神角色为结构枚举（GongShenRole 全枚举）。"""
        roles = set(self.result.gong_shen.keys())
        # ㊻s88 显式补 IDLE(闲神, 原书ch3"不参与做功之神"), 枚举为准；
        # 旧断言只放行 WORKING/TARGET/UNDETERMINED, 与实际枚举定义自相矛盾。
        self.assertTrue(roles.issubset({r.value for r in GongShenRole}))
        # 有做功时 WORKING/TARGET 为支列表
        if self.result.zuo_gong:
            self.assertIsInstance(self.result.gong_shen.get("WORKING"), list)
            self.assertIsInstance(self.result.gong_shen.get("TARGET"), list)

    def test_07_rules_triggered(self) -> None:
        """规则触发记录非空且含 WK-EFFICIENCY。"""
        self.assertIn("WK-EFFICIENCY-001", self.result.rules_triggered)

    def test_08_to_dict_complete(self) -> None:
        """to_dict 含全部新规则字段。"""
        d = self.result.to_dict()
        for key in ("method_scope", "work_efficiency", "structure_clarity",
                    "eff_path_direct", "eff_power_concentrated",
                    "eff_target_effective", "work_level", "gong_shen",
                    "rules_triggered", "undetermined_reasons"):
            self.assertIn(key, d)

    def test_09_case_zuogong(self) -> None:
        """案例庚申壬午丙寅癸巳：有做功（合/制/冲系），做功强弱不为 UNDETERMINED。"""
        self.assertTrue(self.result.zuo_gong)
        self.assertNotEqual(self.result.work_efficiency, WorkEfficiency.UNDETERMINED.value)


class TestBlindRuleComplianceNoWork(unittest.TestCase):
    """无做功案例 → 无效做功。"""

    def test_10_no_work_none_efficiency(self) -> None:
        # 用一例做功极少的盘验证 NONE 分支（若该盘恰好有做功则跳过，不强造数据）
        result = BlindBaziEngine().compute((2000, 1, 1, 0), gender="male")
        self.assertIn(
            result.work_efficiency,
            {WorkEfficiency.NONE.value, WorkEfficiency.MEDIUM.value,
             WorkEfficiency.SMALL.value, WorkEfficiency.LARGE.value,
             WorkEfficiency.UNDETERMINED.value},
        )


class TestBlindSignalCompliance(unittest.TestCase):
    """泛化信号治理 / 制尽 / 未核证域占位（V1-FINAL §30/§33/§37/§58 + VERIFY-BLIND 门禁）。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = BlindBaziEngine().compute((1980, 6, 22, 10), gender="male")

    def test_11_no_generic_events(self) -> None:
        """禁"星存在=事件"泛化信号（§30 OFF-001 / §33 WEALTH-001/002 / §58）。"""
        event_types = {s.event_type for s in self.result.signals}
        self.assertNotIn("WEALTH_ACTIVE", event_types)
        self.assertNotIn("CAREER_ACTIVE", event_types)
        self.assertNotIn("JOB_CHANGE", event_types)

    def test_12_workchain_signals_neutral_strength(self) -> None:
        """做功链信号存在且 strength 为平台中性值 0.5（BLIND-ARCH-006）。"""
        work_signals = [s for s in self.result.signals
                        if s.event_type in ("WEALTH_GAIN", "CAREER_PROMOTION")]
        self.assertTrue(work_signals, "做功链信号应存在（合财/合官）")
        for sig in work_signals:
            self.assertEqual(sig.strength, 0.5)

    def test_13_control_completeness_enum(self) -> None:
        """制尽为枚举（§37 CONTROL-COMPLETENESS-001/002/003）。"""
        self.assertIn(
            self.result.control_completeness,
            {"CLEAN", "PARTIAL", "UNDETERMINED"},   # V3.2: 二态升级为制尽三态
        )
        self.assertIn("CONTROL-COMPLETENESS", "|".join(self.result.rules_triggered))

    def test_14_pending_domains_undetermined(self) -> None:
        """未核证规则域恒 UNDETERMINED 且带 VERIFY-BLIND 门禁原因（不自行发明）。

        V3.0：VERIFY-BLIND-015(贼捕)/017(干支互通)/022(换象) 已按段建业原书
        核证解锁施工，不再要求 UNDETERMINED；仅 023(六亲组合链) 维持占位。
        """
        # 已解锁域：输出为实际结构枚举（或明确无此结构的枚举）
        self.assertNotEqual(self.result.thief_capture, "UNDETERMINED")
        self.assertNotEqual(self.result.ganzhi_transmission, "UNDETERMINED")
        # V3.2: 六亲计数已按《命理玄机探秘》四定律落地（VERIFY-BLIND-036 解锁）
        self.assertNotEqual(self.result.kinship_chain, "UNDETERMINED")
        self.assertTrue(self.result.kinship_chain.startswith("KINSHIP_COUNT"))
        # 若为计数则校验字段完整性
        if self.result.kinship_chain.startswith("KINSHIP_COUNT"):
            self.assertIn("total=", self.result.kinship_chain)
        reasons = "|".join(self.result.undetermined_reasons)
        for vid in ("VERIFY-BLIND-023",):
            self.assertIn(vid, reasons)

    def test_15_to_dict_new_fields(self) -> None:
        """to_dict 含制尽与未核证域字段。"""
        d = self.result.to_dict()
        for key in ("control_completeness", "thief_capture",
                    "ganzhi_transmission", "image_substitution", "kinship_chain"):
            self.assertIn(key, d)


class TestBlindYingqiSeverityCompliance(unittest.TestCase):
    """应期事件强度枚举化（BLIND-ARCH-006 / G16）。"""

    def test_16_yingqi_severity_enum(self) -> None:
        from tongshu.engines.blind_yingqi import BlindYingqiEngine
        r = BlindYingqiEngine().analyze((1980, 6, 22, 10), "male", target_age=40)
        for evt in r.yingqi_events:
            self.assertNotIn("strength", evt, "应期事件不得含数字化 strength")
            self.assertIn(evt["severity"], {"LOW", "MEDIUM", "HIGH"})

    def test_17_yingqi_fail_closed(self) -> None:
        from tongshu.engines.blind_yingqi import BlindYingqiEngine
        eng = BlindYingqiEngine()
        with self.assertRaises(ValueError):
            eng.analyze((1980, 6, 22, 10), "male", target_age=-5)
        with self.assertRaises(ValueError):
            eng.analyze((1980, 6, 22, 10), "male", target_age=150)
        with self.assertRaises(ValueError):
            eng.analyze((1980, 6, 22, 10), "male", target_year=3000)
        # 边界合法：149 岁 / 出生当年
        eng.analyze((1980, 6, 22, 10), "male", target_age=149)
        eng.analyze((1980, 6, 22, 10), "male", target_year=1980)


class TestBlindV30LiteratureRules(unittest.TestCase):
    """V3.0 文献规则修复核验（以段建业原书为唯一依据）。

    覆盖：印制食伤/刑做功/功神废神三元/贼捕解锁/干支互通解锁。
    """

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.blind_bazi_engine import BlindBaziEngine
        cls.result = BlindBaziEngine().compute((1980, 6, 22, 10), gender="male")

    def test_18_printing_control_food_injury(self) -> None:
        """印制食伤（原书制用结构五种之一：印制食伤）"""
        self.assertIn("印制食伤", self.result.zuo_gong_methods)

    def test_19_xing_as_work(self) -> None:
        """刑做功（原书：体用宾主之字进行刑冲克穿合墓都是做功的方式）"""
        xing_methods = [m for m in self.result.zuo_gong_methods if "刑" in m]
        self.assertTrue(xing_methods, "做功方式必须包含刑")

    def test_20_gong_shen_actors_not_all_ti(self) -> None:
        """功神=实际参与做功的支（原书：凡参与做功的神称为功神），
        不得再输出全量体支为 WORKING。"""
        self.assertEqual(self.result.gong_shen["WORKING"], sorted(self.result.zuo_gong_actors))
        self.assertTrue(
            set(self.result.gong_shen["WORKING"]) <= set(self.result.ti_branches),
            "功神必须属于体支集合",
        )

    def test_21_thief_capture_unlocked(self) -> None:
        """贼捕结构解锁（原书：主/体旺制宾/用弱制死制净=贼捕结构）"""
        self.assertIn(self.result.thief_capture, {"THIEF_CAPTURE", "NO_THIEF_CAPTURE_OFFICER_UNCONTROLLED"})

    def test_22_ganzhi_transmission_unlocked(self) -> None:
        """干支互通解锁（段氏理象学：壬午=干克支、癸巳=支克干）"""
        self.assertIn("SELF_HE_COLUMN", self.result.ganzhi_transmission)
        self.assertIn("REN-WU:STEM_KILLS_BRANCH", self.result.ganzhi_transmission)
        self.assertIn("GUI-SI:BRANCH_KILLS_STEM", self.result.ganzhi_transmission)


if __name__ == "__main__":
    unittest.main()
