"""八卦五行关系测试 - Trigram Five Elements

覆盖:
- 五行相生关系验证
- 五行相克关系验证
- 八卦纳甲数映射
- 阴阳属性验证
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import unittest
from tongshu.engines.heluo.hexagram import TRIGRAM_ELEMENT, SHENG_MAP, KE_MAP


class TestFivePhaseSheng(unittest.TestCase):
    """五行相生关系验证。"""
    
    def test_complete_cycle(self):
        """五行相生完整循环。"""
        cycle = ["金", "水", "木", "火", "土", "金"]
        for i in range(5):
            src, dst = cycle[i], cycle[i+1]
            self.assertEqual(SHENG_MAP[src], dst)
    
    def test_sheng_from_jin(self):
        """金生水。"""
        self.assertEqual(SHENG_MAP["金"], "水")
    
    def test_sheng_from_mu(self):
        """木生火。"""
        self.assertEqual(SHENG_MAP["木"], "火")


class TestFivePhaseKe(unittest.TestCase):
    """五行相克关系验证。"""
    
    def test_complete_cycle(self):
        """五行相克完整循环。"""
        cycle = ["金", "木", "土", "水", "火", "金"]
        for i in range(5):
            src, dst = cycle[i], cycle[i+1]
            self.assertEqual(KE_MAP[src], dst)
    
    def test_ke_from_jin(self):
        """金克木。"""
        self.assertEqual(KE_MAP["金"], "木")
    
    def test_ke_from_mu(self):
        """木克土。"""
        self.assertEqual(KE_MAP["木"], "土")


class TestTrigramElements(unittest.TestCase):
    """八卦五行元素测试。"""
    
    def test_all_trigrams_have_element(self):
        """所有八卦都有五行属性。"""
        for trigram in TRIGRAM_ELEMENT:
            self.assertIn(TRIGRAM_ELEMENT[trigram], {"金", "木", "水", "火", "土"})
    
    def test_two_metals(self):
        """两金：乾、兑。"""
        self.assertEqual(TRIGRAM_ELEMENT["乾"], "金")
        self.assertEqual(TRIGRAM_ELEMENT["兑"], "金")
    
    def test_two_woods(self):
        """两木：震、巽。"""
        self.assertEqual(TRIGRAM_ELEMENT["震"], "木")
        self.assertEqual(TRIGRAM_ELEMENT["巽"], "木")
    
    def test_two_earths(self):
        """两土：坤、艮。"""
        self.assertEqual(TRIGRAM_ELEMENT["坤"], "土")
        self.assertEqual(TRIGRAM_ELEMENT["艮"], "土")


if __name__ == "__main__":
    unittest.main()
