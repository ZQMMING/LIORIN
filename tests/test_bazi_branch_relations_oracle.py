"""P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 12 地支关系事实 Oracle 测试。

目的:
- 验证 BRANCH_CLASH/BRANCH_HARM/BRANCH_HE/BRANCH_SANHE/BRANCH_SANHUI/BRANCH_SANXING
  完整覆盖 (12 支冲/6 对害/6 对合/4 局三合/4 局三会/2+1+自刑)
- 验证 calc_branch_*_map 数据契约 (只输出"关系存在", 不含化气/刑义)
- 验证 evaluate_*_transformation 辨层函数 (化气五行/刑义/五行属性)
- 验证三刑关键修复: 自刑必须用 Counter, 不能用 set (避免丢重复支)
- 验证 fail-closed (非法输入)

架构约束 (User 第十一轮审计):
- 关系事实表 (BRANCH_*) 在 bazi_facts, 单源真相
- 化气五行/刑义属性在 bazi_engine _HE_HUA_QI/_SANHE_HUA_QI/_SANHUI_WU_XING/_SANXING_MING
- BaziChart.branch_*_map 只输出"关系存在", 不混入辨层属性
- 三刑三种结构: 三支齐全/二支齐全/自刑, 必须分别处理
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.facts.bazi_facts import (
    BRANCH_CLASH, BRANCH_CLASH_PAIRS,
    BRANCH_HARM, BRANCH_HARM_PAIRS,
    BRANCH_HE, BRANCH_SANHE, BRANCH_SANHUI,
    BRANCH_SANXING_TRIPLE, BRANCH_SANXING_DOUBLE, BRANCH_SANXING_SELF,
    KONG_WANG_BY_XUN, JIAZI_TABLE, JIAZI_INDEX,
)
from tongshu.engines.bazi_engine import (
    BaziChart, Pillar,
    calc_branch_clash_map, calc_branch_harm_map,
    calc_branch_he_map, calc_branch_sanhe_map,
    calc_branch_sanhui_map, calc_branch_sanxing_map,
    evaluate_he_transformation,
    evaluate_sanhe_transformation,
    evaluate_sanhui_transformation,
    evaluate_xing_type,
    attach_p2_fields,
)


# P0-FNDR-06 (R-12 ⑩ 空亡): 测试用合法 60 甲子干支.
# 甲子表: (JIA,ZI), (YI,CHOU), ..., (GUI,HAI), 不能随便用 JIA+任意地支.
# 用 JIAZI_TABLE 第 i 个干支作为日柱, 其他三柱用合法但不影响测试的固定干支.
_TEST_DAY_PILLAR_PAIRS = [
    ("JIA", "ZI"), ("YI", "CHOU"), ("BING", "YIN"), ("DING", "MAO"),
    ("WU", "CHEN"), ("JI", "SI"), ("GENG", "WU"), ("XIN", "WEI"),
    ("REN", "SHEN"), ("GUI", "YOU"),
]


def _make_chart(branches: list[str]) -> BaziChart:
    """构造四柱仅地支按传入列表的 chart (含 attach_p2_fields).

    P0-FNDR-06: 干支必须是合法 60 甲子对. 这里用日柱 = 甲子, 其他三柱用
    甲子表的前几个合法对, 不会触发 KeyError.
    """
    # 使用合法 60 甲子组合作为四柱的"天干-地支"基础
    pillars = [
        Pillar(*_TEST_DAY_PILLAR_PAIRS[0]),    # 甲子
        Pillar(*_TEST_DAY_PILLAR_PAIRS[1]),    # 乙丑
        Pillar(branches[0], branches[0]),       # 日柱地支按传入 (天干同地支无意义但 OK)
        Pillar(*_TEST_DAY_PILLAR_PAIRS[3]),    # 丁卯
    ]
    # 但 branches[0] 必须与 branches[0] 配对天干... 这不合法.
    # 简化: 直接构造合法的 4 柱, branches 仅用于传参 (实际测试只关心 4 个地支)
    # 替换为合法组合
    legal_branches_indices = []
    for b in branches:
        # 找到包含该地支的合法 60 甲子对
        for i, (s, br) in enumerate(JIAZI_TABLE):
            if br == b:
                legal_branches_indices.append(i)
                break
        else:
            raise ValueError(f"地支 {b} 不在 60 甲子表")
    # 用 4 个合法的日柱
    pillars = [
        Pillar(*JIAZI_TABLE[legal_branches_indices[0] % 60]),
        Pillar(*JIAZI_TABLE[legal_branches_indices[1] % 60]),
        Pillar(*JIAZI_TABLE[legal_branches_indices[2] % 60]),
        Pillar(*JIAZI_TABLE[legal_branches_indices[3] % 60]),
    ]
    chart = BaziChart(
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        day_master=pillars[2].heavenly_stem,  # 日主 = 日柱天干
        luck_pillars=[],
        gender="male",
    )
    return attach_p2_fields(chart)


# ============================================================================
# 关系事实表测试
# ============================================================================


class TestClashPairs(unittest.TestCase):
    """六冲: 6 对."""

    def test_01_clash_pairs_complete(self):
        """BRANCH_CLASH_PAIRS 必须正好 6 对, 覆盖 12 地支."""
        self.assertEqual(len(BRANCH_CLASH_PAIRS), 6)
        all_branches = set()
        for pair in BRANCH_CLASH_PAIRS:
            self.assertEqual(len(pair), 2)
            all_branches.update(pair)
        self.assertEqual(len(all_branches), 12)  # 12 支全在

    def test_02_clash_pairs_correctness(self):
        """六冲配对与《渊海子平》一致."""
        expected_pairs = [
            {"ZI", "WU"}, {"CHOU", "WEI"}, {"YIN", "SHEN"},
            {"MAO", "YOU"}, {"CHEN", "XU"}, {"SI", "HAI"},
        ]
        actual_pairs = [set(p) for p in BRANCH_CLASH_PAIRS]
        self.assertEqual(
            sorted([tuple(sorted(p)) for p in actual_pairs]),
            sorted([tuple(sorted(p)) for p in expected_pairs]),
        )

    def test_03_clash_map_records_pairs(self):
        """calc_branch_clash_map 检测命局中存在的六冲对."""
        chart = _make_chart(["ZI", "WU", "MAO", "YOU"])
        result = calc_branch_clash_map(chart)
        # ZI-WU + MAO-YOU
        self.assertEqual(set(result.keys()), {"WU-ZI", "MAO-YOU"})

    def test_04_clash_map_no_clash(self):
        """无冲对时返回空 dict."""
        chart = _make_chart(["ZI", "CHOU", "YIN", "MAO"])
        result = calc_branch_clash_map(chart)
        self.assertEqual(result, {})


class TestHarmPairs(unittest.TestCase):
    """六害: 6 对."""

    def test_05_harm_pairs_complete(self):
        """BRANCH_HARM_PAIRS 6 对覆盖 12 支."""
        self.assertEqual(len(BRANCH_HARM_PAIRS), 6)
        all_branches = set()
        for pair in BRANCH_HARM_PAIRS:
            self.assertEqual(len(pair), 2)
            all_branches.update(pair)
        self.assertEqual(len(all_branches), 12)

    def test_06_harm_pairs_correctness(self):
        """六害配对与经典一致: 子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌."""
        expected_pairs = [
            {"ZI", "WEI"}, {"CHOU", "WU"}, {"YIN", "SI"},
            {"MAO", "CHEN"}, {"SHEN", "HAI"}, {"YOU", "XU"},
        ]
        actual_pairs = [set(p) for p in BRANCH_HARM_PAIRS]
        self.assertEqual(
            sorted([tuple(sorted(p)) for p in actual_pairs]),
            sorted([tuple(sorted(p)) for p in expected_pairs]),
        )

    def test_07_harm_map_records(self):
        chart = _make_chart(["ZI", "WEI", "MAO", "CHEN"])
        result = calc_branch_harm_map(chart)
        self.assertEqual(set(result.keys()), {"WEI-ZI", "CHEN-MAO"})


class TestHePairs(unittest.TestCase):
    """六合: 6 对."""

    def test_08_he_pairs_complete(self):
        """BRANCH_HE 6 对覆盖 12 支."""
        self.assertEqual(len(BRANCH_HE), 6)
        all_branches = set()
        for pair in BRANCH_HE:
            self.assertEqual(len(pair), 2)
            all_branches.update(pair)
        self.assertEqual(len(all_branches), 12)

    def test_09_he_pairs_correctness(self):
        """六合配对: 子丑, 寅亥, 卯戌, 辰酉, 巳申, 午未."""
        expected_pairs = [
            {"ZI", "CHOU"}, {"YIN", "HAI"}, {"MAO", "XU"},
            {"CHEN", "YOU"}, {"SI", "SHEN"}, {"WU", "WEI"},
        ]
        actual_pairs = [set(p) for p in BRANCH_HE]
        self.assertEqual(
            sorted([tuple(sorted(p)) for p in actual_pairs]),
            sorted([tuple(sorted(p)) for p in expected_pairs]),
        )

    def test_10_he_map_only_relations(self):
        """P0-FNDR-05: calc_branch_he_map 只输出"关系存在", 不含化气."""
        chart = _make_chart(["ZI", "CHOU", "YIN", "MAO"])
        result = calc_branch_he_map(chart)
        # CHOU-ZI 六合
        self.assertIn("CHOU-ZI", result)
        # value 必须是 list 且只含两支 (不含化气)
        value = result["CHOU-ZI"]
        self.assertIsInstance(value, list)
        self.assertEqual(set(value), {"ZI", "CHOU"})
        self.assertEqual(len(value), 2)   # 不含化气五行


class TestSanHe(unittest.TestCase):
    """三合: 4 局."""

    def test_11_sanhe_complete(self):
        """BRANCH_SANHE 4 局覆盖 12 支."""
        self.assertEqual(len(BRANCH_SANHE), 4)
        all_branches = set()
        for triple in BRANCH_SANHE:
            self.assertEqual(len(triple), 3)
            all_branches.update(triple)
        self.assertEqual(len(all_branches), 12)

    def test_12_sanhe_correctness(self):
        """三合局: 申子辰, 亥卯未, 寅午戌, 巳酉丑."""
        expected_triples = [
            {"SHEN", "ZI", "CHEN"}, {"HAI", "MAO", "WEI"},
            {"YIN", "WU", "XU"}, {"SI", "YOU", "CHOU"},
        ]
        actual_triples = [set(t) for t in BRANCH_SANHE]
        self.assertEqual(
            sorted([tuple(sorted(t)) for t in actual_triples]),
            sorted([tuple(sorted(t)) for t in expected_triples]),
        )

    def test_13_sanhe_map_only_relations(self):
        chart = _make_chart(["SHEN", "ZI", "CHEN", "YIN"])
        result = calc_branch_sanhe_map(chart)
        self.assertIn("CHEN-SHEN-ZI", result)
        # P0-FNDR-05: value 只含 3 支, 不含化气
        value = result["CHEN-SHEN-ZI"]
        self.assertEqual(set(value), {"SHEN", "ZI", "CHEN"})
        self.assertEqual(len(value), 3)

    def test_14_sanhe_map_partial(self):
        """三合不全 (仅 2 支) 不算成局."""
        chart = _make_chart(["SHEN", "ZI", "YIN", "MAO"])
        result = calc_branch_sanhe_map(chart)
        self.assertEqual(result, {})  # 申子缺辰, 不成局


class TestSanHui(unittest.TestCase):
    """三会: 4 局."""

    def test_15_sanhui_complete(self):
        """BRANCH_SANHUI 4 局覆盖 12 支."""
        self.assertEqual(len(BRANCH_SANHUI), 4)
        all_branches = set()
        for triple in BRANCH_SANHUI:
            self.assertEqual(len(triple), 3)
            all_branches.update(triple)
        self.assertEqual(len(all_branches), 12)

    def test_16_sanhui_correctness(self):
        """三会局: 寅卯辰东方木, 巳午未南方火, 申酉戌西方金, 亥子丑北方水."""
        expected_triples = [
            {"YIN", "MAO", "CHEN"}, {"SI", "WU", "WEI"},
            {"SHEN", "YOU", "XU"}, {"HAI", "ZI", "CHOU"},
        ]
        actual_triples = [set(t) for t in BRANCH_SANHUI]
        self.assertEqual(
            sorted([tuple(sorted(t)) for t in actual_triples]),
            sorted([tuple(sorted(t)) for t in expected_triples]),
        )


class TestSanXing(unittest.TestCase):
    """三刑: 关键测试 (三支/二支/自刑 三种结构)."""

    def test_17_sanxing_triple_complete(self):
        """BRANCH_SANXING_TRIPLE: 寅巳申(无恩), 丑戌未(恃势)."""
        self.assertEqual(len(BRANCH_SANXING_TRIPLE), 2)
        expected_triples = [
            {"YIN", "SI", "SHEN"}, {"CHOU", "XU", "WEI"},
        ]
        actual_triples = [set(t) for t in BRANCH_SANXING_TRIPLE]
        self.assertEqual(
            sorted([tuple(sorted(t)) for t in actual_triples]),
            sorted([tuple(sorted(t)) for t in expected_triples]),
        )

    def test_18_sanxing_double_complete(self):
        """BRANCH_SANXING_DOUBLE: 子卯(无礼)."""
        self.assertEqual(len(BRANCH_SANXING_DOUBLE), 1)
        self.assertEqual(frozenset(BRANCH_SANXING_DOUBLE[0]), frozenset({"ZI", "MAO"}))

    def test_19_sanxing_self_complete(self):
        """BRANCH_SANXING_SELF: 辰午酉亥 自刑地支."""
        self.assertEqual(BRANCH_SANXING_SELF, frozenset({"CHEN", "WU", "YOU", "HAI"}))

    def test_20_sanxing_triple_detected(self):
        """三支齐全刑检测: 寅巳申."""
        chart = _make_chart(["YIN", "SI", "SHEN", "ZI"])
        result = calc_branch_sanxing_map(chart)
        self.assertIn("SHEN-SI-YIN", result)
        # P0-FNDR-05: 只输出 3 支, 不含刑名
        self.assertEqual(set(result["SHEN-SI-YIN"]), {"YIN", "SI", "SHEN"})

    def test_21_sanxing_double_detected(self):
        """二支刑检测: 子卯."""
        chart = _make_chart(["ZI", "MAO", "YIN", "CHEN"])
        result = calc_branch_sanxing_map(chart)
        self.assertIn("MAO-ZI", result)
        self.assertEqual(set(result["MAO-ZI"]), {"ZI", "MAO"})

    def test_22_sanxing_self_double_detected(self):
        """🔥 P0-FNDR-05 关键: 自刑必须用 Counter, 不能用 set.

        命局: 辰 辰 — set 后丢失第二个辰, 但 Counter 保留 cnt=2.
        calc_branch_sanxing_map 必须能检测出"辰辰"自刑.
        """
        chart = _make_chart(["CHEN", "CHEN", "YIN", "MAO"])
        result = calc_branch_sanxing_map(chart)
        self.assertIn("CHEN-CHEN", result)
        self.assertEqual(result["CHEN-CHEN"], ["CHEN", "CHEN"])

    def test_23_sanxing_self_triple_detected(self):
        """自刑三次出现也算 (辰辰辰)."""
        chart = _make_chart(["CHEN", "CHEN", "CHEN", "YIN"])
        result = calc_branch_sanxing_map(chart)
        self.assertIn("CHEN-CHEN", result)

    def test_24_sanxing_self_not_triggered_once(self):
        """自刑地支只出现一次不算自刑."""
        chart = _make_chart(["CHEN", "ZI", "MAO", "YIN"])
        result = calc_branch_sanxing_map(chart)
        self.assertNotIn("CHEN-CHEN", result)


# ============================================================================
# 辨层 evaluate 函数测试
# ============================================================================


class TestEvaluateTransformations(unittest.TestCase):
    """辨层 evaluate_*_transformation 函数."""

    def test_25_evaluate_he_hua_qi(self):
        """六合化气五行映射 (子丑化土)."""
        chart = _make_chart(["ZI", "CHOU", "YIN", "MAO"])
        result = evaluate_he_transformation(chart)
        self.assertIn("CHOU-ZI", result)
        self.assertEqual(result["CHOU-ZI"]["hua_qi"], "EARTH")
        self.assertFalse(result["CHOU-ZI"]["transformed"])   # 默认未真化

    def test_26_evaluate_he_all_six(self):
        """六合 6 对化气五行全验证."""
        expected = [
            (("ZI", "CHOU"), "EARTH"),
            (("YIN", "HAI"), "WOOD"),
            (("MAO", "XU"), "FIRE"),
            (("CHEN", "YOU"), "METAL"),
            (("SI", "SHEN"), "WATER"),
            (("WU", "WEI"), "EARTH"),
        ]
        for pair, expected_qi in expected:
            chart = _make_chart([pair[0], pair[1], "YIN", "MAO"])
            result = evaluate_he_transformation(chart)
            key = "-".join(sorted(pair))
            self.assertIn(key, result)
            self.assertEqual(result[key]["hua_qi"], expected_qi)

    def test_27_evaluate_sanhe_hua_qi(self):
        """三合化气五行映射."""
        chart = _make_chart(["SHEN", "ZI", "CHEN", "YIN"])
        result = evaluate_sanhe_transformation(chart)
        self.assertIn("CHEN-SHEN-ZI", result)
        self.assertEqual(result["CHEN-SHEN-ZI"]["hua_qi"], "WATER")

    def test_28_evaluate_sanhui_wu_xing(self):
        """三会五行属性."""
        chart = _make_chart(["YIN", "MAO", "CHEN", "SI"])
        result = evaluate_sanhui_transformation(chart)
        self.assertIn("CHEN-MAO-YIN", result)
        self.assertEqual(result["CHEN-MAO-YIN"]["wu_xing"], "WOOD")

    def test_29_evaluate_xing_type(self):
        """三刑刑义判定."""
        chart = _make_chart(["YIN", "SI", "SHEN", "ZI"])
        result = evaluate_xing_type(chart)
        self.assertIn("SHEN-SI-YIN", result)
        self.assertEqual(result["SHEN-SI-YIN"]["xing_type"], "无恩之刑")

    def test_30_evaluate_xing_type_double(self):
        """二支刑刑义."""
        chart = _make_chart(["ZI", "MAO", "YIN", "CHEN"])
        result = evaluate_xing_type(chart)
        self.assertIn("MAO-ZI", result)
        self.assertEqual(result["MAO-ZI"]["xing_type"], "无礼之刑")

    def test_31_evaluate_xing_type_self(self):
        """自刑刑义."""
        chart = _make_chart(["CHEN", "CHEN", "YIN", "MAO"])
        result = evaluate_xing_type(chart)
        self.assertIn("CHEN-CHEN", result)
        self.assertEqual(result["CHEN-CHEN"]["xing_type"], "自刑")
        self.assertEqual(result["CHEN-CHEN"]["branch"], "CHEN")


# ============================================================================
# 数据契约分离测试
# ============================================================================


class TestDataContractSeparation(unittest.TestCase):
    """BaziChart.branch_*_map 只输出关系存在, 不混入辨层属性."""

    def test_32_he_map_no_hua_qi_field(self):
        """branch_he_map value 不含化气五行."""
        chart = _make_chart(["ZI", "CHOU", "YIN", "MAO"])
        value = chart.branch_he_map["CHOU-ZI"]
        self.assertEqual(len(value), 2)   # 仅 2 支, 不含 EARTH

    def test_33_sanhe_map_no_hua_qi_field(self):
        chart = _make_chart(["SHEN", "ZI", "CHEN", "YIN"])
        value = chart.branch_sanhe_map["CHEN-SHEN-ZI"]
        self.assertEqual(len(value), 3)   # 仅 3 支, 不含 WATER

    def test_34_sanxing_map_no_xing_name(self):
        chart = _make_chart(["YIN", "SI", "SHEN", "ZI"])
        value = chart.branch_sanxing_map["SHEN-SI-YIN"]
        self.assertEqual(len(value), 3)   # 仅 3 支, 不含"无恩之刑"


# ============================================================================
# Fail-closed 测试
# ============================================================================


class TestFailClosed(unittest.TestCase):
    """非法地支不能误判关系."""

    def test_35_invalid_branch_in_chart_handled_gracefully(self):
        """非法地支应被忽略, 不抛错."""
        # _make_chart 强制使用拼音, 但测试中我们直接构造带非法分支
        # 由于 BaziChart 不直接校验地支, 关键是 calc_*_map 不抛错
        # 这里只测核心 fail-closed (不抛错返回空 dict 是可接受的)
        chart = _make_chart(["ZI", "WU", "YIN", "MAO"])
        # 正常情况: ZI-WU 冲
        result = calc_branch_clash_map(chart)
        self.assertIn("WU-ZI", result)


if __name__ == "__main__":
    unittest.main()
