"""H8 卦象解析层接入排盘生产链路（2026-10-06）

锁定 guajie 解析层与排盘链路的接通断点。

原状：排盘链路只做到「算卦」——ComputeStage 走 heluo_canonical 直调，
绕过 HeluoAdapter，而 build_guajie_from_result 的唯一生产调用点在 adapter 里
（adapter 仅被 tests/heluo/test_heluo_jingyi.py 使用）。结果：

    HeluoResult.guajie 恒为 None

即 guajie.py 2310 行判词 + guidance / metrics_v2 / diagnosis_rule_graph /
evidence_producer / hexagram_state / frozen_state 合计 4,000+ 行解析层
在真实排盘中**从不执行**。

本测试覆盖：
  1. guajie 已填（四层卦名、判词、证据、扩展断法齐备）
  2. 应期日 / 时辰经 TONGSHUPipeline.run() 透传（接线前 run() 不收这两个参数，
     传即 TypeError）
  3. 农历换算正确（河洛流月流日按农历月与月令「节」对齐，传公历月日会错位一月）
  4. API 出口契约：dataclasses.asdict(HelioResult) 仍可 JSON 序列化且带 guajie
  5. 降级边界：解卦异常只令 guajie=None，**不得**连带清空已算好的河洛结果
  6. 按需单点：单盘只解 1 次，不得对 93 个流年全量跑

桩的只有 iztro（本机缺失，走 stub_with_error）；河洛、解卦、四层时间轴、
pipeline 全部是生产对象。
"""
from __future__ import annotations

import dataclasses
import inspect
import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.heluo import guajie as guajie_mod
from tongshu.pipeline import TONGSHUPipeline
from tongshu.pipeline_stages.compute_stage import ComputeStage

_REPO_ROOT = Path(__file__).resolve().parents[1]

_BIRTH = (1990, 5, 20, 8)
_ANALYSIS = date(2026, 10, 6)
_TARGET = date(2026, 8, 17)  # 农历 2026 年七月初五

# 解卦输出契约快照。改动 guajie 输出结构时此集合会失败，需同步评审。
_GUAJIE_KEYS = {
    "liunian_hexagram", "liunian_year", "liunian_yao", "liunian_ye_buye",
    "liuyue_hexagram", "liuyue_yao",
    "liuri_hexagram", "liuri_yao",
    "liushi_hexagram", "liushi_yao",
    "shu_xiong", "yuan_qi_hit", "hua_gong_hit", "zhengdui_fandui",
    "twelve_xiong", "si_duan", "nayin_yuanqi", "jiehua_gong",
    "benming", "kuozhan", "summary", "evidence",
    # 2026-10-06 接入：参评诗断（K3-447卷十·金锁银匙歌）
    "canping",
}


def _run(pipeline, **kw):
    return pipeline.run(
        analysis_date=_ANALYSIS,
        birth_date=_BIRTH,
        gender="male",
        theme="WORK",
        compute_only=True,
        **kw,
    )


class TestGuajieWiredEndToEnd(unittest.TestCase):
    """核心回归：guajie 不再是 None。接线前本组断言全部失败。"""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        cls.result = _run(cls.pipeline, heluo_target_date=_TARGET)

    def test_guajie_is_populated(self):
        """接线前 HeluoResult.guajie 恒为 None——此处即断点断言。"""
        heluo = self.result.heluo_result
        self.assertIsNotNone(heluo)
        self.assertIsNotNone(heluo.guajie, "H8 解卦层未接通")
        self.assertIsInstance(heluo.guajie, dict)

    def test_guajie_key_contract(self):
        self.assertEqual(set(self.result.heluo_result.guajie), _GUAJIE_KEYS)

    def test_three_layers_resolved_without_hour(self):
        """不传时辰时，流年/流月/流日三层卦名必须齐备。"""
        g = self.result.heluo_result.guajie
        self.assertEqual(g["liunian_year"], 2026)
        self.assertTrue(g["liunian_hexagram"], "流年卦")
        self.assertTrue(g["liuyue_hexagram"], "流月卦")
        self.assertTrue(g["liuri_hexagram"], "流日卦")

    def test_liushi_empty_without_hour(self):
        """不传时辰 → 流时层本就剥离（恒空）。"""
        self.assertEqual(self.result.heluo_result.guajie["liushi_hexagram"], "")

    def test_interpretation_layers_nonempty(self):
        """解析层真的跑出了内容，不是空壳。"""
        g = self.result.heluo_result.guajie
        self.assertGreaterEqual(len(g["summary"]), 1, "断语")
        self.assertGreaterEqual(len(g["evidence"]), 1, "证据链")
        self.assertTrue(g["benming"]["gua_ci"], "本卦判词")
        self.assertTrue(g["kuozhan"], "扩展断法")

    def test_asdict_serializable_and_carries_guajie(self):
        """API 出口契约：api._yi_block 用 asdict(整个 HeluoResult) 序列化，
        guajie 无需改 ComputeResult/PipelineResult 即自动进响应。"""
        payload = dataclasses.asdict(self.result.heluo_result)
        self.assertIn("guajie", payload)
        self.assertIsNotNone(payload["guajie"])
        json.dumps(payload, ensure_ascii=False)  # 不得抛


