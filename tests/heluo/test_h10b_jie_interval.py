# -*- coding: utf-8 -*-
"""H10b 节气为界均匀分配 —— 节气间隔与 30 日整间隔两例（自独立包移植）。

来源：LIORIN 独立包 e13e7fd7「H10b 流日卦规则分疏——节气为界、均匀分配」，
按 main 河洛域代码底重新落码（独立包与 main 的农历月/流月编号映射不同，
故只保留与映射无关的两条契约断言）。

契约：
1. 节气间隔真实不均等（2027 年 12 个月，29.47 ~ 31.42 日）——
   不可机械固定每段日数。
2. 30 日整间隔时 hou5 均匀切分退化为经典 5 日段（与原典一致）。

另两条数值契约（test_hou5_uniform_not_mechanical / test_gua6_five_segments）
依赖独立包独有的「农历月 ↔ 流月编号」映射，在 main 代码底上不成立，
已在 docs/heluo/HELUO_ENGINE.md §11 记录待口径统一后重校。
"""
import unittest

from heluo_engine.engines.heluo.canonical import _jie_interval_for_lunar_month
from heluo_engine.engines.heluo.timeline_yun import _parse_datetime, compute_liuri


class TestH10bJieInterval(unittest.TestCase):
    def test_jie_span_uneven(self):
        """节气间隔真实不均等（2027 年 12 段，span 差异 29.47~31.42 日）。"""
        spans = []
        for lm in range(1, 13):
            t0, t1 = _jie_interval_for_lunar_month(2027, lm)
            self.assertIsNotNone(t0)
            self.assertIsNotNone(t1)
            spans.append((t1 and _parse_datetime(t1) - _parse_datetime(t0)).total_seconds() / 86400.0)
        self.assertGreater(max(spans) - min(spans), 1.0, "节气间隔应不均等（>1日差异）")
        self.assertAlmostEqual(max(spans), 31.42, delta=0.5)
        self.assertAlmostEqual(min(spans), 29.47, delta=0.5)

    def test_hou5_matches_original_when_span_30(self):
        """30 日整间隔时 hou5 均匀切分退化为经典 5 日段（与原典一致）。"""
        liuri = compute_liuri(
            [1, 1, 1, 0, 0, 0], 2,
            "2027-03-06 03:39", "2027-04-05 08:17", rule="hou5",
        )
        # 30.19 日 / 6 段 = 5.03 天/段 → 段 3 应为 11-15
        self.assertEqual(liuri.days[2]["day_from"], 11)
        self.assertEqual(liuri.days[2]["day_to"], 15)


if __name__ == "__main__":
    unittest.main()
