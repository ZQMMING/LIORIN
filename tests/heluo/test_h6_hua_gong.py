"""H6: 化工计算测试

覆盖：NORMAL / REVERSE / RESCUED / UNRESOLVED 四种状态判定
原典依据：《河洛真数》起例卷下·论化工
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.hua_gong import compute_huagong, HuaGongState


class TestHuaGongNormal(unittest.TestCase):
    """NORMAL: 卦中含当令化工卦，无反卦"""

    def test_spring_zhen_no_dui(self):
        """春震卦，卦中含震但无兑 → NORMAL"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertEqual(r.state, HuaGongState.NORMAL)
        self.assertTrue(r.has_huagong)
        self.assertFalse(r.has_opposite)
        self.assertEqual(r.huagong_trigram, "震")

    def test_summer_li_no_kan(self):
        """夏离卦，卦中含离但无坎 → NORMAL"""
        r = compute_huagong("离", "离", "离", "乾", "午")
        self.assertEqual(r.state, HuaGongState.NORMAL)

    def test_autumn_dui_no_zhen(self):
        """秋兑卦，卦中含兑但无震 → NORMAL"""
        r = compute_huagong("兑", "兑", "乾", "兑", "申")
        self.assertEqual(r.state, HuaGongState.NORMAL)

    def test_winter_kan_no_li(self):
        """冬坎卦，卦中含坎但无离 → NORMAL"""
        r = compute_huagong("坎", "坎", "坎", "坤", "子")
        self.assertEqual(r.state, HuaGongState.NORMAL)


class TestHuaGongRescued(unittest.TestCase):
    """RESCUED: 卦中既有化工卦又有反卦"""

    def test_summer_li_with_kan(self):
        """夏离卦 + 含坎（反卦）→ RESCUED"""
        r = compute_huagong("乾", "离", "坎", "兑", "午")
        self.assertEqual(r.state, HuaGongState.RESCUED)
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)

    def test_winter_kan_with_li(self):
        """冬坎卦 + 含离（反卦）→ RESCUED"""
        r = compute_huagong("离", "坎", "乾", "坎", "子")
        self.assertEqual(r.state, HuaGongState.RESCUED)

    def test_spring_zhen_with_dui(self):
        """春震卦含震化工、含兑（震之反卦，化工相反图兑↔震）→ RESCUED（相生救应）"""
        r = compute_huagong("兑", "震", "乾", "震", "卯")
        self.assertEqual(r.state, HuaGongState.RESCUED)
        self.assertTrue(r.has_huagong)
        self.assertTrue(r.has_opposite)


class TestHuaGongReverse(unittest.TestCase):
    """REVERSE: 卦中含反卦但无当令化工卦"""

    def test_winter_kan_opposite(self):
        """冬坎卦但卦中无坎只有离 → REVERSE（反位）"""
        r = compute_huagong("乾", "离", "坤", "离", "子")
        self.assertEqual(r.state, HuaGongState.REVERSE)
        self.assertFalse(r.has_huagong)
        self.assertTrue(r.has_opposite)

    def test_summer_li_opposite(self):
        """夏离卦但卦中无离只有坎 → REVERSE"""
        r = compute_huagong("坎", "坎", "乾", "坎", "午")
        self.assertEqual(r.state, HuaGongState.REVERSE)


class TestHuaGongUnresolved(unittest.TestCase):
    """UNRESOLVED: 卦中既无化工卦也无反卦"""

    def test_winter_no_kan_no_li(self):
        """冬乾卦，无坎无离 → UNRESOLVED"""
        r = compute_huagong("乾", "乾", "坤", "坤", "子")
        self.assertEqual(r.state, HuaGongState.UNRESOLVED)
        self.assertFalse(r.has_huagong)
        self.assertFalse(r.has_opposite)

    def test_spring_no_zhen_no_dui(self):
        """春巽卦：巽非震之反卦（化工反对为兑↔震），卦中无震无兑 → UNRESOLVED"""
        r = compute_huagong("巽", "巽", "乾", "乾", "辰")
        self.assertEqual(r.state, HuaGongState.UNRESOLVED)
        self.assertFalse(r.has_huagong)
        self.assertFalse(r.has_opposite)


class TestHuaGongEvidence(unittest.TestCase):
    """化工证据链完整性"""

    def test_evidence_contains_branch(self):
        """证据链包含出生月支"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertTrue(any("寅" in e for e in r.evidence))

    def test_evidence_contains_huagong_trigram(self):
        """证据链包含当令化工卦"""
        r = compute_huagong("乾", "震", "乾", "震", "寅")
        self.assertTrue(any("震" in e for e in r.evidence))


if __name__ == "__main__":
    unittest.main()
