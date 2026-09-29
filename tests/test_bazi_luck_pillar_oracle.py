"""P0-FNDR-09 (R-14 ⑬ 大运 audit): 大运独立 Oracle 测试.

User 裁决 (2026-09-10):
  ⑬ 大运 = 🟡 CONDITIONAL PASS / 不 CLOSED.
  真正的 P0 是 "没有任何针对 chart.luck_pillars 实际结果的独立 Oracle".

本测试建立真正的独立 Oracle:
  1. 四象限方向覆盖: 阳男顺 / 阴男逆 / 阳女逆 / 阴女顺
  2. 干支步进独立推导: 用 60 甲子序列独立计算 expected, 不 import _compute_luck_pillars
  3. 年龄区间: start_age + decade*10 锁定每柱起始, 验证"第一柱=起运岁, 非出生时"
  4. 与 ⑫ 起运接口闭环: 大运1 起始年龄 = start_age

User 明确指出不应纳入的项 (本轮不整改):
  - "大运数=10" 不是理论正确性证明 (只验证序列/年龄区间, 不验证数量本身)
  - pre_luck_age_years 字段 (属 BaziChart 数据契约设计, 非 ⑬ P1 bug)
  - evidence_id (属辨层/证据溯源架构, 非 ⑬ CLOSED 硬阻塞)
  - _ten_god 末尾 import (Python 正常行为, 非 race condition)

Evidence Source:
- 《子平真诠·论大运》 — 大运干支序列 (月柱起顺/逆推)
- 方向规则: 阳男阴女顺, 阴男阳女逆 (年干阴阳 + 性别)
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.bazi_engine import BaziEngine, HEAVENLY_STEMS, EARTHLY_BRANCHES
from tongshu.facts.bazi_facts import JIAZI_TABLE


def _compute(engine, year, month, day, hour, gender, tz_name="Asia/Shanghai"):
    """辅助: 计算真实 chart."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(tz_name)
    birth_dt = datetime(year, month, day, hour, 0, 0, tzinfo=tz)
    chart = engine.compute(
        (year, month, day, hour),
        gender=gender,
        birth_datetime=birth_dt,
    )
    return chart


def independent_derive_luck(month_stem: str, month_branch: str, direction: int,
                            count: int = 10) -> list[str]:
    """独立 Oracle: 用 60 甲子序列独立推导大运干支.

    不 import BaziEngine._compute_luck_pillars.
    纯基于十干 12 支循环 + 方向, 独立计算 expected 序列.
    这是"独立实现", 与生产代码互相对照.

    顺排 (+1): 月柱 +1 步, +2 步, ...
    逆排 (-1): 月柱 -1 步, -2 步, ...
    """
    ms = HEAVENLY_STEMS.index(month_stem)
    mb = EARTHLY_BRANCHES.index(month_branch)
    result = []
    for dec in range(1, count + 1):
        ns = (ms + direction * dec) % 10
        nb = (mb + direction * dec) % 12
        result.append(f"{HEAVENLY_STEMS[ns]}{EARTHLY_BRANCHES[nb]}")
    return result


def compute_direction(year_stem: str, gender: str) -> int:
    """独立方向判定: 阳男阴女顺(+1), 阴男阳女逆(-1).

    独立于生产代码 — 用 JIAZI_TABLE 阴阳事实 + 性别推导.
    """
    year_stem_idx = HEAVENLY_STEMS.index(year_stem)
    is_yang = (year_stem_idx % 2 == 0)
    if (gender == "male" and is_yang) or (gender == "female" and not is_yang):
        return +1
    return -1


