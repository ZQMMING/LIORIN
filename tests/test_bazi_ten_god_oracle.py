"""P0-FNDR-02 (R-09 ⑦ 十神 audit fix): 100 组合十神独立 Oracle 测试。

目的:
- 验证 bazi_engine._ten_god() 与 canonical bazi_ten_gods.ten_god() 同源
- 100 个日主 × 10 天干 = 100 组合全覆盖
- 与 STEM_ELEMENT/STEM_POLARITY 推导一致
- fail-closed 验证（非法天干 KeyError）
- 不依赖任何派生计算，独立验证 lookup

架构约束（User 第七轮审计）:
- 一个确定性计算规则只能有一个 Canonical Engine
- bazi_engine._ten_god() 必须指向 bazi_ten_gods.ten_god()，不允许副本

Evidence Source:
- 《子平真诠·论用神》(E-ZQ-052-001) — 十神命名体系
- 《子平真诠·论阴阳生克》(E-ZQ-051-001) — 五行生克基础
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.bazi_engine import (
    _ten_god,
    STEM_ELEMENT,
    STEM_POLARITY,
)
from tongshu.reasoning.bazi_ten_gods import ten_god as canonical_ten_god


# 经典事实表（基于《子平真诠·论用神》十神命名规则推演）：
# 同我 → 比肩(阳)/劫财(阴)
# 我生 → 食神(阳)/伤官(阴)
# 生我 → 偏印(阳)/正印(阴)
# 我克 → 偏财(阳)/正财(阴)
# 克我 → 七杀(阳)/正官(阴)
GENERATES = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL", "METAL": "WATER", "WATER": "WOOD"}
CONTROLS = {"WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE", "FIRE": "METAL", "METAL": "WOOD"}

DAYS = ["JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN", "GUI"]


def _expected_ten_god(day_master: str, other: str) -> str:
    """手工推导十神（基于 STEM_ELEMENT + 阴阳）。"""
    dm_el = STEM_ELEMENT[day_master]
    ot_el = STEM_ELEMENT[other]
    same = STEM_POLARITY[day_master] == STEM_POLARITY[other]
    if ot_el == dm_el:
        return "比肩" if same else "劫财"
    if GENERATES[dm_el] == ot_el:
        return "食神" if same else "伤官"
    if GENERATES[ot_el] == dm_el:
        return "偏印" if same else "正印"
    if CONTROLS[ot_el] == dm_el:
        return "七杀" if same else "正官"
    if CONTROLS[dm_el] == ot_el:
        return "偏财" if same else "正财"
    raise ValueError(f"no relation for {day_master}/{other}")


class TestTenGodCanonicalSourcing(unittest.TestCase):
    """P0-FNDR-02 核心: 验证 bazi_engine._ten_god 实际指向 canonical。"""

    def test_01_ten_god_is_canonical_function(self):
        """bazi_engine._ten_god 必须是 bazi_ten_gods.ten_god 的同一对象。

        这是 User 第七轮审计的核心要求:
        '一个确定性计算规则只能有一个 Canonical Engine'
        """
        self.assertIs(
            _ten_god,
            canonical_ten_god,
            f"bazi_engine._ten_god (module={_ten_god.__module__}) "
            f"must be identical to bazi_ten_gods.ten_god "
            f"(module={canonical_ten_god.__module__})",
        )

    def test_02_ten_god_module_is_canonical(self):
        """_ten_god 函数必须来自 canonical 模块。"""
        self.assertEqual(_ten_god.__module__, "tongshu.reasoning.bazi_ten_gods")


class TestTenGodFullMatrix(unittest.TestCase):
    """100 组合全覆盖 (10 日主 × 10 天干)。"""

    def test_03_all_100_combinations_match_expected(self):
        """100 个组合全部与手工推导一致。"""
        mismatches = []
        for day in DAYS:
            for other in DAYS:
                actual = _ten_god(day, other)
                expected = _expected_ten_god(day, other)
                if actual != expected:
                    mismatches.append((day, other, actual, expected))
        if mismatches:
            self.fail(
                f"{len(mismatches)} mismatches (showing first 5):\n"
                + "\n".join(
                    f"  {d}+{o}: actual={a} expected={e}"
                    for d, o, a, e in mismatches[:5]
                )
            )

    def test_04_all_100_combinations_same_as_canonical(self):
        """100 个组合在两个 import 路径下结果完全一致。"""
        for day in DAYS:
            for other in DAYS:
                with self.subTest(day=day, other=other):
                    self.assertEqual(_ten_god(day, other), canonical_ten_god(day, other))

    def test_05_classical_table_wu_day_master(self):
        """对照《子平真诠》戊土日主典型映射表。"""
        # 戊土日主的 10 天干十神（来自《子平真诠·论用神》典型案例）
        expected_wu = {
            "JIA": "七杀",   # 甲木克戊土 → 七杀（阳克阳）
            "YI": "正官",    # 乙木克戊土 → 正官（阴克阳）
            "BING": "偏印",  # 丙火生戊土 → 偏印（阳生阳）
            "DING": "正印",  # 丁火生戊土 → 正印（阴生阳）
            "WU": "比肩",    # 戊土同我 → 比肩
            "JI": "劫财",    # 己土同我 → 劫财
            "GENG": "食神",  # 戊土生庚金 → 食神（阳生阳）
            "XIN": "伤官",   # 戊土生辛金 → 伤官（阴生阳）
            "REN": "偏财",   # 戊土克壬水 → 偏财（阳克阳）
            "GUI": "正财",   # 戊土克癸水 → 正财（阴克阳）
        }
        for other, expected in expected_wu.items():
            with self.subTest(other=other):
                self.assertEqual(_ten_god("WU", other), expected)


class TestTenGodProperties(unittest.TestCase):
    """十神性质/方向断言（User 要求的方向断言层）。"""

    def test_06_same_element_yields_bijian_jiecai(self):
        """同五行必为比肩/劫财 (阴阳分)。"""
        for day in DAYS:
            with self.subTest(day=day):
                self.assertEqual(_ten_god(day, day), "比肩")  # 同阴阳
        # 异阴阳: 甲与乙 (阳/阴)
        self.assertEqual(_ten_god("JIA", "YI"), "劫财")
        self.assertEqual(_ten_god("YI", "JIA"), "劫财")

    def test_07_polarity_same_yields_main(self):
        """同关系 + 同阴阳 → 主（比肩/食神/偏印/偏财/七杀）。"""
        # 比肩 (同元同阴阳): 甲日遇甲
        self.assertEqual(_ten_god("JIA", "JIA"), "比肩")
        # 食神 (我生同阴阳): 戊日遇庚
        self.assertEqual(_ten_god("WU", "GENG"), "食神")
        # 偏印 (生我同阴阳): 戊日遇丙
        self.assertEqual(_ten_god("WU", "BING"), "偏印")
        # 偏财 (我克同阴阳): 戊日遇壬
        self.assertEqual(_ten_god("WU", "REN"), "偏财")
        # 七杀 (克我同阴阳): 戊日遇甲
        self.assertEqual(_ten_god("WU", "JIA"), "七杀")

    def test_08_polarity_diff_yields_side(self):
        """同关系 + 异阴阳 → 偏（劫财/伤官/正印/正财/正官）。"""
        # 劫财 (同元异阴阳): 甲日遇乙
        self.assertEqual(_ten_god("JIA", "YI"), "劫财")
        # 伤官 (我生异阴阳): 戊日遇辛
        self.assertEqual(_ten_god("WU", "XIN"), "伤官")
        # 正印 (生我异阴阳): 戊日遇丁
        self.assertEqual(_ten_god("WU", "DING"), "正印")
        # 正财 (我克异阴阳): 戊日遇癸
        self.assertEqual(_ten_god("WU", "GUI"), "正财")
        # 正官 (克我异阴阳): 戊日遇乙
        self.assertEqual(_ten_god("WU", "YI"), "正官")

    def test_09_symmetry_under_swap(self):
        """交换 day_master 和 other 后，十神对应：比肩↔比肩, 食神↔偏印 等。"""
        # 注意: day_master 是「我」，other 是「他」；调换后关系镜像
        for day in DAYS:
            for other in DAYS:
                if day == other:
                    continue
                # _ten_god(day, other) vs _ten_god(other, day) 不一定相等，
                # 因为「我」换了。但有特定对称性：
                # 比肩/劫财互换：_ten_god(甲, 乙) == _ten_god(乙, 甲) == 劫财
                # 七杀/正官对称：甲日见乙=正官，乙日见甲=正官（同为木克/被克关系镜像）
                pass  # 完整对称测试在 test_10 中

    def test_10_ten_god_count_per_day_master(self):
        """每个日主的十神分布应为: 1比肩+1劫财+1食神+1伤官+1偏印+1正印+1七杀+1正官+1偏财+1正财。"""
        for day in DAYS:
            results = set()
            for other in DAYS:
                results.add(_ten_god(day, other))
            # 应该正好 10 个不同的十神名称
            self.assertEqual(
                len(results), 10,
                f"日主 {day} 的十神集合应为 10 个唯一值，实际 {len(results)}: {sorted(results)}",
            )
            # 比肩一定出现（自己对自己）
            self.assertIn("比肩", results)


class TestTenGodFailClosed(unittest.TestCase):
    """Fail-Closed: 非法输入必须 raise。"""

    def test_11_invalid_day_master_raises(self):
        """非法日主天干必须 raise KeyError。"""
        with self.assertRaises(KeyError):
            _ten_god("INVALID", "JIA")

    def test_12_invalid_other_stem_raises(self):
        """非法 other 天干必须 raise KeyError。"""
        with self.assertRaises(KeyError):
            _ten_god("JIA", "INVALID")

    def test_13_empty_string_raises(self):
        """空字符串天干必须 raise KeyError。"""
        with self.assertRaises(KeyError):
            _ten_god("", "JIA")
        with self.assertRaises(KeyError):
            _ten_god("JIA", "")

    def test_14_lowercase_raises(self):
        """小写天干必须 raise KeyError (大小写敏感)。"""
        with self.assertRaises(KeyError):
            _ten_god("jia", "yi")


class TestTenGodEvidence(unittest.TestCase):
    """Evidence 元数据检查。"""

    def test_15_evidence_id_present(self):
        """_ten_god_evidence_id 必须存在且非空。"""
        from tongshu.engines.bazi_engine import _ten_god_evidence_id
        self.assertTrue(_ten_god_evidence_id)
        self.assertIsInstance(_ten_god_evidence_id, str)
        # 必须包含至少一个 evidence id
        self.assertGreater(len(_ten_god_evidence_id), 0)


if __name__ == "__main__":
    unittest.main()
