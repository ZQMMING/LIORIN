# -*- coding: utf-8 -*-
"""BZ-BLIND-001 盲派引擎接入主链集成测试。

验证：
- blind_school_adapter 字段映射修正后：BlindBaziResult → FeatureMapResult 真映射（resolved>0）
- ComputeStage.run() 真实调用盲派引擎，blind_result 进入 ComputeResult 最终输出
- 盲派消费主链 BaziChart（compute_from_chart S0 契约，禁止重排盘）
- 盲派失败降级为 None，不中断既有主链路（bazi/ziwei/huangli/heluo）
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import unittest

from tongshu.canonical.composer import CanonicalComposer
from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine
from tongshu.feature_registry import FeatureRegistry
from tongshu.feature_registry.adapters.blind_school_adapter import BlindSchoolFeatureAdapter
from tongshu.pipeline import TONGSHUPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]  # D:\\shuntian


def _make_stage(pipeline):
    stage = pipeline.compute_stage
    stage.composer = CanonicalComposer(
        theme="WORK",
        engine_versions={
            "bazi": "1.0.0",
            "ziwei": "1.0.0",
            "rules": "1.0.0",
            "reasoning": "1.0.0",
        },
    )
    return stage


class TestBlindAdapterMapping(unittest.TestCase):
    """修正后的 adapter：BlindBaziResult 真实字段映射。"""

    @classmethod
    def setUpClass(cls):
        cls.chart = BaziEngine().compute((1980, 6, 22, 10), gender="male")
        cls.blind = BlindBaziEngine(bazi_engine=BaziEngine()).compute_from_chart(
            cls.chart, gender="male"
        )

    def test_mapped_features_resolved(self):
        """9 个 feature 定义中 7 个可映射字段全部 resolved（GRAVE/TIMING 保留定义不映射）。"""
        result = BlindSchoolFeatureAdapter(FeatureRegistry()).adapt(self.blind)
        self.assertEqual(result.engine, "BLIND_SCHOOL")
        self.assertEqual(result.total_evidence, 7)
        self.assertEqual(result.resolved, 7)
        self.assertEqual(result.unmapped, 0)
        self.assertGreater(result.coverage_rate, 0)

    def test_body_use_guest_host_values(self):
        """体/用/宾/主 映射到 ti/yong/guest/main_branches（引擎字段为 set，adapter 消费 to_dict 的 list）。"""
        result = BlindSchoolFeatureAdapter(FeatureRegistry()).adapt(self.blind)
        fmap = {f.feature_id: f.value for f in result.resolved_features}
        self.assertEqual(set(fmap["BLIND.BODY"]), self.blind.ti_branches)
        self.assertEqual(set(fmap["BLIND.USE"]), self.blind.yong_branches)
        self.assertEqual(set(fmap["BLIND.GUEST"]), self.blind.guest_branches)
        self.assertEqual(set(fmap["BLIND.HOST"]), self.blind.main_branches)

    def test_doing_work_palace_ten_god_values(self):
        """做功链/宫位数据/十神落宫 映射到真实字段。"""
        result = BlindSchoolFeatureAdapter(FeatureRegistry()).adapt(self.blind)
        fmap = {f.feature_id: f.value for f in result.resolved_features}
        self.assertEqual(fmap["BLIND.DOING_WORK"], self.blind.zuo_gong_methods)
        self.assertEqual(fmap["BLIND.PALACE_DATA"], self.blind.to_dict()["space_palace"])
        self.assertEqual(
            fmap["BLIND.TEN_GOD_PALACE"], self.blind.transparent_ten_gods
        )


class TestBlindMainchain(unittest.TestCase):
    """ComputeStage.run() 真实调用盲派引擎，结果进入 ComputeResult。"""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        cls.stage = _make_stage(cls.pipeline)

    def _run(self):
        return self.stage.run(
            analysis_date=date(2026, 10, 18),
            birth_date=(1980, 6, 22, 10),
            gender="male",
            theme="WORK",
            request_id="RR-TEST-BLIND-0001",
            trace_id="TRACE-TEST-BLIND-0001",
        )

    def test_blind_result_populated(self):
        cr = self._run()
        self.assertIsNotNone(cr.blind_result)
        self.assertEqual(cr.blind_result.engine, "BLIND_SCHOOL")
        self.assertGreater(cr.blind_result.resolved, 0)

    def test_mainchain_not_broken(self):
        """既有引擎结果不因盲派接入而破坏。"""
        cr = self._run()
        self.assertIsNotNone(cr.bazi_chart)
        self.assertIsNotNone(cr.ziwei_chart)
        self.assertIsNotNone(cr.huangli_day)


class TestBlindDegradation(unittest.TestCase):
    """盲派失败降级为 None，不中断主链路。"""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = TONGSHUPipeline.for_demo(_REPO_ROOT)
        cls.stage = _make_stage(cls.pipeline)

    def test_blind_failure_degrades_gracefully(self):
        original = self.stage._blind_engine

        class _BrokenBlind:
            def compute_from_chart(self, *args, **kwargs):
                raise RuntimeError("boom")

        self.stage._blind_engine = _BrokenBlind()
        try:
            cr = self.stage.run(
                analysis_date=date(2026, 10, 18),
                birth_date=(1980, 6, 22, 10),
                gender="male",
                theme="WORK",
                request_id="RR-TEST-BLIND-0002",
                trace_id="TRACE-TEST-BLIND-0002",
            )
            self.assertIsNone(cr.blind_result)
            # 主链路结果必须仍在（不因盲派失败而崩溃）
            self.assertIsNotNone(cr.bazi_chart)
            self.assertIsNotNone(cr.huangli_day)
        finally:
            self.stage._blind_engine = original


if __name__ == "__main__":
    unittest.main()
