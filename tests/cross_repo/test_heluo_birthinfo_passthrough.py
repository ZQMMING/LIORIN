"""河洛接入排盘链路的出生信息透传回归（2026-10-06）

锁定 ComputeStage._compute_heluo_yi 的接通断点修复：

原实现调用 HeluoCanonical.calculate() 时**不传 birth_year / birth_date**，
而 calculate() 在二者皆缺时会：
  - _build_timeline 把 birth_year 兜底成 1984 → 大运/流年/流月/流日/流时
    整条四层时间轴跑在**占位年份**上，与真实出生年无关；
  - 跳过 _solar_phase_for_date → 纯卦元堂半年相分支拿不到冬至/夏至判定。

本测试用**桩 BaziChart**（不依赖 sxtwl）直接驱动 _compute_heluo_yi，
断言真实出生年月日确实贯通到 HeluoResult 与四层时间轴。

为何用桩盘：本机无 sxtwl，真实 BaziEngine.compute() 会 fail-closed 抛错。
四柱干支本身不影响本断言——断点修的是出生**日期**的贯通，故直接构造合法 Pillar。
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.bazi_engine import Pillar, BaziChart
from tongshu.pipeline import TONGSHUPipeline

_REPO_ROOT = Path(__file__).resolve().parents[2]
if not (_REPO_ROOT / "backend" / "data").is_dir():
    _REPO_ROOT = Path(__file__).resolve().parents[2]


class _StubChart:
    """最小 BaziChart 替身：只提供 _compute_heluo_yi 实际读取的四柱。"""

    def __init__(self, pillars: list[tuple[str, str]]):
        y, m, d, h = (Pillar(heavenly_stem=s, earthly_branch=b) for s, b in pillars)
        self.year_pillar, self.month_pillar = y, m
        self.day_pillar, self.hour_pillar = d, h


class _StubBaziEngine:
    """桩 BaziEngine：真实 compute() 缺 sxtwl 会 fail-closed 抛错。

    返回**真实 BaziChart**（含 stem_ten_god），使 ComputeStage.run() 后续
    fail-closed 校验（BZ-FNDR-15.2 十神非空）也能通过。
    十神相对日主庚(阳金)：甲偏财／辛劫财／庚比肩／壬食神（纯查表推导）。
    """

    _has_sxtwl = False

    def compute(self, birth, gender="male"):
        y, m, d, h = (Pillar(s, b, stem_ten_god=g) for s, b, g in (
            ("JIA", "WU", "偏财"), ("XIN", "SI", "劫财"),
            ("GENG", "CHEN", "比肩"), ("REN", "SHEN", "食神"),
        ))
        return BaziChart(year_pillar=y, month_pillar=m, day_pillar=d, hour_pillar=h,
                         day_master="GENG", luck_pillars=[], gender=gender)


# 1990-05-20 申时：庚午年 辛巳月 庚辰日 壬申时（干支仅需结构合法）
_CHART = _StubChart([("JIA", "WU"), ("XIN", "SI"), ("GENG", "CHEN"), ("REN", "SHEN")])

# 刻意避开 1984 —— 那是 heluo 侧 birth_year 缺失时的兜底值，
# 用它做断言会因巧合而无法区分「修好了」与「仍在兜底」。
_YEAR, _MONTH, _DAY = 1990, 5, 20


class TestHeluoBirthInfoPassthrough(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        cls.stage = cls.pipeline.compute_stage

    def _run(self, year=_YEAR, month=_MONTH, day=_DAY):
        return self.stage._compute_heluo_yi(_CHART, "male", year=year, month=month, day=day)

    def test_heluo_result_populated(self):
        heluo, yi_structure, yi_interpretation = self._run()
        self.assertIsNotNone(heluo, "河洛结果不应为空")
        self.assertTrue(heluo.prenatal.hexagram_name)
        self.assertTrue(heluo.postnatal.hexagram_name)
        self.assertTrue(heluo.yuantang.yuantang)
        self.assertIsNotNone(yi_structure)
        self.assertIsNotNone(yi_interpretation)
        self.assertEqual(yi_structure.truth_hexagram, heluo.postnatal.hexagram_name)

    def test_birth_date_reaches_heluo_input(self):
        """真实出生日期必须落到 HeluoInput，而非 heluo 侧派生的占位值。"""
        heluo, _, _ = self._run()
        self.assertEqual(heluo.input.birth_date, f"{_YEAR}-{_MONTH:02d}-{_DAY:02d}")

    def test_liunian_years_start_at_real_birth_year(self):
        """四层时间轴的起点必须是真实出生年，不能是 1984 兜底。"""
        heluo, _, _ = self._run()
        yearly = heluo.timeline.yearly_hexagrams
        self.assertTrue(yearly)
        self.assertEqual(yearly[0]["year"], _YEAR,
                         f"流年应起于 {_YEAR}，实得 {yearly[0]['year']}")
        self.assertNotEqual(yearly[0]["year"], 1984, "不得落回 1984 占位")

    def test_liunian_covers_dayun_span_from_real_birth(self):
        """流年数应与该盘大运段长度一致（先天6爻+后天6爻 = 72~108 岁）。"""
        heluo, _, _ = self._run()
        yearly = heluo.timeline.yearly_hexagrams
        dayun = heluo.timeline.qi_phase["dayun"]
        self.assertEqual(len(yearly), dayun[-1]["age_end"])
        self.assertTrue(72 <= len(yearly) <= 108, f"流年数异常：{len(yearly)}")

    def test_month_day_layers_present(self):
        """流月/流日层在真实出生年下应正常产出，且流日带 flip_index。"""
        heluo, _, _ = self._run()
        y0 = heluo.timeline.yearly_hexagrams[0]
        self.assertEqual(len(y0["months"]), 12)
        for m in y0["months"]:
            self.assertEqual(len(m["days"]), 6)
            for d in m["days"]:
                self.assertIn("flip_index", d)
                self.assertNotIn("hours", d, "流时应按需，不得预展开")

    def test_different_birth_years_give_different_timelines(self):
        """两个不同出生年必须产出不同时间轴——若都落 1984 兜底则此断言失败。"""
        a, _, _ = self._run(1990, 5, 20)
        b, _, _ = self._run(1975, 3, 8)
        self.assertEqual(a.timeline.yearly_hexagrams[0]["year"], 1990)
        self.assertEqual(b.timeline.yearly_hexagrams[0]["year"], 1975)
        self.assertNotEqual(a.timeline.yearly_hexagrams[0]["ganzhi"],
                            b.timeline.yearly_hexagrams[0]["ganzhi"])

    def test_missing_birth_info_keeps_legacy_signature(self):
        """旧签名 _compute_heluo_yi(chart, gender) 仍须可用（向后兼容）。"""
        out = self.stage._compute_heluo_yi(_CHART, "male")
        self.assertEqual(len(out), 3)
        heluo, _, _ = out
        self.assertIsNotNone(heluo)
        # 缺出生年时仍走 heluo 侧兜底，不得抛错
        self.assertTrue(heluo.timeline.yearly_hexagrams)

    def test_failure_degrades_to_none(self):
        """河洛失败必须降级为 (None, None, None)，不抛。"""

        class _Broken:
            def calculate(self, **kwargs):
                raise RuntimeError("boom")

        saved = self.stage.heluo_canonical
        self.stage.heluo_canonical = _Broken()
        try:
            self.assertEqual(self._run(), (None, None, None))
        finally:
            self.stage.heluo_canonical = saved


class TestPipelineEndToEnd(unittest.TestCase):
    """端到端：走完整 ComputeStage.run()，验证出生信息在真实排盘链路中贯通。

    桩的只有 BaziEngine（绕开 sxtwl 的 fail-closed），其余全部是生产对象：
    真实 pipeline / 真实 ComputeStage / 真实 HeluoCanonical / 真实 BaziChart。
    """

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        cls.stage = cls.pipeline.compute_stage
        cls._saved_bazi = cls.stage.bazi_engine
        cls.stage.bazi_engine = _StubBaziEngine()
        cls.cr = cls.stage.run(
            analysis_date=date(2026, 8, 17),
            birth_date=(_YEAR, _MONTH, _DAY, 16),
            gender="male", theme="WORK",
            request_id="RR-E2E-0001", trace_id="TRACE-E2E-0001",
        )

    @classmethod
    def tearDownClass(cls):
        cls.stage.bazi_engine = cls._saved_bazi

    def test_heluo_result_carried_by_compute_result(self):
        self.assertIsNotNone(self.cr.heluo_result)
        self.assertTrue(self.cr.heluo_result.prenatal.hexagram_name)
        self.assertTrue(self.cr.heluo_result.postnatal.hexagram_name)
        self.assertIsNotNone(self.cr.yi_structure)
        self.assertIsNotNone(self.cr.yi_interpretation)

    def test_birth_date_is_real_not_1984_placeholder(self):
        """修复前此处恒为 '1984-01-01'（heluo 侧 birth_year 缺失的兜底值）。"""
        self.assertEqual(self.cr.heluo_result.input.birth_date,
                         f"{_YEAR}-{_MONTH:02d}-{_DAY:02d}")
        self.assertNotEqual(self.cr.heluo_result.input.birth_date, "1984-01-01")

    def test_timeline_starts_at_real_birth_year(self):
        yearly = self.cr.heluo_result.timeline.yearly_hexagrams
        self.assertEqual(yearly[0]["year"], _YEAR)
        self.assertEqual(yearly[-1]["year"], _YEAR + len(yearly) - 1)

    def test_four_layers_present(self):
        """排盘产出四层时间序列（先天/后天/99 流年/目标段月日）。

        2026-10-10 批次 P 第二步算力裁剪后：full-path 仍 99 段都嵌 months
        （钉旧契约，见 test_heluo_fastpath.py::TestFastPathDisabled）；
        fast-path 下首段（出生年 1983）无 months（只有目标/上一年 2 段嵌）。
        这里锚的不是单段 months，而是时间轴四层都在——先天/后天/流年骨架
        + **至少一段** 含满 12 月 × 6 日。
        """
        h = self.cr.heluo_result
        self.assertTrue(h.prenatal.hexagram_name, "先天卦")
        self.assertTrue(h.postnatal.hexagram_name, "后天卦")
        self.assertTrue(h.timeline.yearly_hexagrams, "流年")
        # 至少要有一段嵌满 12 流月 × 6 流日（fast-path 下是目标年+上一年，
        # 全量下是任意一段）
        full_segs = [e for e in h.timeline.yearly_hexagrams
                     if e.get("months") and len(e["months"]) == 12
                     and e["months"][0].get("days")
                     and len(e["months"][0]["days"]) == 6]
        self.assertGreaterEqual(len(full_segs), 1,
                                "至少应有一段含满 12 流月 × 6 流日")

    def test_yi_block_serializable(self):
        """排盘输出的 yi 块可 JSON 序列化（API 出口契约）。"""
        import dataclasses
        import json
        block = {
            "heluo": dataclasses.asdict(self.cr.heluo_result),
            "yi_structure": self.cr.yi_structure.to_dict(),
            "yi_interpretation": self.cr.yi_interpretation.to_dict(),
        }
        json.dumps(block)
        self.assertTrue(block["yi_structure"]["truth_hexagram"])
        self.assertEqual(block["yi_structure"]["truth_hexagram"],
                         self.cr.heluo_result.postnatal.hexagram_name)


if __name__ == "__main__":
    unittest.main()
