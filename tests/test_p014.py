# -*- coding: utf-8 -*-
"""P0-14 tests — Time Policy → Calculation Context → Engine Behavioral → Golden。

覆盖 P0-14 第一阶段新增契约(不动五经/Rule/Mapping/SIR/AI):
  - CalculationContext 冻结 schema(事实层,非政策层)
  - 子正换日 (2026-09-14 裁决, 覆盖 23:00 子初换日): 日界 0:00,
    夜子时 (23:00-23:59:59) 日柱=当天, 时柱按次日日干
  - BaziAdapter 投影转发(bazi_view 不提前换日 → 引擎,禁止重写 bazi_engine)
  - ZiweiAdapter 政策 SPEC_DECISION_PENDING → compute() 拒绝执行
  - Boundary Golden(G6-A..I)runner 11/11 全绿
  - T4 时间链等价性: civil+(lon−ref)×4+EoT ≡ UTC 链(UTC+lon×4+EoT)

Golden 20/20 与 193 既有测试由全量回归另行保证(本文件不触碰公共 pipeline)。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone as dt_timezone
from pathlib import Path

from tongshu.engines.bazi_adapter import BaziAdapter
from tongshu.engines.time_resolver import (
    RESOLVER_VERSION,
    CalculationContext,
    TimeResolver,
)
from tongshu.engines.ziwei_adapter import (
    ZiweiAdapter,
    ZiweiCalculationPolicy,
)
from tongshu.engines.ziwei_engine import ZiweiChart, ZiweiEngine
from tongshu.golden.boundary import run_all

_REPO = Path(__file__).resolve().parents[1]
_RESOLVER = TimeResolver()
_BAZI = BaziAdapter()
_ZIWEI_ENGINE = ZiweiEngine(_REPO / "node_modules")


def _ctx(bd: str, t: str, tz: str, loc: str) -> CalculationContext:
    y, mo, d = map(int, bd.split("-"))
    hh, mm = map(int, t.split(":"))
    return _RESOLVER.resolve_context(
        birth_date=date(y, mo, d), hour=hh, minute=mm,
        timezone=tz, location=loc, timezone_source="location_derived",
    )


class TestCalculationContextSchema(unittest.TestCase):
    def test_frozen_schema_fields_present(self):
        ctx = _ctx("2020-01-02", "00:10", "Asia/Shanghai", "Beijing")
        self.assertIsInstance(ctx.birth_civil_datetime, datetime)
        self.assertEqual(ctx.timezone, "Asia/Shanghai")
        self.assertEqual(ctx.calendar_system, "solar")
        self.assertEqual(ctx.day_boundary_policy, "00:00")
        self.assertEqual(ctx.solar_time_policy, "apparent_solar=True")
        self.assertEqual(ctx.timezone_source, "location_derived")
        self.assertEqual(ctx.resolver_version, RESOLVER_VERSION)
        # 事实层已含 utc/lmst/eot/true_solar/effective/traditional_hour
        for attr in ("utc_instant", "local_mean_solar_datetime", "equation_of_time",
                     "true_solar_datetime", "effective_date", "effective_hour",
                     "effective_minute", "traditional_hour"):
            self.assertTrue(hasattr(ctx, attr), attr)

    def test_night_zi_invariant(self):
        # 子正换日 (2026-09-14): 00:10 北京 → 真太阳时 23:56 (01-01 夜子时)
        # → effective_date=01-01 (不提前换日), day_rolled=True 标记夜子时
        g6 = _ctx("2020-01-02", "00:10", "Asia/Shanghai", "Beijing")
        self.assertEqual(g6.effective_date, date(2020, 1, 1))
        self.assertEqual(g6.effective_hour, 23)
        self.assertTrue(g6.day_rolled)
        self.assertEqual(g6.traditional_hour, "子时(晚)")
        self.assertEqual(tuple(g6.bazi_view), (2020, 1, 1, 23))  # 不提前换日
        # ziwei_view 用 solar date(未换日)→ 01-01 23
        self.assertEqual(tuple(g6.ziwei_view), (2020, 1, 1, 23))

    def test_g3_2300_no_roll(self):
        g3 = _ctx("2020-01-01", "23:00", "Asia/Shanghai", "Beijing")
        # 北京 23:00 → solar 22:42(<23)→ 不换日,仍 01-01
        self.assertEqual(g3.effective_date, date(2020, 1, 1))
        self.assertEqual(g3.effective_hour, 22)
        self.assertFalse(g3.day_rolled)

    def test_early_zi_no_warning_late_zi_warning(self):
        late = _ctx("2020-01-02", "00:10", "Asia/Shanghai", "Beijing")
        self.assertTrue(any("晚子时" in w for w in late.warnings))
        early = _ctx("2020-01-02", "00:30", "Asia/Shanghai", "Beijing")
        self.assertFalse(any("晚子时" in w for w in early.warnings))

    def test_utc_instant_is_absolute(self):
        ctx = _ctx("2020-01-02", "00:10", "Asia/Shanghai", "Beijing")
        self.assertEqual(
            ctx.utc_instant,
            ctx.birth_civil_datetime.astimezone(dt_timezone.utc),
        )


class TestT4ChainEquivalence(unittest.TestCase):
    """civil+(lon−ref)×4+EoT ≡ UTC+lon×4+EoT(wall-clock 读数)。"""

    CASES = [
        ("2020-01-01", "23:17", "Asia/Shanghai", "Beijing"),
        ("2020-01-02", "00:10", "Asia/Shanghai", "Beijing"),
        ("2020-07-15", "23:30", "Europe/Berlin", "Berlin"),
        ("2020-01-15", "23:30", "Europe/Berlin", "Berlin"),
        ("2020-06-15", "12:00", "Asia/Shanghai", "Urumqi"),
        ("2020-01-15", "23:30", "America/New_York", "New York"),
        ("2020-01-01", "23:30", "Asia/Shanghai", "Shanghai"),
    ]

    def test_formula_chain_equals_utc_chain(self):
        """公式链 civil+(lon−ref)×4+EoT ≡ UTC 链 (civil−offset)+lon×4+EoT。

        约定:true_solar_datetime 的 tzinfo 是民用 IANA 帧(仅用于读 .hour/.date),
        不能跨帧相减。因此断言:民用帧的公式链读数 == UTC 帧的 UTC 链读数
        (两条链在同一坐标轴上的「午夜后分钟数」恒等)。
        """
        from tongshu.engines.time_resolver import MIN_PER_DEGREE
        for bd, t, tz, loc in self.CASES:
            ctx = _ctx(bd, t, tz, loc)
            # 公式链(Resolver 实现):civil + (lon−ref)×4 + EoT,民用帧读数
            formula = ctx.true_solar_datetime  # tzinfo = 民用 IANA 帧
            # UTC 链:(civil−offset)+lon×4+EoT,UTC 帧读数
            utc_chain = ctx.utc_instant + timedelta(
                minutes=ctx.longitude * MIN_PER_DEGREE + ctx.equation_of_time)
            u = utc_chain.astimezone(dt_timezone.utc)
            self.assertEqual(
                (formula.year, formula.month, formula.day, formula.hour, formula.minute),
                (u.year, u.month, u.day, u.hour, u.minute),
                f"T4 chain mismatch {loc} {bd} {t}",
            )


class TestBaziAdapter(unittest.TestCase):
    """投影转发:effective(bazi_view)→ 现有 BaziEngine;禁止重写引擎。"""

    def test_night_zi_same_day_pillar(self):
        # 子正换日 (2026-09-14): civil 01-02 00:10 → 真太阳时 23:56 (01-01 夜子时)
        # → 日柱=01-01 癸卯(GUIMAO), 时柱=子时按次日 01-02 (甲日) 五鼠遁 → 甲子(JIAZI)
        chart = _BAZI.compute(_ctx("2020-01-02", "00:10", "Asia/Shanghai", "Beijing"))
        self.assertEqual(_pillar(chart.day_pillar), "GUIMAO")
        self.assertEqual(_pillar(chart.hour_pillar), "JIAZI")

    def test_g3_before_roll(self):
        # civil 01-01 23:00 → solar 22:42 → 同日 亥时 → 癸卯(GUIMAO)癸亥(GUIHAI)
        chart = _BAZI.compute(_ctx("2020-01-01", "23:00", "Asia/Shanghai", "Beijing"))
        self.assertEqual(_pillar(chart.day_pillar), "GUIMAO")
        self.assertEqual(_pillar(chart.hour_pillar), "GUIHAI")

    def test_adapter_holds_real_engine(self):
        self.assertIsNotNone(_BAZI.engine)


class TestZiweiAdapterPolicyRatified(unittest.TestCase):
    """P0-14 已完成，政策已冻结。测试 RATIFIED 状态下的行为。"""

    def test_policy_defaults_ratified(self):
        p = ZiweiCalculationPolicy()
        self.assertFalse(p.is_pending)
        self.assertTrue(p.is_ratified)
        self.assertEqual(p.date_source, "lunar")
        self.assertEqual(p.late_zi_handling, "same_day")
        self.assertEqual(p.ratified_policy_version, "P0-14-v1")
        d = p.to_dict()
        self.assertEqual(d["status"], "RATIFIED")

    def test_adapter_computes_when_ratified(self):
        adapter = ZiweiAdapter(_ZIWEI_ENGINE)
        # 政策已冻结，compute() 应正常工作
        ctx = _ctx("1990-05-15", "10:00", "Asia/Shanghai", "Beijing")
        result = adapter.compute(ctx, gender="male")
        self.assertIsInstance(result, ZiweiChart)
        # 2026-11-10 接线裁决: 默认后端 native（零 node 依赖）；auto 路径 iztro 已安装
        # 走 iztro，未安装按契约 fail-closed（stub 由显式构造产生）
        self.assertIn(result.source, ["native", "iztro", "stub"])

    def test_adapter_policy_is_shared_reference(self):
        policy = ZiweiCalculationPolicy()
        adapter = ZiweiAdapter(_ZIWEI_ENGINE, policy=policy)
        self.assertIs(adapter.policy, policy)



class TestBoundaryGolden(unittest.TestCase):
    """P0-14 Boundary Golden(G6-A..I):时间链端到端回归 11/11。"""

    def test_all_boundary_cases_pass(self):
        results = run_all()
        self.assertEqual(len(results), 11)
        failures = [r for r in results if not r.passed]
        msgs = [f"{r.case_id}: {r.failures}" for r in failures]
        self.assertEqual(failures, [], f"boundary golden failures:\n" + "\n".join(msgs))


def _pillar(p) -> str:
    return f"{p.heavenly_stem}{p.earthly_branch}"


if __name__ == "__main__":
    unittest.main()