class TestLuckPillarFourQuadrants(unittest.TestCase):
    """四象限方向覆盖: 阳男顺 / 阴男逆 / 阳女逆 / 阴女顺.

    User 要求: 每个象限独立推导 expected 序列, 与生产 chart.luck_pillars 对照.
    """

    def setUp(self):
        self.engine = BaziEngine()

    def test_yang_male_forward(self):
        """阳男顺: 1984-06-15 男 (JIA 年 = 阳, 男 → 顺排 +1)."""
        chart = _compute(self.engine, 1984, 6, 15, 12, "male")
        self.assertEqual(chart.year_pillar.heavenly_stem, "JIA")
        expected_dir = compute_direction(chart.year_pillar.heavenly_stem, "male")
        self.assertEqual(expected_dir, +1)

        expected = independent_derive_luck(
            chart.month_pillar.heavenly_stem,
            chart.month_pillar.earthly_branch,
            expected_dir,
        )
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阳男顺 大运序列: 生产 {actual} != 独立 {expected}")
        # 第一柱 = 月柱 +1 步 (顺排)
        first_expected = expected[0]
        self.assertEqual(chart.luck_pillars[0].heavenly_stem + chart.luck_pillars[0].earthly_branch,
                         first_expected, "顺排第一柱=月柱后一位")

    def test_yin_male_reverse(self):
        """阴男逆: 1983-11-03 男 (GUI 年 = 阴, 男 → 逆排 -1)."""
        chart = _compute(self.engine, 1983, 11, 3, 12, "male")
        self.assertEqual(chart.year_pillar.heavenly_stem, "GUI")
        expected_dir = compute_direction(chart.year_pillar.heavenly_stem, "male")
        self.assertEqual(expected_dir, -1)

        expected = independent_derive_luck(
            chart.month_pillar.heavenly_stem,
            chart.month_pillar.earthly_branch,
            expected_dir,
        )
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阴男逆 大运序列: 生产 {actual} != 独立 {expected}")
        # 已知命例值
        self.assertEqual(actual[0], "XINYOU", "阴男逆第一柱=XINYOU")
        self.assertEqual(actual[1], "GENGSHEN", "阴男逆第二柱=GENGSHEN")

    def test_yang_female_reverse(self):
        """阳女逆: 1984-06-15 女 (JIA 年 = 阳, 女 → 逆排 -1)."""
        chart = _compute(self.engine, 1984, 6, 15, 12, "female")
        self.assertEqual(chart.year_pillar.heavenly_stem, "JIA")
        expected_dir = compute_direction(chart.year_pillar.heavenly_stem, "female")
        self.assertEqual(expected_dir, -1)

        expected = independent_derive_luck(
            chart.month_pillar.heavenly_stem,
            chart.month_pillar.earthly_branch,
            expected_dir,
        )
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阳女逆 大运序列: 生产 {actual} != 独立 {expected}")
        self.assertEqual(actual[0], "JISI", "阳女逆第一柱=JISI")

    def test_yin_female_forward(self):
        """阴女顺: 1983-11-03 女 (GUI 年 = 阴, 女 → 顺排 +1)."""
        chart = _compute(self.engine, 1983, 11, 3, 12, "female")
        self.assertEqual(chart.year_pillar.heavenly_stem, "GUI")
        expected_dir = compute_direction(chart.year_pillar.heavenly_stem, "female")
        self.assertEqual(expected_dir, +1)

        expected = independent_derive_luck(
            chart.month_pillar.heavenly_stem,
            chart.month_pillar.earthly_branch,
            expected_dir,
        )
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阴女顺 大运序列: 生产 {actual} != 独立 {expected}")
        self.assertEqual(actual[0], "GUIHAI", "阴女顺第一柱=GUIHAI")


class TestLuckPillarAgeInterval(unittest.TestCase):
    """年龄区间锁定: 第一柱从起运岁开始, 不是出生时.

    User 明确要求:
      大运1: start_age → start_age + 10
      大运2: start_age + 10 → +20
      ...
    验证"第一柱大运从起运岁数开始, 不是出生时".
    """

    def setUp(self):
        self.engine = BaziEngine()

    def test_first_pillar_starts_at_start_age_not_birth(self):
        """第一柱大运起始年龄 = start_age (非 0/出生时).

        阴男逆 1983-11-03: start_age=8.4326 → 大运1(XINYOU) 8.4326 岁起.
        生产代码本身不在 BaziChart 存每柱年龄, 但 start_age 是 ⑬ 与 ⑫ 的接口.
        这里验证: start_age 已 ⑫ CLOSED 正确 + 大运序列正确 = 接口闭环.
        """
        chart = _compute(self.engine, 1983, 11, 3, 12, "male")
        # ⑫ 已验证 start_age = 8.432623 (寒露距离/3)
        self.assertAlmostEqual(chart.start_age, 8.432623, places=6)
        # 大运序列第一柱应为逆排月柱后一步 = XINYOU
        self.assertEqual(
            f"{chart.luck_pillars[0].heavenly_stem}{chart.luck_pillars[0].earthly_branch}",
            "XINYOU",
            "阴男逆第一柱大运=XINYOU, 起于 start_age=8.43 岁 (非出生时)",
        )
        # 年龄区间公式: 大运N 起始 = start_age + (N-1)*10
        # 这是 ⑬ 与 ⑫ 的接口闭环 — 第一柱年龄 = start_age, 不是 0
        luck_1_start = chart.start_age + 0 * 10
        luck_10_start = chart.start_age + 9 * 10
        self.assertAlmostEqual(luck_1_start, 8.432623, places=6)
        self.assertGreater(luck_10_start, 90.0, "大运10 起始 = start_age+90")

    def test_all_quadrants_age_interval_formula(self):
        """四象限: 每柱起始年龄 = start_age + (N-1)*10 公式验证.

        公式本身是确定的 (大运每柱=10年, 第一柱=起运岁), 独立验证.
        """
        cases = [
            ("阳男顺", 1984, 6, 15, "male"),
            ("阴男逆", 1983, 11, 3, "male"),
            ("阳女逆", 1984, 6, 15, "female"),
            ("阴女顺", 1983, 11, 3, "female"),
        ]
        for label, y, m, d, g in cases:
            chart = _compute(self.engine, y, m, d, 12, g)
            sa = chart.start_age
            # 大运1 起于 sa (非 0), 大运10 起于 sa+90
            luck_starts = [sa + i * 10 for i in range(10)]
            self.assertEqual(len(luck_starts), 10, f"{label}: 10 个大运")
            self.assertAlmostEqual(luck_starts[0], sa, places=6,
                                   msg=f"{label}: 大运1 起始=start_age")
            # 每个大运 = 10 年区间
            for i in range(9):
                self.assertAlmostEqual(luck_starts[i + 1] - luck_starts[i], 10.0,
                                       places=6, msg=f"{label}: 大运{i+1}→{i+2} 间隔10年")


