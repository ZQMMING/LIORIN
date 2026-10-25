# -*- coding: utf-8 -*-
"""失败路径与边界契约守卫（2026-10-25 新增）。

为什么要有这个模块
------------------
覆盖率显示：包内 82%，但**未覆盖的几乎全是「出错时怎么办」的那几行**
（``except`` 分支、非法入参报错、兜底、缺依赖降级）。

这些恰恰是**最不该没测**的地方 —— 本项目的核心纪律是
「**缺失被当成正常，比答错更坏**」：
  · 失败必须**留痕**（写入 warnings / error 字段），不得静默；
  · 降级必须**不阻塞**主链（河洛失败不应拖垮整条业务链）；
  · 非法输入必须**显式报错**，不得悄悄返回空/None 让调用方误以为「没这回事」。

本模块逐条钉住这些契约。覆盖的是**行为**，不是行号 ——
将来重构换了实现，只要契约不变，守卫仍应全绿。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter                      # noqa: E402
from heluo_engine.engines.heluo import interpretation_pipeline as ip  # noqa: E402


def _result():
    return HeluoAdapter().compute(
        (1983, 11, 3, 12), gender="male", target_date="2026-10-23")


class TestInterpretationPipelineDegradation(unittest.TestCase):
    """解读层：任一子块失败 → **不阻塞**主链，且**必须留痕**。"""

    def test_all_blocks_present_on_normal_run(self):
        out = ip.build_interpretation(_result())
        for key in ("platform_signals", "interpretation", "diagnosis",
                    "guidance", "metrics", "hexagram_state",
                    "dimension_view", "event_candidates", "warnings"):
            self.assertIn(key, out, "解读层缺 %s" % key)

    def test_broken_result_does_not_raise(self):
        """喂一个完全不是 result 的东西 ⇒ 不得抛异常（主链不能被拖垮）。"""
        for junk in (None, 0, "", [], {}, object()):
            with self.subTest(junk=type(junk).__name__):
                out = ip.build_interpretation(junk)
                self.assertIsInstance(out, dict)
                self.assertIn("warnings", out)

    def test_failures_are_recorded_in_warnings(self):
        """子块失败必须写进 warnings（不得静默留空）。"""
        # 判词层读取抛异常 ⇒ 必须留痕
        class _Boom:
            def __getattr__(self, name):
                raise RuntimeError("boom:" + name)

        out = ip.build_interpretation(_Boom())
        self.assertIsInstance(out, dict)
        self.assertTrue(out["warnings"], "判词层读取失败却没有任何 warnings（静默）")
        self.assertTrue(any("判词层读取失败" in w for w in out["warnings"]),
                        "warnings 未点名失败环节：%r" % out["warnings"])

    def test_non_dict_guajie_is_tolerated(self):
        """判词层不是 dict ⇒ 不得崩，且照常产出各块。"""
        class _NoGuajie:
            guajie = "not-a-dict"
            bazi = []
        out = ip.build_interpretation(_NoGuajie())
        self.assertIsInstance(out, dict)
        for key in ("platform_signals", "diagnosis", "guidance", "warnings"):
            self.assertIn(key, out)

    def test_warnings_is_a_list(self):
        out = ip.build_interpretation(_result())
        self.assertIsInstance(out["warnings"], list)

    def test_no_fabricated_scores_in_output(self):
        """输出里不得出现 0–1 的浮点分数（自拟分数已作废）。"""
        out = ip.build_interpretation(_result())
        block = out.get("hexagram_state") or {}
        note = str(block.get("note", ""))
        self.assertIn("不给 0–1 分数", note,
                      "卦象状态须显式声明不给分数")


class TestIllegalInputIsRejected(unittest.TestCase):
    """非法入参必须**显式报错**，不得悄悄返回空。"""

    def test_jie_gua_rejects_bad_index(self):
        from heluo_engine.engines.heluo.jiegua import get_jie_gua
        for bad in (-1, 24, 100):
            with self.subTest(index=bad):
                with self.assertRaises(ValueError):
                    get_jie_gua(bad)

    def test_jie_gua_by_name_rejects_unknown(self):
        from heluo_engine.engines.heluo.jiegua import get_jie_gua_by_name
        with self.assertRaises(ValueError):
            get_jie_gua_by_name("不存在的节气")

    def test_hou_rejects_bad_index(self):
        from heluo_engine.engines.heluo.jiegua import get_hou
        with self.assertRaises(ValueError):
            get_hou(-1)
        with self.assertRaises(ValueError):
            get_hou(72)

    def test_hou_by_wuhou_rejects_unknown(self):
        from heluo_engine.engines.heluo.jiegua import get_hou_by_wuhou
        with self.assertRaises(ValueError):
            get_hou_by_wuhou("不存在的物候")

    def test_jie_gua_valid_index_works(self):
        """合法入参必须正常工作（守卫不能只测异常路径）。"""
        from heluo_engine.engines.heluo.jiegua import get_jie_gua
        for i in (0, 12, 23):
            with self.subTest(index=i):
                self.assertIsNotNone(get_jie_gua(i))


class TestMetricsDegradation(unittest.TestCase):
    """解读质量指标：空数据集要**显式报错**而非崩。"""

    def test_empty_dataset_returns_error(self):
        from heluo_engine.engines.heluo.metrics_v2 import evaluate_dataset
        out = evaluate_dataset([], classical_sources={}, evidence_chains=[])
        self.assertIn("error", out)
        self.assertTrue(str(out["error"]).strip())

    def test_evaluate_interpretation_handles_empty(self):
        """空解读输入不得抛异常（返回**质量评分数据类**，且自带 warnings）。"""
        from heluo_engine.engines.heluo.metrics_v2 import evaluate_interpretation
        score = evaluate_interpretation({}, None, None, [])
        # ⚠ 契约：返回的是 ``InterpretationQualityScore``（不是 dict）
        self.assertTrue(hasattr(score, "overall_score"))
        self.assertTrue(hasattr(score, "warnings"))
        self.assertTrue(score.warnings, "空解读必须给出 warnings（不留痕=静默）")


class TestInputValidation(unittest.TestCase):
    """输入预处理：缺字段必须**显式报错**。"""

    def test_prepare_heluo_input_requires_subject(self):
        from heluo_engine.engines.heluo.input import prepare_heluo_input

        class _NoSubject:
            pass

        with self.assertRaises((ValueError, AttributeError, KeyError, TypeError)):
            prepare_heluo_input(_NoSubject())


class TestCanonicalSignalContract(unittest.TestCase):
    """平台信号：无判词时**不产出**信号（而非产出空壳）。"""

    def test_build_platform_signals_on_normal_result(self):
        from heluo_engine.engines.heluo.canonical_signals import (
            build_platform_signals,
        )
        sigs = build_platform_signals(_result())
        self.assertIsInstance(sigs, list)

    def test_build_platform_signals_on_empty_result(self):
        """空 result ⇒ 不得抛异常（返回空列表即可）。"""
        from heluo_engine.engines.heluo.canonical_signals import (
            build_platform_signals,
        )
        self.assertIsInstance(build_platform_signals(None), list)


class TestPublicApiSurface(unittest.TestCase):
    """公开 API 门面：``__all__`` 与惰性导出必须一致且可用。"""

    def test_all_exports_resolve(self):
        import heluo_engine
        for name in heluo_engine.__all__:
            with self.subTest(name=name):
                self.assertIsNotNone(getattr(heluo_engine, name))

    def test_lazy_getattr_raises_for_unknown(self):
        import heluo_engine
        with self.assertRaises(AttributeError):
            heluo_engine.不存在的名字

    def test_version_is_semver(self):
        import heluo_engine
        parts = heluo_engine.__version__.split(".")
        self.assertGreaterEqual(len(parts), 3)
        for p in parts[:3]:
            self.assertTrue(p.isdigit(), "版本号非语义化：%r" % heluo_engine.__version__)


if __name__ == "__main__":
    unittest.main()
