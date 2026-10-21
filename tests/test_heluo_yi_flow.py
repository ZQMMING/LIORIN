"""河洛理数+易经 综合接入层测试 (V1.0).

验证:
- get_liunian_gua: 河洛流年卦计算(已知案例)
- gua_direction:   五行生克+卦名意象的吉凶方向
- heluo_yi_dir:    综合方向信号
- gua_jixiong:     卦名吉凶意象表
"""
from __future__ import annotations
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.heluo_yi_flow import (
    get_liunian_gua,
    gua_direction,
    heluo_yi_dir,
    direction_modifier,
    get_bazi,
)
from tongshu.engines.gua_jixiong import gua_name_direction


class TestHeluoYiBridge(unittest.TestCase):
    """河洛+易经桥接层测试."""

    def test_get_bazi_four_pillars(self):
        """四柱计算: 1974-4-28 16时 男."""
        bazi = get_bazi(1974, 4, 28, 16)
        self.assertEqual(len(bazi), 4)
        # 年柱应为甲寅
        self.assertEqual(bazi[0][0], "甲")
        self.assertEqual(bazi[0][1], "寅")

    def test_get_liunian_gua_known(self):
        """河洛流年卦: 1974-4-28 男 1996年应为水山蹇(已知桥接验证)."""
        gua = get_liunian_gua(1974, 4, 28, 16, "male", 1996)
        self.assertIsNotNone(gua)
        self.assertEqual(gua["year"], 1996)
        self.assertEqual(gua["upper"], "坎")
        self.assertEqual(gua["lower"], "艮")
        self.assertIn("蹇", gua["hexagram"])

    def test_gua_direction_wuxing(self):
        """五行生克方向: 上生下一用生体=吉."""
        # 上坎水下震木: 水生木, 用生体 -> 吉
        d = gua_direction("坎", "震")
        self.assertGreater(d, 0)

    def test_gua_direction_name_xiong(self):
        """卦名意象: 蹇卦主凶, 五行中平但卦名应下拉方向."""
        # 水山蹇: 上坎水下艮土(体克用=0), 卦名"蹇"凶 -> 综合为负
        d = gua_direction("坎", "艮", "水山蹇")
        self.assertLess(d, 0)

    def test_gua_direction_name_ji(self):
        """卦名意象: 泰卦主吉."""
        # 地天泰: 上坤土下乾金, 卦名"泰"吉 -> 综合为正
        d = gua_direction("坤", "乾", "地天泰")
        self.assertGreater(d, 0)

    def test_heluo_yi_dir_available(self):
        """综合方向信号: 应返回available与direction."""
        r = heluo_yi_dir(1974, 4, 28, 16, "male", 1996)
        self.assertTrue(r["available"])
        self.assertIn("direction", r)
        self.assertIn("label", r)
        self.assertIn("gua", r)

    def test_direction_modifier(self):
        """方向修正: 吉年正面事件加分."""
        # 吉年(方向>0)正面事件 -> 正修正
        m = direction_modifier(0.8, "positive", 0.6)
        self.assertGreater(m, 0)
        # 吉年负面事件 -> 负修正
        m2 = direction_modifier(0.8, "negative", 0.6)
        self.assertLess(m2, 0)
        # 凶年负面事件 -> 正修正(凶年负面更可能)
        m3 = direction_modifier(-0.8, "negative", 0.6)
        self.assertGreater(m3, 0)

    def test_heluo_liunian_none_for_unknown(self):
        """未知年份应返回None."""
        gua = get_liunian_gua(1974, 4, 28, 16, "male", 9999)
        self.assertIsNone(gua)


class TestGuaJixiong(unittest.TestCase):
    """卦名吉凶意象表测试."""

    def test_xiong_hexagram(self):
        """凶卦方向为负."""
        self.assertLess(gua_name_direction("水山蹇"), 0)
        self.assertLess(gua_name_direction("泽水困"), 0)
        self.assertLess(gua_name_direction("地火明夷"), 0)

    def test_ji_hexagram(self):
        """吉卦方向为正."""
        self.assertGreater(gua_name_direction("地天泰"), 0)
        self.assertGreater(gua_name_direction("地山谦"), 0)
        self.assertGreater(gua_name_direction("雷水解"), 0)

    def test_unknown_hexagram(self):
        """未收录卦返回0."""
        self.assertEqual(gua_name_direction("未知卦"), 0.0)


if __name__ == "__main__":
    unittest.main()
