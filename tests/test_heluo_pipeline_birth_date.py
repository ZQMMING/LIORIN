"""河洛主链路出生日期传递回归（2026-11-11）。

修复：ComputeStage._compute_heluo_yi 此前直调 HeluoCanonical.calculate() 时
漏传 birth_date / birth_year / era，导致 canonical 内部用 1984-01-01 占位，
影响依赖出生日期的化工/节候/流年结果。本测试锁定：出生 1980-06-22 的盘，
heluo_result.input.birth_date 必须为真实日期 1980-06-22，而非占位 1984-01-01。

相关：
- src/tongshu/pipeline_stages/compute_stage.py::_compute_heluo_yi
- src/tongshu/engines/heluo/canonical.py::HeluoCanonical.calculate
- src/tongshu/engines/heluo_adapter.py（正确口径的对照实现）
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")


class TestHeluoPipelineBirthDate(unittest.TestCase):
    """主链路河洛计算必须传递真实出生日期，不得回落 1984-01-01 占位。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.pipeline import TONGSHUPipeline
        cls.pipeline = TONGSHUPipeline.for_demo(Path(__file__).resolve().parents[1])

    def test_pipeline_heluo_uses_real_birth_date(self):
        # 1980-06-22：若漏传出生日期会得到占位 1984-01-01。
        result = self.pipeline.run(
            analysis_date=date(2026, 8, 17),
            birth_date=(1980, 6, 22, 12),
            gender="male",
            theme="WORK",
            compute_only=True,
        )
        self.assertIsNotNone(result.heluo_result, "河洛主链不应降级为 None")
        got = result.heluo_result.input.birth_date
        self.assertEqual(got, "1980-06-22",
                         f"出生日期应透传真实值 1980-06-22，实际 {got!r}（占位 bug 回归）")

    def test_pipeline_heluo_era_derived_from_birth_year(self):
        # era 不再硬编码 zhong：1984 年落入下元（(1984-1864)%180=120 >= 120 → xia）。
        # 用 1984 出生验证主链 era 由 sanyuan(birth_year) 推导，而非固定 zhong。
        from tongshu.engines.heluo_adapter import sanyuan
        self.assertEqual(sanyuan(1984), "xia")
        result = self.pipeline.run(
            analysis_date=date(2026, 8, 17),
            birth_date=(1984, 12, 7, 16),
            gender="male",
            theme="WORK",
            compute_only=True,
        )
        self.assertIsNotNone(result.heluo_result)
        self.assertEqual(result.heluo_result.input.birth_date, "1984-12-07",
                         "era 推导的同时出生日期必须透传真实值")

    def test_heluo_adapter_reference_path_agrees(self):
        """适配器路径与主链路径对同一出生日期应产出相同的 input.birth_date。"""
        from tongshu.engines.bazi_engine import BaziEngine
        from tongshu.engines.bazi_adapter import BaziAdapter
        from tongshu.engines.time.resolver import TimeResolver
        from tongshu.engines.heluo_adapter import HeluoAdapter

        ctx = TimeResolver().resolve_context(
            birth_date=date(1980, 6, 22), hour=12, minute=30,
            timezone="Asia/Shanghai", location="北京", gender="male",
        )
        chart = BaziAdapter(BaziEngine()).compute(ctx, gender="male")
        adapter_result = HeluoAdapter().compute_from_chart(chart)
        self.assertEqual(adapter_result.input.birth_date, "1980-06-22")


class TestHeluoMissingBirthDateFailClosed(unittest.TestCase):
    """缺失出生日期时，占位日期不得冒充真实出生日期（2026-11-11 fail-closed）。"""

    def test_no_birth_date_does_not_fabricate_placeholder(self):
        """只传 birth_year 不传 birth_date 时，input.birth_date 应为空串，而非伪造 {year}-01-01。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        bazi = [("庚", "申"), ("壬", "午"), ("丙", "寅"), ("癸", "巳")]
        r = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="巳", era="zhong", birth_year=1980,
        )
        self.assertEqual(r.input.birth_date, "",
                         "缺失出生日期时不得伪造 '1980-01-01' 等占位日期")
        self.assertEqual(r.input.true_solar_datetime, "",
                         "缺失出生日期时 true_solar_datetime 也应标记缺失")

    def test_no_birth_date_seasonal_hexagram_is_none(self):
        """缺失出生日期时节候卦须 fail-closed 为 None，不得用占位日期查节气。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        bazi = [("庚", "申"), ("壬", "午"), ("丙", "寅"), ("癸", "巳")]
        r = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="巳", era="zhong", birth_year=1980,
        )
        self.assertIsNone(r.seasonal_hexagram,
                          "缺失出生日期时节候卦不得用占位日期冒充真实出生日")

    def test_no_birth_year_and_no_birth_date(self):
        """完全无出生信息时同样不伪造 1984-01-01。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        bazi = [("庚", "申"), ("壬", "午"), ("丙", "寅"), ("癸", "巳")]
        r = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="巳", era="zhong",
        )
        self.assertEqual(r.input.birth_date, "",
                         "完全无出生信息时不得伪造 '1984-01-01' 占位")
        self.assertIsNone(r.seasonal_hexagram)


class TestHeluoBirthYearFromPillar(unittest.TestCase):
    """出生年份缺失时从年柱干支反推（60 甲子），不得用 1984 占位错位流年干支。"""

    def test_pillar_reverse_matches_truth(self):
        """庚申 → 1980（truth case heluo-002 的真实出生年）。"""
        from tongshu.engines.heluo.canonical import _birth_year_from_pillar
        self.assertEqual(_birth_year_from_pillar("庚", "申"), 1980)
        self.assertEqual(_birth_year_from_pillar("壬", "子"), 1972)
        self.assertEqual(_birth_year_from_pillar("甲", "子"), 1924)
        self.assertEqual(_birth_year_from_pillar("癸", "亥"), 1983)

    def test_pillar_reverse_roundtrip(self):
        """反推值的干支阴阳与年柱一致。"""
        from tongshu.engines.heluo.canonical import _birth_year_from_pillar
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        for g, b in [("庚", "申"), ("壬", "子"), ("乙", "未"), ("丙", "寅")]:
            y = _birth_year_from_pillar(g, b)
            self.assertIsNotNone(y)
            self.assertEqual(stems[(y - 4) % 10], g)
            self.assertEqual(branches[(y - 4) % 12], b)

    def test_no_birth_year_uses_pillar_for_liunian(self):
        """不传 birth_year 时，流年卦从年柱反推出生年，而非 1984 占位。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        # 庚申年出生（1980），不传 birth_year
        bazi = [("庚", "申"), ("壬", "午"), ("丙", "寅"), ("癸", "巳")]
        r = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="巳", era="zhong",
        )
        self.assertIsNotNone(r.timeline, "流年卦不应因缺失出生年份而降级")
        years = r.timeline.yearly_hexagrams
        self.assertTrue(len(years) > 0, "应从年柱反推出生年并推流年卦")
        # 第一个流年（虚岁1）干支应为「庚申」（真实出生年 1980），而非「甲子」（1984 占位）
        self.assertEqual(years[0]["ganzhi"], "庚申",
                         "缺失出生年份时流年干支应从年柱反推，而非 1984 占位")

    def test_invalid_pillar_returns_none(self):
        """非法干支 fail-closed 返回 None。"""
        from tongshu.engines.heluo.canonical import _birth_year_from_pillar
        self.assertIsNone(_birth_year_from_pillar("X", "申"))
        self.assertIsNone(_birth_year_from_pillar("庚", "X"))


if __name__ == "__main__":
    unittest.main()
