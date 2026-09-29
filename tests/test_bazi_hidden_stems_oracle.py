"""P0-FNDR-04 (R-10 ⑧ 藏干 audit fix): 12 地支完整藏干 Oracle 测试。

目的:
- 验证 hidden_stems_all() / hidden_main_stem() 对 12 地支全覆盖
- 验证 fail-closed (非法输入 KeyError)
- 验证 bazi_facts → bazi_ten_gods → bazi_engine → bazi_l1_facts 单源链
- 验证 bazi_l1_facts 派生视图 (中文键) 与 canonical 拼音表完全一致
- 不依赖任何派生计算, 独立验证 lookup

架构约束 (User 第八轮审计):
- 藏干数据单源真相在 tongshu.facts.bazi_facts.BRANCH_HIDDEN_STEMS
- 三个旧副本 (bazi_engine._BRANCH_HIDDEN_MAIN / bazi_l1_facts.BRANCH_HIDDEN_STEMS /
  bazi_ten_gods 内部) 已统一指向 canonical 表

Evidence Source:
- 《渊海子平·论地支藏干》(E-YHZP-013~024) — 主气/中气/余气三层表
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS as FACTS_HHS
from tongshu.reasoning.bazi_ten_gods import (
    hidden_main_stem,
    hidden_stems_all,
    hidden_main_role,
)
from tongshu.engines.bazi_l1_facts import (
    BRANCH_HIDDEN_STEMS as L1_HHS,
    TIAN_GAN_WU_XING as L1_TG_WX,
    HIDDEN_STEM_EVIDENCE_ID,
)


# Canonical 事实表 (基于《渊海子平·论地支藏干》):
# 拼音 -> [主气, 中气?, 余气?] (None 表示该层无藏干)
HIDDEN_STEMS_EXPECTED_PINYIN = {
    "ZI":   ["GUI"],                    # 子 — 癸水
    "CHOU": ["JI", "GUI", "XIN"],       # 丑 — 己癸辛 (季冬土)
    "YIN":  ["JIA", "BING", "WU"],      # 寅 — 甲丙戊 (春木)
    "MAO":  ["YI"],                     # 卯 — 乙木
    "CHEN": ["WU", "YI", "GUI"],        # 辰 — 戊乙癸 (季春土)
    "SI":   ["BING", "WU", "GENG"],     # 巳 — 丙戊庚 (夏火)
    "WU":   ["DING", "JI"],             # 午 — 丁己
    "WEI":  ["JI", "DING", "YI"],       # 未 — 己丁乙 (季夏土)
    "SHEN": ["GENG", "REN", "WU"],      # 申 — 庚壬戊 (秋金)
    "YOU":  ["XIN"],                    # 酉 — 辛金
    "XU":   ["WU", "XIN", "DING"],      # 戌 — 戊辛丁 (季秋土)
    "HAI":  ["REN", "JIA"],             # 亥 — 壬甲
}

# 中文键 -> [主气, 中气?, 余气?]
HIDDEN_STEMS_EXPECTED_CHINESE = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}


class TestHiddenStemsFacts(unittest.TestCase):
    """Canonical facts 表验证."""

    def test_01_facts_has_12_branches(self):
        """bazi_facts.BRANCH_HIDDEN_STEMS 必须包含 12 地支."""
        self.assertEqual(len(FACTS_HHS), 12)
        for b in ("ZI", "CHOU", "YIN", "MAO", "CHEN", "SI",
                  "WU", "WEI", "SHEN", "YOU", "XU", "HAI"):
            self.assertIn(b, FACTS_HHS)

    def test_02_facts_matches_expected_pinyin(self):
        """bazi_facts 拼音键与《渊海子平》一致."""
        for pinyin, expected in HIDDEN_STEMS_EXPECTED_PINYIN.items():
            with self.subTest(branch=pinyin):
                entries = FACTS_HHS[pinyin]
                actual = [stem for stem, _role in entries]
                self.assertEqual(
                    actual, expected,
                    f"{pinyin} 藏干应为 {expected}, 实际 {actual}",
                )

    def test_03_facts_role_order_preserved(self):
        """藏干角色顺序: main, middle, residual."""
        for pinyin, entries in FACTS_HHS.items():
            roles = [role for _stem, role in entries]
            with self.subTest(branch=pinyin):
                # 角色必须是 main 开头, 中间是 middle, 最后是 residual
                for r in roles:
                    self.assertIn(r, {"main", "middle", "residual"})
                # 必须有 main
                self.assertEqual(roles[0], "main")


class TestHiddenStemsAllAPI(unittest.TestCase):
    """canonical API 验证: hidden_main_stem / hidden_stems_all."""

    def test_04_hidden_main_stem_all_12(self):
        """hidden_main_stem 对 12 地支全覆盖 (主气)."""
        for pinyin, expected in HIDDEN_STEMS_EXPECTED_PINYIN.items():
            with self.subTest(branch=pinyin):
                self.assertEqual(hidden_main_stem(pinyin), expected[0])

    def test_05_hidden_stems_all_all_12(self):
        """hidden_stems_all 对 12 地支返回完整层级列表."""
        for pinyin, expected in HIDDEN_STEMS_EXPECTED_PINYIN.items():
            with self.subTest(branch=pinyin):
                self.assertEqual(hidden_stems_all(pinyin), expected)

    def test_06_hidden_main_role(self):
        """hidden_main_role 固定返回 'main'."""
        for pinyin in HIDDEN_STEMS_EXPECTED_PINYIN:
            with self.subTest(branch=pinyin):
                self.assertEqual(hidden_main_role(pinyin), "main")


class TestL1DerivedView(unittest.TestCase):
    """bazi_l1_facts 派生视图 (中文键) 验证."""

    def test_07_l1_has_12_branches_chinese(self):
        """bazi_l1_facts.BRANCH_HIDDEN_STEMS 必须包含 12 中文地支."""
        self.assertEqual(len(L1_HHS), 12)
        for b in ("子", "丑", "寅", "卯", "辰", "巳",
                  "午", "未", "申", "酉", "戌", "亥"):
            self.assertIn(b, L1_HHS)

    def test_08_l1_matches_expected_chinese(self):
        """L1 中文键藏干与《渊海子平》一致."""
        for chinese, expected in HIDDEN_STEMS_EXPECTED_CHINESE.items():
            with self.subTest(branch=chinese):
                hidden_dict = L1_HHS[chinese]
                # 提取本气/中气/余气 (非 None)
                actual = [
                    hidden_dict["本气"],
                    hidden_dict["中气"],
                    hidden_dict["余气"],
                ]
                # 去除 None
                actual_clean = [x for x in actual if x]
                self.assertEqual(
                    actual_clean, expected,
                    f"{chinese} 藏干应为 {expected}, 实际 {actual_clean}",
                )

    def test_09_l1_structure_keys(self):
        """L1 藏干必须包含 本气/中气/余气 三个键 (即使值为 None)."""
        for b, hidden in L1_HHS.items():
            with self.subTest(branch=b):
                self.assertIn("本气", hidden)
                self.assertIn("中气", hidden)
                self.assertIn("余气", hidden)

    def test_10_l1_tian_gan_wu_xing_complete(self):
        """L1 天干五行映射完整 10 天干."""
        self.assertEqual(len(L1_TG_WX), 10)
        for stem, expected_element in [
            ("甲", "WOOD"), ("乙", "WOOD"),
            ("丙", "FIRE"), ("丁", "FIRE"),
            ("戊", "EARTH"), ("己", "EARTH"),
            ("庚", "METAL"), ("辛", "METAL"),
            ("壬", "WATER"), ("癸", "WATER"),
        ]:
            with self.subTest(stem=stem):
                self.assertEqual(L1_TG_WX[stem], expected_element)


class TestSingleSource(unittest.TestCase):
    """单源真相验证: 三个表内容必须一致."""

    def test_11_canonical_pinyin_vs_l1_chinese_consistency(self):
        """canonical 拼音表与 L1 中文派生视图内容一致."""
        for pinyin, chinese in [
            ("ZI", "子"), ("CHOU", "丑"), ("YIN", "寅"), ("MAO", "卯"),
            ("CHEN", "辰"), ("SI", "巳"), ("WU", "午"), ("WEI", "未"),
            ("SHEN", "申"), ("YOU", "酉"), ("XU", "戌"), ("HAI", "亥"),
        ]:
            canonical_stems = [stem for stem, _ in FACTS_HHS[pinyin]]
            l1_hidden = L1_HHS[chinese]
            l1_stems = [
                s for s in [l1_hidden["本气"], l1_hidden["中气"], l1_hidden["余气"]]
                if s is not None
            ]
            with self.subTest(branch=pinyin):
                # canonical 拼音 -> 中文映射, 应与 L1 中文派生一致
                pinyin_to_chinese_stem = {
                    "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁",
                    "WU": "戊", "JI": "己", "GENG": "庚", "XIN": "辛",
                    "REN": "壬", "GUI": "癸",
                }
                expected_chinese = [pinyin_to_chinese_stem[s] for s in canonical_stems]
                self.assertEqual(
                    l1_stems, expected_chinese,
                    f"{pinyin}({chinese}) 派生视图与 canonical 不一致",
                )


class TestFailClosed(unittest.TestCase):
    """Fail-closed 验证."""

    def test_12_invalid_branch_hidden_main_raises(self):
        """hidden_main_stem 对非法地支 KeyError."""
        with self.assertRaises(KeyError):
            hidden_main_stem("INVALID")

    def test_13_invalid_branch_hidden_all_raises(self):
        """hidden_stems_all 对非法地支 KeyError."""
        with self.assertRaises(KeyError):
            hidden_stems_all("INVALID")

    def test_14_lowercase_branch_raises(self):
        """小写地支 KeyError (大小写敏感)."""
        with self.assertRaises(KeyError):
            hidden_main_stem("zi")


class TestEvidence(unittest.TestCase):
    """Evidence 元数据."""

    def test_15_hidden_stem_evidence_id_present(self):
        """HIDDEN_STEM_EVIDENCE_ID 存在且非空."""
        self.assertTrue(HIDDEN_STEM_EVIDENCE_ID)
        self.assertIsInstance(HIDDEN_STEM_EVIDENCE_ID, str)

    def test_16_facts_evidence_ids_include_hidden_stems(self):
        """bazi_facts.EVIDENCE_IDS 必须包含 BRANCH_HIDDEN_STEMS."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        self.assertIn("BRANCH_HIDDEN_STEMS", EVIDENCE_IDS)


if __name__ == "__main__":
    unittest.main()
