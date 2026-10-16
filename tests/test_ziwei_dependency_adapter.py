# -*- coding: utf-8 -*-
"""iztro 大限方向依赖适配器测试（计划 2.4）。

覆盖：
- 传统规则 oracle：阳男阴女顺、阴男阳女逆（四组合 + 中文性别兼容）
- adapt：无差异直通 / 有差异修正 + 审计字段
- adapt_from_chart：生产入口的槽位重绑（slot rebinding）正确性、
  原 chart 零副作用、修正后方向自洽（幂等）
- 干支查询 / 单例 / 元信息
"""
from __future__ import annotations

import copy

import pytest

from tongshu.engines.ziwei_dependency_adapter import (
    CANONICAL_CASES,
    Direction,
    ShuntianZiweiDependencyAdapter,
    adapt_decadal_direction,
    compute_expected_direction,
    get_adapter,
    get_year_stem_branch,
    verify_canonical_cases,
)

F, R = Direction.FORWARD, Direction.REVERSE


class TestOracle:
    @pytest.mark.parametrize("name,year,gender,expected", CANONICAL_CASES)
    def test_four_canonical_combinations(self, name, year, gender, expected):
        assert compute_expected_direction(year, gender) is expected, name

    @pytest.mark.parametrize("cn,en", [("男", "male"), ("女", "female")])
    def test_chinese_gender_compat(self, cn, en):
        for year in (2024, 2025):
            assert compute_expected_direction(year, cn) == \
                compute_expected_direction(year, en)

    def test_stem_branch_lookup(self):
        assert get_year_stem_branch(1984) == ("甲", "子")
        assert get_year_stem_branch(2024) == ("甲", "辰")
        assert get_year_stem_branch(2025) == ("乙", "巳")


class TestAdapt:
    def test_no_discrepancy_passthrough(self):
        # 2024 阳男 expected FORWARD；iztro 也给 FORWARD → 不修正
        r = adapt_decadal_direction(2024, "male", F)
        assert r.has_discrepancy is False
        assert r.corrected_direction is F
        assert r.is_corrected is False

    def test_discrepancy_corrected(self):
        # iztro 错给 REVERSE → 修正为传统规则，审计留痕
        r = adapt_decadal_direction(2024, "male", R)
        assert r.has_discrepancy is True
        assert r.expected_direction is F
        assert r.corrected_direction is F
        assert r.is_corrected is True
        assert r.year_stem == "甲" and r.year_branch == "辰"

    def test_chinese_gender_on_adapt(self):
        r = adapt_decadal_direction(2024, "男", R)
        assert r.corrected_direction is F

    def test_result_serializable(self):
        d = adapt_decadal_direction(2025, "female", R).to_dict()
        assert d["iztro_direction"] == "reverse"
        assert d["corrected_direction"] == "forward"
        assert d["has_discrepancy"] is True

    def test_builtin_verification_all_match(self):
        assert all(x["match"] for x in verify_canonical_cases())


def _stub_chart_raw_reverse():
    """12宫 stub：大限原始顺序为 命→兄弟→夫妻…（REVERSE 表象）。

    命宫在丑；range 从 6 岁起每限 10 年。
    """
    # (宫名, 地支, [range起,止], 大限干)
    layout = [
        ("命宫", "丑", [6, 15], "甲"), ("兄弟", "子", [16, 25], "乙"),
        ("夫妻", "亥", [26, 35], "丙"), ("子女", "戌", [36, 45], "丁"),
        ("财帛", "酉", [46, 55], "戊"), ("疾厄", "申", [56, 65], "己"),
        ("迁移", "未", [66, 75], "庚"), ("仆役", "午", [76, 85], "辛"),
        ("福德", "巳", [86, 95], "壬"), ("田宅", "辰", [96, 105], "癸"),
        ("父母", "卯", [106, 115], "甲"), ("官禄", "寅", [116, 125], "乙"),
    ]
    return {
        "fiveElementsClass": "火六局",
        "soulPalaceBranch": "丑",
        "palaces": {
            name: {"branch": br, "decadalRange": rng,
                  "decadalStem": stem, "decadalBranch": br}
            for name, br, rng, stem in layout
        },
    }


class TestAdaptFromChart:
    def test_no_discrepancy_returns_original(self):
        # 2025 阴男 expected REVERSE；chart 已是 REVERSE 序 → 原对象直返
        chart = _stub_chart_raw_reverse()
        out, res = get_adapter().adapt_from_chart(chart, (2025, 1, 1), "male")
        assert res.has_discrepancy is False
        assert out is chart

    def test_correction_rebinds_slots(self):
        # 2024 阳男 expected FORWARD；chart 是 REVERSE 序 → 触发重绑
        chart = _stub_chart_raw_reverse()
        frozen = copy.deepcopy(chart)
        out, res = get_adapter().adapt_from_chart(chart, (2024, 5, 15), "male")
        assert res.has_discrepancy is True
        # 命宫锚点不变
        assert out["palaces"]["命宫"]["decadalRange"] == [6, 15]
        # FORWARD canonical: 丑寅卯辰巳午未申酉戌亥子
        # slot[1](16-25) 应落到地支寅的宫 = 官禄
        assert out["palaces"]["官禄"]["decadalRange"] == [16, 25]
        assert out["palaces"]["父母"]["decadalRange"] == [26, 35]  # 卯 slot[2]
        assert out["palaces"]["兄弟"]["decadalRange"] == [116, 125]  # 子 slot[11]
        # 干支随槽位一起重绑
        assert out["palaces"]["官禄"]["decadalStem"] == "乙"
        # 原 chart 零副作用（deepcopy 隔离）
        assert chart == frozen

    def test_correction_is_self_consistent(self):
        """修正后的 chart 再提取方向应为 FORWARD（幂等前提）。"""
        adapter = ShuntianZiweiDependencyAdapter(enable_audit=False)
        out, _ = adapter.adapt_from_chart(_stub_chart_raw_reverse(), (2024, 1, 1), "male")
        again, res2 = adapter.adapt_from_chart(out, (2024, 1, 1), "male")
        assert res2.has_discrepancy is False

    def test_second_extraction_directions(self):
        adapter = ShuntianZiweiDependencyAdapter(enable_audit=False)
        rev = _stub_chart_raw_reverse()
        assert adapter._extract_direction_from_chart(rev) is R
        fwd, _ = adapter.adapt_from_chart(rev, (2024, 1, 1), "male")
        assert adapter._extract_direction_from_chart(fwd) is F
        # 空宫位表 → 安全回退 FORWARD
        assert adapter._extract_direction_from_chart({"palaces": {}}) is F


class TestAdapterSurface:
    def test_singleton(self):
        assert get_adapter() is get_adapter()

    def test_metadata(self):
        m = get_adapter().get_metadata()
        assert m["dependency"] == "iztro"
        assert m["version"] == "2.6.0"
        assert m["known_discrepancy"] == "decadal_direction"
