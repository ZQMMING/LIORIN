"""P0-FNDR-01 (R-08 ⑥ 五行 audit fix): 12 地支五行独立 Oracle 测试。

目的：
- 验证 Pillar.branch_element / _branch_element 覆盖全部 12 地支
- 验证非法地支 fail-closed（KeyError，不再静默返回 WATER）
- 与 STEM_ELEMENT 行为一致
- 不依赖 BaziEngine 任何派生逻辑，独立验证 lookup table

Evidence Source:
- 《渊海子平·论地支五行所属》(E-YHZP-001)
- 《子平真诠·论用神配气候》(E-ZPZ-002)

P0-FNDR-01: User 在第 ⑥ 五行审计中发现 branch_element 用 if-elif
            实现 + else 静默 return "WATER"，存在 fail-open 风险。
            本测试为修复后的对照验证。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.bazi_engine import (
    BRANCH_ELEMENT,
    Pillar,
    _branch_element,
)


# 经典原文事实表 (《渊海子平·论地支五行所属》):
#   子属水，丑属土，寅卯属木，辰属土，巳午属火，
#   未属土，申酉属金，戌属土，亥属水。
BRANCH_ELEMENT_EXPECTED = {
    # WATER 子亥
    "ZI":   "WATER",   # 子 — 涧下水
    "HAI":  "WATER",   # 亥 — 癸水
    # WOOD 寅卯
    "YIN":  "WOOD",    # 寅 — 甲木
    "MAO":  "WOOD",    # 卯 — 乙木
    # FIRE 巳午
    "SI":   "FIRE",    # 巳 — 丙火
    "WU":   "FIRE",    # 午 — 丁火
    # METAL 申酉
    "SHEN": "METAL",   # 申 — 庚金
    "YOU":  "METAL",   # 酉 — 辛金
    # EARTH 辰戌丑未 (四季土)
    "CHEN": "EARTH",   # 辰 — 季春土
    "XU":   "EARTH",   # 戌 — 季秋土
    "CHOU": "EARTH",   # 丑 — 季冬土
    "WEI":  "EARTH",   # 未 — 季夏土
}


class TestBranchElementCoverage(unittest.TestCase):
    """覆盖所有 12 地支（User 要求的 ⑥ 五行独立 Oracle）。"""

    def test_01_branches_dict_has_12_entries(self):
        """BRANCH_ELEMENT 必须正好包含 12 地支。"""
        self.assertEqual(len(BRANCH_ELEMENT), 12)
        for b in ("ZI", "CHOU", "YIN", "MAO", "CHEN", "SI",
                  "WU", "WEI", "SHEN", "YOU", "XU", "HAI"):
            self.assertIn(b, BRANCH_ELEMENT)

    def test_02_all_12_branches_pillar_lookup(self):
        """Pillar.branch_element 对 12 地支全覆盖 (对照经典原文)。"""
        for branch, expected_element in BRANCH_ELEMENT_EXPECTED.items():
            with self.subTest(branch=branch):
                p = Pillar("JIA", branch)  # stem 任意，只看 branch_element
                self.assertEqual(
                    p.branch_element,
                    expected_element,
                    f"Pillar(任意,{branch}).branch_element 应为 {expected_element}",
                )

    def test_03_all_12_branches_helper_function(self):
        """_branch_element 函数对 12 地支全覆盖。"""
        for branch, expected_element in BRANCH_ELEMENT_EXPECTED.items():
            with self.subTest(branch=branch):
                self.assertEqual(
                    _branch_element(branch),
                    expected_element,
                    f"_branch_element({branch}) 应为 {expected_element}",
                )

    def test_04_branches_dict_matches_expected(self):
        """BRANCH_ELEMENT 常量内容与经典原文一致。"""
        self.assertEqual(BRANCH_ELEMENT, BRANCH_ELEMENT_EXPECTED)


class TestBranchElementFailClosed(unittest.TestCase):
    """Fail-Closed: 非法输入必须 raise，不再静默返回 'WATER'。"""

    def test_05_invalid_branch_string_in_pillar_raises(self):
        """Pillar.branch_element 对非法地支必须 raise KeyError。"""
        p = Pillar("JIA", "INVALID")
        with self.assertRaises(KeyError):
            _ = p.branch_element

    def test_06_empty_branch_in_pillar_raises(self):
        """空字符串地支必须 raise KeyError。"""
        p = Pillar("JIA", "")
        with self.assertRaises(KeyError):
            _ = p.branch_element

    def test_07_lowercase_branch_in_pillar_raises(self):
        """小写地支不是合法输入，必须 raise KeyError (大小写敏感)。"""
        p = Pillar("JIA", "zi")
        with self.assertRaises(KeyError):
            _ = p.branch_element

    def test_08_invalid_branch_in_helper_raises(self):
        """_branch_element 对非法输入必须 raise KeyError。"""
        with self.assertRaises(KeyError):
            _branch_element("INVALID")

    def test_09_branch_element_no_silent_water(self):
        """关键审计点: 非法地支不能返回 'WATER' (这是 P0-FNDR-01 修复的核心目标)。"""
        # P0-FNDR-01: 原代码 Pillar(任意, "INVALID").branch_element 静默返回 "WATER"
        # 修复后必须 raise
        try:
            result = _branch_element("INVALID")
            self.fail(
                f"_branch_element('INVALID') 不应返回 {result!r}, "
                "必须 raise KeyError (fail-closed)"
            )
        except KeyError:
            pass  # 期望行为


class TestBranchElementEvidence(unittest.TestCase):
    """Evidence 元数据检查。"""

    def test_10_evidence_id_present(self):
        """BRANCH_ELEMENT 必须有 evidence_id 元数据 (在 bazi_facts.EVIDENCE_IDS 中)。"""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        self.assertIn("BRANCH_ELEMENT", EVIDENCE_IDS)
        self.assertTrue(EVIDENCE_IDS["BRANCH_ELEMENT"])


if __name__ == "__main__":
    unittest.main()