class TestTargetPassthrough(unittest.TestCase):
    """应期日 / 时辰须能从 TONGSHUPipeline.run() 传进去。

    接线前 ComputeStage.run() 有这两个参数但 pipeline.run() 没有，
    从 pipeline 入口传即 TypeError。
    """

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)

    def test_pipeline_run_accepts_heluo_target_kwargs(self):
        params = inspect.signature(TONGSHUPipeline.run).parameters
        for name in ("heluo_target_date", "heluo_target_hour"):
            self.assertIn(name, params, f"pipeline.run() 未暴露 {name}")

    def test_compute_stage_run_accepts_heluo_target_kwargs(self):
        params = inspect.signature(ComputeStage.run).parameters
        for name in ("heluo_target_date", "heluo_target_hour"):
            self.assertIn(name, params, f"ComputeStage.run() 未暴露 {name}")

    def test_hour_layer_is_stripped(self):
        """2026-10-06 起流时层剥离：不产卦名，且传参必留痕。"""
        r = _run(self.pipeline, heluo_target_date=_TARGET, heluo_target_hour=6)
        gj = r.heluo_result.guajie
        self.assertEqual(gj["liushi_hexagram"], "", "流时层应已剥离")
        self.assertIsNone(gj["liushi_yao"])
        self.assertTrue(any("流时：已剥离" in e for e in gj["evidence"]),
                        "传入时辰必须留痕，不得静默忽略")

    def test_day_layer_unaffected_by_hour_stripping(self):
        """剥离流时不得牵连流日。"""
        a = _run(self.pipeline, heluo_target_date=_TARGET).heluo_result.guajie
        b = _run(self.pipeline, heluo_target_date=_TARGET,
                 heluo_target_hour=6).heluo_result.guajie
        self.assertEqual(a["liuri_hexagram"], b["liuri_hexagram"])
        self.assertEqual(a["liuyue_hexagram"], b["liuyue_hexagram"])

    def test_distinct_target_dates_give_distinct_month_day(self):
        """应期日必须真的参与推演——四个农历月日各异，流月/流日卦应随之变化。

        已知映射（_heluo_lunar_target 口径）：
            2026-08-17 → 农历七月；2026-01-20 → 农历十二月
            2026-05-04 → 农历三月； 2026-11-03 → 农历九月
        """
        seen_month, seen_day = set(), set()
        for d in (date(2026, 8, 17), date(2026, 1, 20),
                  date(2026, 5, 4), date(2026, 11, 3)):
            g = _run(self.pipeline, heluo_target_date=d).heluo_result.guajie
            seen_month.add(g["liuyue_hexagram"])
            seen_day.add(g["liuri_hexagram"])
        self.assertEqual(len(seen_month), 4, f"流月卦未随应期日变化：{seen_month}")
        self.assertEqual(len(seen_day), 4, f"流日卦未随应期日变化：{seen_day}")


class TestLunarTargetConversion(unittest.TestCase):
    """公历应期日 → 河洛口径 (流年公历年, 农历月, 农历日)。

    河洛流月/流日按农历月与月令「节」对齐（canonical._LUNAR_MONTH_JIE 与
    compute_liuri 的 jie_datetime），直接传公历月日会整体错位一个月。
    """

    def test_known_conversions(self):
        cases = [
            (date(2026, 8, 17), (2026, 7, 5)),
            (date(2026, 1, 20), (2026, 12, 2)),
            # 农历年可能早于公历年：2026-02-04 落在农历乙巳年十二月
            (date(2026, 2, 4), (2026, 12, 17)),
        ]
        for src, want in cases:
            with self.subTest(src=src):
                self.assertEqual(ComputeStage._heluo_lunar_target(src), want)

    def test_falls_back_to_solar_on_failure(self):
        """换算失败回退公历口径，不抛。"""
        import lunar_python

        class _Boom:
            @staticmethod
            def fromYmd(*a, **k):
                raise RuntimeError("boom")

        saved = lunar_python.Solar
        lunar_python.Solar = _Boom
        try:
            got = ComputeStage._heluo_lunar_target(date(2026, 8, 17))
        finally:
            lunar_python.Solar = saved
        self.assertEqual(got, (2026, 8, 17), "失败须回退公历月日")


