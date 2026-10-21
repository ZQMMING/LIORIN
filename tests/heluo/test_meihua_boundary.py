# -*- coding: utf-8 -*-
"""梅花易数 E3 Boundary 测试 — 边界条件验证."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from tongshu.engines.meihua import cast_by_time, cast_by_numbers, MeihuaResult, XIANTIAN_NUM


class TestNumberBoundary:
    """起卦数字边界测试."""

    def test_min_numbers(self):
        """最小数字 (1,1) → 乾为天，动爻2."""
        r = cast_by_numbers(1, 1)
        assert r.ben_gua == "乾为天"
        assert r.dong_yao_1based == 2  # (1+1)%6=2
        assert r.upper == "乾"
        assert r.lower == "乾"

    def test_max_numbers(self):
        """最大数字 (8,8) → 坤为地，动爻4."""
        r = cast_by_numbers(8, 8)
        assert r.ben_gua == "坤为地"
        assert r.dong_yao_1based == 4  # (8+8)%6=4
        assert r.upper == "坤"
        assert r.lower == "坤"

    def test_cross_boundary_1_8(self):
        """跨边界 (1,8) → 天地否."""
        r = cast_by_numbers(1, 8)
        assert r.ben_gua == "天地否"
        assert r.dong_yao_1based == 3  # (1+8)%6=3

    def test_cross_boundary_8_1(self):
        """跨边界 (8,1) → 地天泰."""
        r = cast_by_numbers(8, 1)
        assert r.ben_gua == "地天泰"
        assert r.dong_yao_1based == 3  # (8+1)%6=3

    def test_all_64_combinations_valid(self):
        """所有64组数字组合产生有效卦."""
        from src.tongshu.engines.yi.core import SIXTY_FOUR_MAP
        for u in range(1, 9):
            for l in range(1, 9):
                r = cast_by_numbers(u, l)
                assert r.ben_gua in SIXTY_FOUR_MAP.values(), f"({u},{l})"
                assert r.bian_gua in SIXTY_FOUR_MAP.values(), f"({u},{l})"
                assert 1 <= r.dong_yao_1based <= 6, f"({u},{l})"


class TestTimeBoundary:
    """时间起卦边界测试."""

    def test_zi_hour_23(self):
        """子时23点 → shichen=1."""
        r = cast_by_time(2021, 1, 1, 23)
        assert r.dong_yao_1based == 5  # year_zhi=2, month=1, day=1, shichen=1, total=5
        assert r.ben_gua == "雷风恒"

    def test_zi_hour_0(self):
        """子时0点 → shichen=1."""
        r = cast_by_time(2021, 1, 1, 0)
        assert r.dong_yao_1based == 5  # 与23点相同
        assert r.ben_gua == "雷风恒"

    def test_chou_hour_1_2(self):
        """丑时1-2点 → shichen=2."""
        r1 = cast_by_time(2021, 1, 1, 1)
        r2 = cast_by_time(2021, 1, 1, 2)
        assert r1.dong_yao_1based == 6  # total=6, 6%6=0→6
        assert r2.dong_yao_1based == 6
        assert r1.ben_gua == "雷水解"
        assert r2.ben_gua == "雷水解"

    def test_yin_hour_3_4(self):
        """寅时3-4点 → shichen=3."""
        r = cast_by_time(2021, 1, 1, 3)
        assert r.dong_yao_1based == 1  # total=6+3=9? Let me verify
        # year_zhi=2, month=1, day=1, shichen=3, total=7, 7%6=1
        assert r.ben_gua == "雷山小过"

    def test_wu_hour_12(self):
        """午时12点 → shichen=7."""
        r = cast_by_time(2021, 1, 1, 12)
        assert r.dong_yao_1based == 5  # total=2+1+1+7=11, 11%6=5
        assert r.ben_gua == "雷火丰"

    def test_all_24_hours_valid(self):
        """所有24小时产生有效结果."""
        for hour in range(24):
            r = cast_by_time(2021, 1, 1, hour)
            assert isinstance(r, MeihuaResult)
            assert 1 <= r.dong_yao_1based <= 6
            assert r.ben_gua
            assert r.upper in {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"}
            assert r.lower in {"乾", "兑", "离", "震", "巽", "坎", "艮", "坤"}


class TestDongYaoBoundary:
    """动爻边界测试（余数0→6）."""

    def test_remainder_zero_time(self):
        """时间起卦 sum%6==0 → dong_yao=6."""
        # 2021-01-01 01:00: year_zhi=2, month=1, day=1, shichen=2, total=6
        r = cast_by_time(2021, 1, 1, 1)
        assert r.dong_yao_1based == 6
        assert r.dong_yao == 5  # 0-based index

    def test_remainder_zero_numbers(self):
        """数字起卦 sum%6==0 → dong_yao=6."""
        # (3,3): sum=6, 6%6=0→6
        r = cast_by_numbers(3, 3)
        assert r.dong_yao_1based == 6
        assert r.dong_yao == 5

    def test_all_dong_yao_values_covered(self):
        """所有6个动爻值都能被触发."""
        targets = {1, 2, 3, 4, 5, 6}
        found = set()
        # 遍历足够多的组合来覆盖所有动爻值
        for u in range(1, 9):
            for l in range(1, 9):
                r = cast_by_numbers(u, l)
                found.add(r.dong_yao_1based)
                if len(found) == 6:
                    break
            if len(found) == 6:
                break
        assert found == targets

    def test_dong_yao_6_flips_top_line(self):
        """动爻6 → 改变最上面一爻（index 5）."""
        r = cast_by_numbers(3, 3)  # dong_yao=6
        assert r.dong_yao == 5  # 0-based
        # 变卦应与本卦仅在index 5处不同
        diff = sum(1 for a, b in zip(r.lines, r.bian_lines) if a != b)
        assert diff == 1
        assert r.bian_lines[5] != r.lines[5]


class TestTiYongBoundary:
    """体用边界测试."""

    def test_ti_yong_same_trigram(self):
        """上下同卦 → 体用相同 → 比和."""
        r = cast_by_numbers(1, 1)  # 乾为天
        assert r.ti == r.yong
        assert r.ti_yong_relation == "比和"

    def test_ti_yong_different_trigrams(self):
        """上下异卦 → 体用不同."""
        r = cast_by_numbers(1, 2)  # 乾上兑下
        assert r.ti != r.yong or r.ti_yong_relation != "比和"

    def test_dong_yao_below_3_ti_is_upper(self):
        """动爻在1-3爻 → 上卦为体."""
        r = cast_by_numbers(1, 1)  # dong_yao=2
        assert r.dong_yao_1based == 2
        assert r.ti == r.upper

    def test_dong_yao_above_3_ti_is_lower(self):
        """动爻在4-6爻 → 下卦为体."""
        r = cast_by_numbers(3, 3)  # dong_yao=6
        assert r.dong_yao_1based == 6
        assert r.ti == r.lower


class TestBianHuBoundary:
    """变卦/互卦边界测试."""

    def test_bian_gua_always_different(self):
        """变卦应与本卦至少有一爻不同."""
        r = cast_by_numbers(1, 1)
        assert r.bian_lines != r.lines

    def test_hu_gua_always_valid(self):
        """互卦始终有效."""
        for u in range(1, 9):
            for l in range(1, 9):
                r = cast_by_numbers(u, l)
                assert r.hu_gua
                assert r.hu_upper in XIANTIAN_NUM.values()
                assert r.hu_lower in XIANTIAN_NUM.values()

    def test_cuo_gua_valid(self):
        """错卦始终有效."""
        for u in range(1, 9):
            for l in range(1, 9):
                r = cast_by_numbers(u, l)
                assert r.cuo_gua

    def test_zong_gua_valid(self):
        """综卦始终有效."""
        for u in range(1, 9):
            for l in range(1, 9):
                r = cast_by_numbers(u, l)
                assert r.zong_gua


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
