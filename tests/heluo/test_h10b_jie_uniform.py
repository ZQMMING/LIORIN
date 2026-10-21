# -*- coding: utf-8 -*-
"""H10b 流日卦规则分疏——节气为界均匀分配测试。

关键原则（用户核证）：日卦起算必须严格遵循各月节气交接的具体时刻，
按实际节气间隔（节→下节，约 29~31 日不等）均匀切段，不可机械固定每卦/每爻日数。
"""
import unittest

from tongshu.engines.heluo.timeline_yun import compute_liuri
from tongshu.engines.heluo.canonical import _jie_interval_for_lunar_month
from tongshu.engines.heluo_adapter import HeluoAdapter


class TestH10bJieUniform(unittest.TestCase):
    def test_jie_span_uneven(self):
        """节气间隔真实不均：2027 年 12 月 span 差异（29.47~31.42 日）。"""
        spans = []
        for lm in range(1, 13):
            t0, t1 = _jie_interval_for_lunar_month(2027, lm)
            self.assertIsNotNone(t0)
            self.assertIsNotNone(t1)
            from tongshu.engines.heluo.timeline_yun import _parse_datetime
            spans.append((t1 and _parse_datetime(t1) - _parse_datetime(t0)).total_seconds() / 86400.0)
        self.assertGreater(max(spans) - min(spans), 1.0, "节气间隔应不均等（>1日差异）")
        self.assertAlmostEqual(max(spans), 31.42, delta=0.5)
        self.assertAlmostEqual(min(spans), 29.47, delta=0.5)

    def test_hou5_uniform_not_mechanical(self):
        """五日一变（hou5）：按节气间隔均匀切段，不可机械固定每段 5 日。

        2027 年 6 月（巳月）span≈31.17 日 ÷6 ≈ 5.19 日/段，
        段5=21-26（6日）、段6=27-32（6日）——机械 5 日被打破。
        """
        r = HeluoAdapter().compute((1980, 6, 22, 10), gender="male",
                                   target_year=2027, target_month=6, target_day=15)
        dly = r.timeline.daily_hexagram["daily_yao"]
        self.assertEqual(len(dly), 6)
        # 段5（index 4）应为 6 日跨（21-26），非机械 5 日
        seg5 = dly[4]
        self.assertEqual((seg5["day_from"], seg5["day_to"]), (21, 26))
        # 末段到下一节（27-32）
        seg6 = dly[5]
        self.assertEqual((seg6["day_from"], seg6["day_to"]), (27, 32))
        # 段边界含时刻（节气为界）
        self.assertIn(":", dly[0]["date_from"], "段首应含节气时刻")
        self.assertIn("jie_span_days", dly[0])

    def test_gua6_five_segments(self):
        """六日一变（gua6）：5 段，每卦管约 6 日（31.17/5≈6.23 日）。"""
        t0, t1 = _jie_interval_for_lunar_month(2027, 6)
        m_lines = [1, 0, 1, 0, 0, 1]
        liuri = compute_liuri(m_lines, 3, t0, t1, rule="gua6")
        self.assertEqual(len(liuri.days), 5)
        seg1, seg5 = liuri.days[0], liuri.days[4]
        self.assertEqual((seg1["day_from"], seg1["day_to"]), (1, 6))
        self.assertEqual((seg5["day_from"], seg5["day_to"]), (25, 32))
        self.assertIn(":", seg1["date_from"])

    def test_hou5_matches_original_when_span_30(self):
        """30 日整间隔时 hou5 退化为经典 5 日段（与原典一致）。"""
        from tongshu.engines.heluo.timeline_yun import compute_liuri
        liuri = compute_liuri([1, 1, 1, 0, 0, 0], 2,
                              "2027-03-06 03:39", "2027-04-05 08:17", rule="hou5")
        # 30.19 日/6 ≈ 5.03 日 → 段3 ≈ 11-15
        self.assertEqual(liuri.days[2]["day_from"], 11)
        self.assertEqual(liuri.days[2]["day_to"], 15)


if __name__ == "__main__":
    unittest.main()
