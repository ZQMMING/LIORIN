"""参评诗断接入回归（2026-10-06）

锁定 canping 从「能起数」到「能出断语」的接通。

原状：canping.py 有完整的金锁银匙歌起数算法、逐页转录的五行部诗断语料
（156 条），以及按层取句的 ``layer_lines_448``，但**两端从未接起来**——
起数结果不回查诗断表，生产链路拿不到任何一条参评断语。

本文件锁：
  1. 起数算法复现原典三个向量（金锁银匙歌，见 canping 模块头载明的原典复算）
  2. 总数 → 诗断表检索（3306 = 金部 p59）
  3. 性别 → 本命层（男上/男下 vs 女上/女下）
  4. 语料未收录的数不报错，found=False 且带说明
  5. 端到端：guajie 产出 canping 块、证据与断语
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canping import (
    CANPING_LAYERS,
    judge_canping,
    layer_lines_448,
    lookup_by_number,
    qishu,
)

_BAZI = [("庚", "午"), ("辛", "巳"), ("庚", "辰"), ("壬", "申")]


class TestQishuMatchesClassic(unittest.TestCase):
    """金锁银匙歌原典复算——算法正确性的锚点。"""

    def test_shuixing_2542(self):
        """戌日寅时，乙卯（纳音水）：2000+500+14+27+1 = 2542 ✓（原文"二千五百四十二"）"""
        self.assertEqual(qishu("戌", "寅", "水", "顺")["total"], 2542)

    def test_huoxing_3347(self):
        """申日申时，戊午（纳音火）：2000+1300+18+27+2 = 3347 ✓（原文"三千三百四十七"）"""
        self.assertEqual(qishu("申", "申", "火", "顺")["total"], 3347)

    def test_reverse_2942(self):
        """戌日寅时逆数（乙卯水）：2000+900+14+27+1 = 2942 ✓（原文"二千九百四十二"）"""
        self.assertEqual(qishu("戌", "寅", "水", "逆")["total"], 2942)

    def test_direction_changes_result(self):
        """顺/逆两法须给出不同数（原典"时日顺冲还共语"）。"""
        self.assertNotEqual(qishu("戌", "寅", "水", "顺")["total"],
                            qishu("戌", "寅", "水", "逆")["total"])

    def test_steps_record_derivation(self):
        """起数五步须留痕，便于回溯与校勘。"""
        steps = qishu("辰", "申", "土", "顺")["steps"]
        self.assertGreaterEqual(len(steps), 5)
        self.assertTrue(any("二千" in s for s in steps))


class TestCorpusLookup(unittest.TestCase):
    """总数 → 诗断表。"""

    def test_lookup_known_number(self):
        item = lookup_by_number(3306)
        self.assertIsNotNone(item, "3306（金部 p59）应已转录入语料")
        self.assertEqual(str(item["no"]), "3306")
        self.assertEqual(len(item["lines"]), 6, "每编号 6 句 = 男2+女2+运2")

    def test_lookup_unknown_number_returns_none(self):
        self.assertIsNone(lookup_by_number(9999))

    def test_part_filter(self):
        self.assertIsNotNone(lookup_by_number(3306, part="jin"))
        self.assertIsNone(lookup_by_number(3306, part="tu"))


class TestLayerSelection(unittest.TestCase):
    """性别 → 本命层（参评例：上层男命、中层女命、下层大运流年）。"""

    def setUp(self):
        self.item = lookup_by_number(3306)

    def test_three_layers_differ(self):
        m = layer_lines_448(self.item, "男命")
        f = layer_lines_448(self.item, "女命")
        y = layer_lines_448(self.item, "岁运")
        self.assertEqual(len(m), 2)
        self.assertEqual(len(f), 2)
        self.assertEqual(len(y), 2)
        self.assertNotEqual(m, f)
        self.assertNotEqual(m, y)

    def test_single_sentence_labels(self):
        """单句标签与层名同源（CANPING_LAYER_SPANS 单源表）。"""
        for i, lab in enumerate(CANPING_LAYERS):
            self.assertEqual(layer_lines_448(self.item, lab),
                             [self.item["lines"][i]])


class TestJudgeCanping(unittest.TestCase):
    """起数 → 查表 → 取本命层，端到端。"""

    def test_known_chart_resolves(self):
        """1990-05-20 辰日申时，庚午年（纳音土）→ 2569 土部 p84。"""
        r = judge_canping("辰", "申", "庚", "午", "male")
        self.assertTrue(r["ok"])
        self.assertEqual(r["total"], 2569)
        self.assertTrue(r["found"], "2569 应已收录")
        self.assertEqual(r["layer"], "男命")
        self.assertEqual(len(r["lines"]), 2)
        self.assertEqual(r["part_cn"], "土部")

    def test_gender_selects_layer(self):
        m = judge_canping("辰", "申", "庚", "午", "male")
        f = judge_canping("辰", "申", "庚", "午", "female")
        self.assertEqual(m["total"], f["total"], "性别不改起数")
        self.assertEqual(m["layer"], "男命")
        self.assertEqual(f["layer"], "女命")
        self.assertNotEqual(m["lines"], f["lines"])

    def test_untranscribed_number_is_not_an_error(self):
        """全表仍在逐页录入；某数未收录应 found=False，不抛错。"""
        r = judge_canping("子", "子", "甲", "子", "male")   # 甲子纳音金
        self.assertTrue(r["ok"], "起数应成功")
        if not r["found"]:
            self.assertTrue(r["note"], "未收录须带说明")
            self.assertEqual(r["lines"], [])

    def test_bad_nayin_is_reported(self):
        r = judge_canping("辰", "申", "?", "?", "male")
        self.assertFalse(r["ok"])
        self.assertIn("纳音", r["note"])


class TestGuajieCarriesCanping(unittest.TestCase):
    """端到端：guajie 产出 canping 块。"""

    def test_guajie_has_canping(self):
        from tongshu.engines.heluo.canonical import HeluoCanonical
        from tongshu.engines.heluo.guajie import build_guajie_from_result
        r = HeluoCanonical().calculate(
            bazi=_BAZI, gender="male", birth_hour="申", era="zhong",
            birth_year=1990, birth_date="1990-05-20")
        g = build_guajie_from_result(r, bazi=_BAZI, target_year=2026,
                                     target_month=7, target_day=5)
        self.assertIn("canping", g)
        self.assertTrue(g["canping"]["ok"])
        self.assertTrue(g["canping"]["found"])
        self.assertEqual(len(g["canping"]["lines"]), 2)
        self.assertTrue(any("参评诗断" in e for e in g["evidence"]))
        self.assertTrue(any(s.startswith("参评·") for s in g["summary"]))

    def test_canping_failure_does_not_break_guajie(self):
        """参评段抛异常时，guajie 仍须完整产出（该段是独立降级域）。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        from tongshu.engines.heluo import canping as cp_mod
        from tongshu.engines.heluo.guajie import build_guajie_from_result
        r = HeluoCanonical().calculate(
            bazi=_BAZI, gender="male", birth_hour="申", era="zhong",
            birth_year=1990, birth_date="1990-05-20")

        saved = cp_mod.judge_canping

        def _boom(*a, **k):
            raise RuntimeError("参评炸了")

        cp_mod.judge_canping = _boom
        try:
            g = build_guajie_from_result(r, bazi=_BAZI, target_year=2026,
                                         target_month=7, target_day=5)
        finally:
            cp_mod.judge_canping = saved

        self.assertNotIn("error", g, "参评异常不得让 guajie 整体失败")
        self.assertTrue(g["liunian_hexagram"], "其余解卦内容须照常产出")
        self.assertIsNone(g["canping"])
        self.assertTrue(any("参评诗断：计算跳过" in e for e in g["evidence"]),
                        "降级须在 evidence 留痕")


if __name__ == "__main__":
    unittest.main()