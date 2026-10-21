# -*- coding: utf-8 -*-
"""H10 惰性化定稿方案测试。

对齐定稿 JSON：yearly_meta（全量元数据）/ target_year_hexagram（目标流年卦）/
monthly_hexagrams（目标年 12 流月卦，顶层完整）/ daily_hexagram（目标月流日本卦，
base_hex + daily_yao 6 段，每爻管 5 日、满 30 日）。
"""
import unittest

from tongshu.engines.heluo_adapter import HeluoAdapter


class TestH10LazyTimeline(unittest.TestCase):
    def setUp(self):
        self.a = HeluoAdapter()

    def test_lazy_with_target(self):
        """带 target：只算目标点，structure 对齐定稿 JSON。"""
        r = self.a.compute((1980, 6, 22, 10), gender="male",
                           target_year=2027, target_month=6, target_day=15)
        tl = r.timeline
        # 流年元数据全量（有大运段覆盖的年龄），无卦象
        self.assertTrue(len(tl.yearly_meta) >= 80, "流年元数据应覆盖大运段内全部年龄")
        for m in tl.yearly_meta[:3]:
            self.assertIn("year", m)
            self.assertIn("ganzhi", m)
        # 目标流年卦（惰性：yearly_hexagrams 仅目标年 1 条）
        self.assertEqual(len(tl.yearly_hexagrams), 1)
        self.assertEqual(tl.yearly_hexagrams[0]["year"], 2027)
        self.assertTrue(tl.yearly_hexagrams[0]["hexagram"])
        # 流月卦顶层 12 条完整（month 1-12，含卦象/流日段）
        self.assertEqual(len(tl.monthly_hexagrams), 12)
        m6 = tl.monthly_hexagrams[5]
        self.assertEqual(m6["month"], 6)
        self.assertTrue(m6["name"])
        self.assertTrue(m6["lines"])
        self.assertTrue(m6["days"], "流月应带流日段")
        # 流日卦顶层：base_hex + daily_yao 6 段（每爻管 5 日，满 30 日）
        dly = tl.daily_hexagram
        self.assertEqual(len(dly["daily_yao"]), 6)
        seg3 = dly["daily_yao"][2]
        self.assertEqual((seg3["day_from"], seg3["day_to"]), (11, 15))
        self.assertEqual(dly["target_day"], 15)
        self.assertEqual(dly["active_segment"]["day_from"], 11)
        self.assertTrue(dly["base_hex"])

    def test_no_target_compat(self):
        """无 target：保持全量兼容（静态层一次算完，不动旧语义）；惰性作用在目标查询路径。"""
        r = self.a.compute((1980, 6, 22, 10), gender="male")
        tl = r.timeline
        # 兼容：无 target 时 yearly_hexagrams 全量（liunian_count 语义不变）
        self.assertTrue(len(tl.yearly_hexagrams) >= 80, "无 target 保持全量流年卦")
        self.assertEqual(len(tl.yearly_meta), len(tl.yearly_hexagrams))

    def test_lazy_guajie_uses_top_level(self):
        """解卦层消费顶层结构：流日段命中 target_day（每爻 5 日）。"""
        r = self.a.compute((1980, 6, 22, 10), gender="male",
                           target_year=2027, target_month=6, target_day=15)
        gj = r.guajie or {}
        self.assertTrue(gj.get("liunian_hexagram"))
        self.assertTrue(gj.get("liuyue_yao"))
        self.assertTrue(gj.get("liuri_yao"))
        lr = gj["liuri_yao"]
        self.assertIn("jingyi", lr)
        # 流时按设计剥离
        self.assertIsNone(gj.get("liushi_yao"))

    def test_dayun_metadata(self):
        """大运层：元数据（不起卦），12 段覆盖。"""
        r = self.a.compute((1980, 6, 22, 10), gender="male")
        dayun = r.timeline.qi_phase.get("dayun") or []
        self.assertTrue(len(dayun) >= 10, "大运段应覆盖（阳爻9年/阴爻6年）")
        for e in dayun:
            self.assertIn("age_start", e)
            self.assertIn("age_end", e)
            self.assertIn("hexagram", e)  # 所在卦名（先天/后天），非新起卦


if __name__ == "__main__":
    unittest.main()