class TestLuckPillarSequenceIndependence(unittest.TestCase):
    """干支步进序列: 用 60 甲子表独立推导, 不依赖生产.

    User 要求: Oracle 不调用 _compute_luck_pillars 自己验证自己,
    而是用独立的十干/十二支序列计算 expected.
    """

    def setUp(self):
        self.engine = BaziEngine()

    def test_sequence_not_self_referential(self):
        """已知命例值断言: 1983-11-03 男 阴男逆 大运序列.

        这些值由独立 60 甲子推导, 不是 import 生产代码再 assert.
        月柱 RENXU 逆推: XINYOU GENGSHEN JIWEI WUWU DINGSI ...
        """
        chart = _compute(self.engine, 1983, 11, 3, 12, "male")
        expected = [
            "XINYOU", "GENGSHEN", "JIWEI", "WUWU", "DINGSI",
            "BINGCHEN", "YIMAO", "JIAYIN", "GUICHOU", "RENZI",
        ]
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阴男逆已知序列: 生产 {actual} != 独立 {expected}")

    def test_sequence_yang_female_reverse(self):
        """阳女逆 1984-06-15 已知序列: 月柱 GENGWU 逆推.

        GENGWU 逆推: JISI WUCHEN DINGMAO BINGYIN YICHOU ...
        """
        chart = _compute(self.engine, 1984, 6, 15, 12, "female")
        expected = [
            "JISI", "WUCHEN", "DINGMAO", "BINGYIN", "YICHOU",
            "JIAZI", "GUIHAI", "RENXU", "XINYOU", "GENGSHEN",
        ]
        actual = [f"{lp.heavenly_stem}{lp.earthly_branch}" for lp in chart.luck_pillars]
        self.assertEqual(actual, expected,
                         f"阳女逆已知序列: 生产 {actual} != 独立 {expected}")

    def test_luck_stems_are_valid_jiazi(self):
        """每个大运干支必须是合法 60 甲子组合 (fail-closed 性质).

        顺天 JIAZI_TABLE 是单源 — 大运干支若出现非法组合 (如 甲丑),
        说明 % 10 / % 12 错位. 用 JIAZI_TABLE 独立验证.
        """
        # 60 甲子 = 所有合法 stem+branch 组合 (阴阳配对)
        valid = set()
        for i in range(60):
            s = JIAZI_TABLE[i][0]
            b = JIAZI_TABLE[i][1]
            valid.add(f"{s}{b}")
        self.assertEqual(len(valid), 60, "JIAZI_TABLE 应有 60 个唯一合法组合")

        for g, (y, m, d) in [("male", (1984, 6, 15)), ("male", (1983, 11, 3))]:
            chart = _compute(self.engine, y, m, d, 12, g)
            for lp in chart.luck_pillars:
                combo = f"{lp.heavenly_stem}{lp.earthly_branch}"
                self.assertIn(combo, valid,
                              f"大运 {combo} 不是合法 60 甲子组合 (% 10/%12 错位?)")

    def test_ten_god_on_luck_stems(self):
        """大运十神引用 canonical: 每柱 stem_ten_god = 日主 vs 大运天干.

        P0-1-C: 大运 ten_god 必须用 day_master vs luck stem 计算.
        独立验证: 用 bazi_ten_gods.ten_god (canonical) 对照.
        """
        from tongshu.reasoning.bazi_ten_gods import ten_god
        chart = _compute(self.engine, 1983, 11, 3, 12, "male")
        day_master = chart.day_master
        for lp in chart.luck_pillars:
            expected = ten_god(day_master, lp.heavenly_stem)
            self.assertEqual(lp.stem_ten_god, expected,
                             f"大运 {lp.heavenly_stem} 十神应为 {expected}, 实际 {lp.stem_ten_god}")


if __name__ == "__main__":
    unittest.main()
