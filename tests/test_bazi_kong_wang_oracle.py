"""P0-FNDR-06 (R-12 ⑩ 空亡 audit fix): 60 甲子空亡全覆盖 Oracle 测试.

目的:
- 验证 KONG_WANG_BY_XUN 6 旬全覆盖 (60 甲子)
- 验证 JIAZI_TABLE/JIAZI_INDEX 60 甲子无重复无缺失
- 验证 _get_jiazi_index / calc_kong_wang fail-closed (非法干支 raise KeyError)
- 验证 6 旬空亡地支与《渊海子平·论空亡》一致
- 验证 XUN_BRANCHES (旬内 10 地支) 互补 KONG_WANG_BY_XUN

架构约束 (User 第十二轮审计):
- KONG_WANG_BY_XUN / JIAZI_TABLE / JIAZI_INDEX / XUN_BRANCHES 在 bazi_facts (单源真相)
- _get_jiazi_index 用 JIAZI_INDEX O(1) 查找, 非法干支 raise KeyError (fail-closed)
- 60 甲子全部覆盖, 不允许静默 fail-open

Evidence Source:
- 《渊海子平·论空亡旬表》(E-YHZP-008-001) - 六甲旬空亡规则
- 《渊海子平·六十甲子对照表》(E-YHZP-009-001) - 60 甲子序列
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.facts.bazi_facts import (
    KONG_WANG_BY_XUN, JIAZI_TABLE, JIAZI_INDEX, XUN_BRANCHES,
)
from tongshu.engines.bazi_engine import (
    BaziChart, Pillar, calc_kong_wang, _get_jiazi_index,
    attach_p2_fields,
)


# 6 旬空亡事实表 (基于《渊海子平·论空亡旬表》):
# 甲子旬(序号0-9):   子丑寅卯辰巳午未申酉  用, 戌亥  空亡
# 甲戌旬(序号10-19): 戌亥子丑寅卯辰巳午未  用, 申酉  空亡
# 甲申旬(序号20-29): 申酉戌亥子丑寅卯辰巳  用, 午未  空亡
# 甲午旬(序号30-39): 午未申酉戌亥子丑寅卯  用, 辰巳  空亡
# 甲辰旬(序号40-49): 辰巳午未申酉戌亥子丑  用, 寅卯  空亡
# 甲寅旬(序号50-59): 寅卯辰巳午未申酉戌亥  用, 子丑  空亡
EXPECTED_KONG_WANG_BY_XUN = {
    0: ("XU", "HAI"),     # 甲子旬
    1: ("SHEN", "YOU"),   # 甲戌旬
    2: ("WU", "WEI"),     # 甲申旬
    3: ("CHEN", "SI"),    # 甲午旬
    4: ("YIN", "MAO"),    # 甲辰旬
    5: ("ZI", "CHOU"),    # 甲寅旬
}


def _make_chart_with_day(day_stem: str, day_branch: str) -> BaziChart:
    """构造合法 60 甲子 chart, 日柱 = (day_stem, day_branch)."""
    pillars = [
        Pillar(*JIAZI_TABLE[0]),    # 年柱 = 甲子
        Pillar(*JIAZI_TABLE[1]),    # 月柱 = 乙丑
        Pillar(day_stem, day_branch),  # 日柱 = 测试目标
        Pillar(*JIAZI_TABLE[3]),    # 时柱 = 丁卯
    ]
    chart = BaziChart(
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        day_master=day_stem,
        luck_pillars=[],
        gender="male",
    )
    return attach_p2_fields(chart)


class TestJiaziTable(unittest.TestCase):
    """60 甲子完整表测试."""

    def test_01_jiazi_table_has_60_entries(self):
        """JIAZI_TABLE 必须正好 60 条."""
        self.assertEqual(len(JIAZI_TABLE), 60)

    def test_02_jiazi_index_keys_complete(self):
        """JIAZI_INDEX 索引 60 个唯一键."""
        self.assertEqual(len(JIAZI_INDEX), 60)

    def test_03_jiazi_table_no_duplicates(self):
        """60 甲子无重复."""
        seen = set()
        for stem, branch in JIAZI_TABLE:
            pair = (stem, branch)
            self.assertNotIn(pair, seen, f"重复干支对: {pair}")
            seen.add(pair)

    def test_04_jiazi_index_matches_table(self):
        """JIAZI_INDEX 与 JIAZI_TABLE 内容一致."""
        for i, (stem, branch) in enumerate(JIAZI_TABLE):
            self.assertEqual(JIAZI_INDEX[(stem, branch)], i)


class TestKongWangFactTable(unittest.TestCase):
    """KONG_WANG_BY_XUN 6 旬事实表."""

    def test_05_kong_wang_covers_6_xun(self):
        """KONG_WANG_BY_XUN 必须覆盖 6 旬 (0-5)."""
        self.assertEqual(len(KONG_WANG_BY_XUN), 6)
        for xun in range(6):
            self.assertIn(xun, KONG_WANG_BY_XUN)

    def test_06_kong_wang_matches_expected(self):
        """空亡地支与《渊海子平》一致."""
        for xun, expected_pair in EXPECTED_KONG_WANG_BY_XUN.items():
            with self.subTest(xun=xun):
                self.assertEqual(KONG_WANG_BY_XUN[xun], expected_pair)

    def test_07_xun_branches_complement_kong_wang(self):
        """XUN_BRANCHES (旬内 10 地支) 互补 KONG_WANG_BY_XUN (旬外 2 空亡)."""
        all_branches = set(b for b_tuple in XUN_BRANCHES.values() for b in b_tuple)
        self.assertEqual(len(all_branches), 12)  # 覆盖所有 12 地支 (各旬中 10 个互有重叠)
        # 每旬: 10 + 2 = 12, 但 10 中可能重复 (各旬共享 8 个)
        # 实际: 每旬的 10 地支 + 2 空亡 = 12 (一个完整旬)
        for xun, used_branches in XUN_BRANCHES.items():
            with self.subTest(xun=xun):
                kw_branches = set(KONG_WANG_BY_XUN[xun])
                # 旬内 10 地支 + 旬外 2 空亡 = 12 (完整集合)
                combined = set(used_branches) | kw_branches
                # 注意: 10 + 2 包含 12 个不重复的 (地支)
                self.assertEqual(len(used_branches), 10)
                self.assertEqual(len(kw_branches), 2)
                self.assertEqual(len(combined), 12)


class TestKongWangByPillar(unittest.TestCase):
    """calc_kong_wang 对 60 甲子全覆盖."""

    def test_08_kong_wang_for_jiazi_xun(self):
        """甲子旬 (序号 0-9): 任意日柱空亡 = (XU, HAI)."""
        # 甲子旬包含的日柱: 甲子乙丑丙寅丁卯戊辰己巳庚午辛未壬申癸酉
        jiazi_xun_stems = [
            ("JIA", "ZI"), ("YI", "CHOU"), ("BING", "YIN"), ("DING", "MAO"),
            ("WU", "CHEN"), ("JI", "SI"), ("GENG", "WU"), ("XIN", "WEI"),
            ("REN", "SHEN"), ("GUI", "YOU"),
        ]
        for stem, branch in jiazi_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("XU", "HAI"))

    def test_09_kong_wang_for_jiaxu_xun(self):
        """甲戌旬 (序号 10-19): 空亡 = (SHEN, YOU)."""
        jiaxu_xun_stems = [
            ("JIA", "XU"), ("YI", "HAI"), ("BING", "ZI"), ("DING", "CHOU"),
            ("WU", "YIN"), ("JI", "MAO"), ("GENG", "CHEN"), ("XIN", "SI"),
            ("REN", "WU"), ("GUI", "WEI"),
        ]
        for stem, branch in jiaxu_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("SHEN", "YOU"))

    def test_10_kong_wang_for_jiashen_xun(self):
        """甲申旬 (序号 20-29): 空亡 = (WU, WEI)."""
        jiashen_xun_stems = [
            ("JIA", "SHEN"), ("YI", "YOU"), ("BING", "XU"), ("DING", "HAI"),
            ("WU", "ZI"), ("JI", "CHOU"), ("GENG", "YIN"), ("XIN", "MAO"),
            ("REN", "CHEN"), ("GUI", "SI"),
        ]
        for stem, branch in jiashen_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("WU", "WEI"))

    def test_11_kong_wang_for_jiawu_xun(self):
        """甲午旬 (序号 30-39): 空亡 = (CHEN, SI)."""
        jiawu_xun_stems = [
            ("JIA", "WU"), ("YI", "WEI"), ("BING", "SHEN"), ("DING", "YOU"),
            ("WU", "XU"), ("JI", "HAI"), ("GENG", "ZI"), ("XIN", "CHOU"),
            ("REN", "YIN"), ("GUI", "MAO"),
        ]
        for stem, branch in jiawu_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("CHEN", "SI"))

    def test_12_kong_wang_for_jiachen_xun(self):
        """甲辰旬 (序号 40-49): 空亡 = (YIN, MAO)."""
        jiachen_xun_stems = [
            ("JIA", "CHEN"), ("YI", "SI"), ("BING", "WU"), ("DING", "WEI"),
            ("WU", "SHEN"), ("JI", "YOU"), ("GENG", "XU"), ("XIN", "HAI"),
            ("REN", "ZI"), ("GUI", "CHOU"),
        ]
        for stem, branch in jiachen_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("YIN", "MAO"))

    def test_13_kong_wang_for_jiayin_xun(self):
        """甲寅旬 (序号 50-59): 空亡 = (ZI, CHOU)."""
        jiayin_xun_stems = [
            ("JIA", "YIN"), ("YI", "MAO"), ("BING", "CHEN"), ("DING", "SI"),
            ("WU", "WU"), ("JI", "WEI"), ("GENG", "SHEN"), ("XIN", "YOU"),
            ("REN", "XU"), ("GUI", "HAI"),
        ]
        for stem, branch in jiayin_xun_stems:
            with self.subTest(day=f"{stem}{branch}"):
                chart = _make_chart_with_day(stem, branch)
                self.assertEqual(chart.kong_wang, ("ZI", "CHOU"))

    def test_14_kong_wang_all_60_coverage(self):
        """60 甲子全 6 旬 6*10=60 case 全覆盖."""
        all_results = []
        for stem, branch in JIAZI_TABLE:
            chart = _make_chart_with_day(stem, branch)
            all_results.append((stem, branch, chart.kong_wang))
        # 验证 60 个结果, 每旬空亡一致
        xun_results = {}
        for stem, branch, kw in all_results:
            idx = JIAZI_INDEX[(stem, branch)]
            xun = idx // 10
            xun_results.setdefault(xun, set()).add(kw)
        # 6 旬, 每旬空亡唯一
        self.assertEqual(len(xun_results), 6)
        for xun, kws in xun_results.items():
            with self.subTest(xun=xun):
                self.assertEqual(len(kws), 1)
                self.assertEqual(next(iter(kws)), KONG_WANG_BY_XUN[xun])


class TestJiaziIndex(unittest.TestCase):
    """_get_jiazi_index O(1) 查找."""

    def test_15_jiazi_index_first_10(self):
        """序号 0-9 = 甲子旬."""
        for i, (s, b) in enumerate(JIAZI_TABLE[:10]):
            self.assertEqual(_get_jiazi_index(s, b), i)

    def test_16_jiazi_index_last_10(self):
        """序号 50-59 = 甲寅旬."""
        for i, (s, b) in enumerate(JIAZI_TABLE[50:], start=50):
            self.assertEqual(_get_jiazi_index(s, b), i)


class TestFailClosed(unittest.TestCase):
    """Fail-closed 验证."""

    def test_17_invalid_stem_raises(self):
        """非法天干应 raise KeyError."""
        with self.assertRaises(KeyError):
            _get_jiazi_index("INVALID", "ZI")

    def test_18_invalid_branch_raises(self):
        """非法地支应 raise KeyError."""
        with self.assertRaises(KeyError):
            _get_jiazi_index("JIA", "INVALID")

    def test_19_empty_raises(self):
        """空字符串应 raise KeyError."""
        with self.assertRaises(KeyError):
            _get_jiazi_index("", "ZI")
        with self.assertRaises(KeyError):
            _get_jiazi_index("JIA", "")

    def test_20_lowercase_raises(self):
        """小写应 raise KeyError (大小写敏感)."""
        with self.assertRaises(KeyError):
            _get_jiazi_index("jia", "zi")

    def test_21_p0_fndr06_no_silent_return(self):
        """P0-FNDR-06 关键: _get_jiazi_index 不返回 -1, 不静默 fail-open."""
        # 之前: idx=-1 时 calc_kong_wang 静默返 (None, None)  ← 修复
        # 现在: 直接 raise KeyError
        with self.assertRaises(KeyError):
            _get_jiazi_index("JIA", "MAO")  # JIA 不配 MAO

    def test_22_calc_kong_wang_propagates_keyerror(self):
        """calc_kong_wang 对非法干支必须 raise (不静默)."""
        # 构造非法 chart (日柱用 BING+MAO, BING 不配 MAO)
        chart = BaziChart(
            year_pillar=Pillar("JIA", "ZI"),
            month_pillar=Pillar("YI", "CHOU"),
            day_pillar=Pillar("BING", "MAO"),   # 非法
            hour_pillar=Pillar("DING", "MAO"),  # 非法
            day_master="BING",
            luck_pillars=[],
            gender="male",
        )
        with self.assertRaises(KeyError):
            calc_kong_wang(chart)


class TestEvidence(unittest.TestCase):
    """Evidence 元数据."""

    def test_23_kong_wang_evidence_id_present(self):
        """KONG_WANG 必须在 EVIDENCE_IDS 中标注."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        self.assertIn("KONG_WANG", EVIDENCE_IDS)
        self.assertTrue(EVIDENCE_IDS["KONG_WANG"])

    def test_24_jiazi_table_evidence_id_present(self):
        """JIAZI_TABLE 必须在 EVIDENCE_IDS 中标注."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        self.assertIn("JIAZI_TABLE", EVIDENCE_IDS)
        self.assertTrue(EVIDENCE_IDS["JIAZI_TABLE"])


if __name__ == "__main__":
    unittest.main()
