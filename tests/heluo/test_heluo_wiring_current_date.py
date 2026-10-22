# -*- coding: utf-8 -*-
"""河洛生产接线的守卫（2026-10-23）：流日卦按**当前日期**自动算 + 黄历注入点。

用户裁决（2026-10-22/23）：
  「河洛还要消费黄历引擎的因为流日卦需要日期的，到时候是自动算流日卦的
    根据当前日期自动算的」

故本守卫钉住三件事：
  1. 适配器**不传目标日**时，流日卦按**今天（北京时间）**取用；
  2. 显式目标日（``target_date`` / 三元组）优先于今天；
  3. 黄历引擎以**注入**方式接入（``huangli_provider``）—— 字段契约与
     ``heluo_lunar_bridge`` 的期望一致；缺注入时走 lunar_python 兜底。
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo_adapter import (
    HeluoAdapter,
    now_beijing,
    resolve_target_date,
)


class TestTargetDateResolution(unittest.TestCase):
    """目标日解析：显式 > 今天（北京时间）。"""

    def test_explicit_target_date_wins(self):
        self.assertEqual(
            resolve_target_date(target_date="2026-09-15"),
            (2026, 9, 15))

    def test_explicit_triple_wins(self):
        self.assertEqual(
            resolve_target_date(target_year=2020, target_month=3, target_day=4),
            (2020, 3, 4))

    def test_default_is_today_beijing(self):
        now = now_beijing()
        self.assertEqual(resolve_target_date(), (now.year, now.month, now.day),
                         "默认目标日 = 今天（北京时间）")

    def test_partial_input_falls_back_to_today(self):
        """只给 target_year 时，月日仍取今天（不半截拼接）。"""
        now = now_beijing()
        self.assertEqual(
            resolve_target_date(target_year=2026),
            (2026, now.month, now.day))

    def test_now_beijing_has_timezone(self):
        now = now_beijing()
        self.assertIsNotNone(now.tzinfo, "必须带时区，避免服务器时区漂移")


class TestAdapterDefaultTarget(unittest.TestCase):
    """适配器默认按今天算流日卦。"""

    @classmethod
    def setUpClass(cls):
        cls.res = HeluoAdapter().compute((1980, 6, 22, 10), gender="male")

    def test_timeline_targets_today(self):
        """时间轴按今天计算（fast path：只算该年该月）。"""
        y = self.res.timeline.target_year_hexagram
        self.assertIsNotNone(y, "应产出流年卦")
        now = now_beijing()
        self.assertEqual(self.res.target_date,
                         f"{now.year:04d}-{now.month:02d}-{now.day:02d}",
                         "结果对象自带流日取用日 = 今天")

    def test_liuri_resolves_for_today(self):
        """流日卦按今天解出（不传任何目标日）。"""
        from tongshu.engines.heluo.guajie import build_guajie_from_result
        out = build_guajie_from_result(self.res)
        self.assertTrue(out.get("liuri_hexagram"), "流日卦应按今天自动解出")
        self.assertIsNotNone(out.get("liuri_yao"))

    def test_explicit_target_date_is_used(self):
        res = HeluoAdapter().compute((1980, 6, 22, 10), gender="male",
                                     target_date="2026-09-15")
        self.assertEqual(res.target_date, "2026-09-15",
                         "显式目标日须被采用并记录在结果上")
        from tongshu.engines.heluo.guajie import build_guajie_from_result
        out = build_guajie_from_result(res)      # 不传目标 → 回退到结果自带日期
        self.assertTrue(out.get("liuri_hexagram"),
                        "回退到结果自带的取用日仍应解出流日")


class TestHuangliInjectionPoint(unittest.TestCase):
    """黄历引擎注入点：字段契约与 heluo_lunar_bridge 期望一致。"""

    def test_bridge_accepts_injected_huangli_day(self):
        from tongshu.engines.heluo.heluo_lunar_bridge import annotate_day
        injected = {
            "day_ganzhi": "丙申", "lunar_month": "十月", "lunar_day": "初五",
            "jie_qi": "立冬", "yi": ["出行"], "ji": ["动土"],
            "day_na_yin": "山下火", "source": "huangli_engine",
        }
        anno = annotate_day("2026-11-07", injected)
        self.assertEqual(anno["day_ganzhi"], "丙申", "注入的日柱须被采用")
        self.assertEqual(anno["jie_qi"], "立冬")
        self.assertEqual(anno["source"], "huangli_engine",
                         "来源须标注入方，便于溯源")

    def test_bridge_falls_back_without_injection(self):
        """未注入时走 lunar_python 兜底（不崩、不静默空）。"""
        from tongshu.engines.heluo.heluo_lunar_bridge import annotate_day
        anno = annotate_day("2026-11-07")
        self.assertTrue(anno.get("day_ganzhi"), "兜底也须给出日柱")
        self.assertEqual(anno.get("source"), "lunar_python")

    def test_bridge_accepts_huangli_day_dataclass(self):
        """主仓 `HuangliEngine.get_day()` 返回的是 **dataclass** —— 桥接层须直接吃对象。

        平台侧因此只需一行：
            huangli_provider=lambda d: huangli_engine.get_day(d)
        不必再手工 ``.to_dict()``（此前主仓无任何代码做这次转换 → 河洛拆包后断链）。
        """
        from tongshu.engines.heluo.heluo_lunar_bridge import annotate_day

        class _HuangliDay:                       # 模拟主仓 HuangliDay 的形态
            def __init__(self):
                self.day_ganzhi = "丙申"
                self.lunar_month = "十"
                self.lunar_day = "初五"
                self.day_na_yin = "山下火"
                self.jie_qi = "立冬"
                self.yi = ["出行"]
                self.ji = ["动土"]

            def to_dict(self):
                return {
                    "day_ganzhi": self.day_ganzhi,
                    "lunar_month": self.lunar_month,
                    "lunar_day": self.lunar_day,
                    "day_na_yin": self.day_na_yin,
                    "jie_qi": self.jie_qi,
                    "yi": self.yi, "ji": self.ji,
                }

        anno = annotate_day("2026-11-07", _HuangliDay())
        self.assertEqual(anno["day_ganzhi"], "丙申", "dataclass 形态须被采用")
        self.assertEqual(anno["jie_qi"], "立冬")
        self.assertEqual(anno["source"], "huangli_engine")

    def test_bridge_survives_broken_provider_object(self):
        """注入物形态异常时不得崩（退回兜底）。"""
        from tongshu.engines.heluo.heluo_lunar_bridge import annotate_day
        anno = annotate_day("2026-11-07", object())
        self.assertTrue(anno.get("day_ganzhi"), "异常注入应退回兜底而非崩")


if __name__ == "__main__":
    unittest.main()