class TestGuajieDegradation(unittest.TestCase):
    """降级边界：解卦炸了，河洛计算结果必须原样留住，guajie 单独降为 None。

    说明：现状下 H8 已自带独立 try，此组锁的是**对外契约**——即便有人日后
    把该 try 合并进外层、或调整赋值顺序，河洛结果也不得被解卦异常带走。
    """

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)

    def test_guajie_failure_keeps_heluo_result(self):
        saved = guajie_mod.build_guajie_from_result

        def _boom(*a, **k):
            raise RuntimeError("解卦炸了")

        guajie_mod.build_guajie_from_result = _boom
        try:
            r = _run(self.pipeline, heluo_target_date=_TARGET)
        finally:
            guajie_mod.build_guajie_from_result = saved

        self.assertIsNotNone(r.heluo_result, "解卦异常不得清空 heluo_result")
        self.assertIsNone(r.heluo_result.guajie, "解卦异常须令 guajie=None")
        self.assertTrue(r.heluo_result.prenatal.hexagram_name, "先天卦仍在")
        self.assertIsNotNone(r.yi_structure, "解卦异常不得清空 yi_structure")
        self.assertIsNotNone(r.yi_interpretation, "解卦异常不得清空 yi_interpretation")

    def test_explicit_none_target_disables_guajie(self):
        """显式关闭开关：target_date=None 时不产 guajie。"""
        stage = self.pipeline.compute_stage
        r = stage._compute_heluo_yi(
            _stub_chart(), "male", year=1990, month=5, day=20, target_date=None,
        )
        heluo = r[0]
        self.assertIsNotNone(heluo)
        self.assertIsNone(heluo.guajie, "target_date=None 时不得解卦")

    def test_no_target_defaults_to_analysis_date(self):
        """不传 heluo_target_* 时应回落 analysis_date 并解出 guajie。"""
        r = _run(self.pipeline)
        self.assertIsNotNone(r.heluo_result.guajie)
        # analysis_date 2026-10-06 → 农历九月十四，与 _TARGET(七月) 的流月卦不同
        by_default = r.heluo_result.guajie["liuyue_hexagram"]
        explicit = _run(self.pipeline, heluo_target_date=_ANALYSIS)
        self.assertEqual(by_default,
                         explicit.heluo_result.guajie["liuyue_hexagram"])


class TestSingleTargetNotFullScan(unittest.TestCase):
    """按需单点：单盘只解 1 次。

    build_guajie_from_result 是 target_* 单目标设计，实测约 1 ms；若对 93 个
    流年全量跑即 +93 ms，会吃掉此前算卦的全部优化收益。
    """

    def test_called_exactly_once_per_chart(self):
        pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        real = guajie_mod.build_guajie_from_result
        calls = []

        def _counting(*a, **k):
            calls.append(k.get("target_year"))
            return real(*a, **k)

        guajie_mod.build_guajie_from_result = _counting
        try:
            _run(pipeline, heluo_target_date=_TARGET, heluo_target_hour=6)
        finally:
            guajie_mod.build_guajie_from_result = real

        self.assertEqual(len(calls), 1, f"单盘解卦 {len(calls)} 次，应为 1 次")
        self.assertEqual(calls[0], 2026)


def _stub_chart():
    """最小 BaziChart 替身，供直接驱动 _compute_heluo_yi。"""
    from tongshu.engines.bazi_engine import Pillar

    y, m, d, h = (Pillar(heavenly_stem=s, earthly_branch=b) for s, b in (
        ("JIA", "WU"), ("XIN", "SI"), ("GENG", "CHEN"), ("REN", "SHEN"),
    ))

    class _Chart:
        year_pillar, month_pillar = y, m
        day_pillar, hour_pillar = d, h

    return _Chart()


if __name__ == "__main__":
    unittest.main()