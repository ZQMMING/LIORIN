# -*- coding: utf-8 -*-
"""平台信号出口守卫（canonical_signals.py）。

主仓已有河洛→信号的消费契约（`signal/adapters/HeluoAdapter`），但主链把
`heluo_result` 置 None，从未喂过数据。本守卫钉住河洛侧按该契约产出的信号项：

* 字段名与类型必须与平台契约一致（gua/yao/position/shi/strength/temporal_scope）；
* 每条信号都要能回查原典判词（爻辞出自包内 64 卦逐爻数据）；
* 强度不得臆造（沿用平台默认 0.5）；
* 没有判词就不产出该项（宁缺勿造）。
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.canonical_signals import (
    _yao_index,
    build_platform_signals,
)
from heluo_engine.engines.heluo.canonical import HeluoCanonical
from heluo_engine.engines.heluo.guajie import build_guajie_from_result, query_yao_duan

#: 平台适配器契约的字段（signal/adapters/__init__.py:203-211）
CONTRACT_FIELDS = ("gua", "yao", "position", "shi", "strength", "temporal_scope")

#: 《起例卷之中》L184 算例 1（历法校正后的四柱）
BAZI = [("庚", "午"), ("甲", "申"), ("丙", "申"), ("丁", "酉")]


def _signals():
    res = HeluoCanonical().calculate(
        bazi=BAZI, gender="male", birth_hour="酉", era="zhong",
        birth_year=1150, birth_date="1150-08-16",
        target_year=1150, target_month=7, target_day=22,
    )
    gj = build_guajie_from_result(
        res, bazi=BAZI, target_year=1150, target_month=7, target_day=22)
    res = replace(res, guajie=gj)
    return build_platform_signals(res), gj


class TestPlatformSignals(unittest.TestCase):
    """按平台既有契约产出信号。"""

    @classmethod
    def setUpClass(cls):
        cls.signals, cls.guajie = _signals()

    def test_signals_produced(self):
        self.assertTrue(self.signals, "应至少产出一条信号（流年/流月/流日/本命）")
        for sig in self.signals:
            for field in CONTRACT_FIELDS:
                self.assertIn(field, sig, f"缺平台契约字段 {field}")
            self.assertIsInstance(sig["gua"], str)
            self.assertIsInstance(sig["yao"], int)
            self.assertIsInstance(sig["position"], str)
            self.assertIsInstance(sig["shi"], str)
            self.assertIsInstance(sig["strength"], float)
            self.assertIsInstance(sig["temporal_scope"], dict)

    def test_yao_index_in_range(self):
        for sig in self.signals:
            self.assertIn(sig["yao"], range(1, 7),
                          f"爻位序号应为 1..6：{sig}")
            self.assertTrue(sig["position"],
                            f"position 应为爻名：{sig}")
            # 爻名 → 序号 → 爻名 必须自洽（防止「上六」被读成「五爻」这类错位）
            self.assertEqual(_yao_index(sig["position"]), sig["yao"],
                             f"爻名与爻位序号须自洽：{sig}")

    def test_strength_is_platform_default(self):
        """河洛侧不建模强度 → 沿用平台默认 0.5，且必须注明来源。"""
        for sig in self.signals:
            self.assertEqual(sig["strength"], 0.5)
            self.assertIn("platform_default", sig["strength_source"])

    def test_shi_traceable_to_original_text(self):
        """每条信号的断语都必须能在包内 64 卦逐爻数据里查到（可回查原典）。"""
        self.assertTrue(self.signals)
        for sig in self.signals:
            yao_duan = query_yao_duan(sig["gua"], sig["position"])
            self.assertIsNotNone(
                yao_duan, f"{sig['gua']}/{sig['position']} 应能在原典逐爻数据中查到")
            self.assertTrue(sig["shi"], "断语不得为空")
            self.assertTrue(
                any(part and part in sig["shi"] for part in
                    (yao_duan.ci, yao_duan.ye, yao_duan.buye)),
                f"断语须出自原典爻辞/叶吉/不叶：{sig}")

    def test_layers_are_platform_layers(self):
        layers = {s["layer"] for s in self.signals}
        self.assertTrue(layers <= {"BASELINE", "CYCLE_CONTEXT", "DAILY_ACTIVATION"},
                        f"层名须取平台三层之一：{layers}")

    def test_no_guajie_no_signal(self):
        """没有判词就不产出（宁缺勿造）。"""
        self.assertEqual(build_platform_signals(SimpleNamespace(guajie=None)), [])
        self.assertEqual(build_platform_signals(SimpleNamespace(guajie={})), [])


if __name__ == "__main__":
    unittest.main()
