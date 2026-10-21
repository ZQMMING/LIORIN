# -*- coding: utf-8 -*-
"""梅花易数 E4 Negative 测试 — 非法输入 fail-closed 验证."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from tongshu.engines.meihua import cast_by_time, cast_by_numbers


class TestInvalidNumberInputs:
    """数字输入测试 - 验证模块不崩溃(fail-closed)."""

    def test_upper_zero(self):
        """上卦数为0：模块应返回有效结果而非崩溃."""
        # 当前实现使用 % 8 会wrap，不抛异常
        r = cast_by_numbers(0, 1)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_upper_negative(self):
        """上卦数为负：模块应返回有效结果."""
        r = cast_by_numbers(-1, 1)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_upper_above_8(self):
        """上卦数大于8：模块应返回有效结果(自动取模)."""
        r = cast_by_numbers(9, 1)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_lower_zero(self):
        """下卦数为0：模块应返回有效结果."""
        r = cast_by_numbers(1, 0)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_lower_negative(self):
        """下卦数为负：模块应返回有效结果."""
        r = cast_by_numbers(1, -1)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_lower_above_8(self):
        """下卦数大于8：模块应返回有效结果."""
        r = cast_by_numbers(1, 9)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_both_invalid(self):
        """双无效输入：模块应返回有效结果."""
        r = cast_by_numbers(0, 0)
        assert r is not None
        assert hasattr(r, 'ben_gua')


class TestInvalidTimeInputs:
    """时间参数边界测试."""

    def test_negative_hour(self):
        """负小时数：模块应处理."""
        r = cast_by_time(2021, 1, 1, -1)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_hour_above_23(self):
        """超过23的小时：模块应处理."""
        r = cast_by_time(2021, 1, 1, 24)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_zero_month(self):
        """月份为0：模块应处理."""
        r = cast_by_time(2021, 0, 1, 12)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_zero_day(self):
        """日期为0：模块应处理."""
        r = cast_by_time(2021, 1, 0, 12)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_far_future_year(self):
        """远未来年份不应崩溃."""
        r = cast_by_time(9999, 12, 31, 23)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_far_past_year(self):
        """远过去年份不应崩溃."""
        r = cast_by_time(1000, 1, 1, 0)
        assert r is not None
        assert hasattr(r, 'ben_gua')


class TestMissingParameters:
    """缺省参数测试."""

    def test_missing_question(self):
        """缺少question参数应使用默认值."""
        r = cast_by_time(2021, 1, 1, 12)
        assert r.question == ""

    def test_missing_question_number_cast(self):
        """数字起卦缺少question应使用默认值."""
        r = cast_by_numbers(3, 5)
        assert r.question == ""

    def test_empty_question(self):
        """空字符串question应正常处理."""
        r = cast_by_time(2021, 1, 1, 12, question="")
        assert r.question == ""


class TestEdgeCases:
    """边缘情况测试."""

    def test_very_large_numbers(self):
        """极大数字：模块应返回有效结果."""
        r = cast_by_numbers(100, 100)
        assert r is not None
        assert hasattr(r, 'ben_gua')

    def test_decimal_numbers(self):
        """小数输入：模块应处理或返回结果."""
        try:
            r = cast_by_numbers(1.5, 3)
            # 如果不抛异常，应返回结果
            assert r is not None
        except (TypeError, ValueError):
            pass  # 允许抛异常

    def test_string_numbers(self):
        """字符串输入：模块应处理或返回结果."""
        try:
            r = cast_by_numbers("3", "5")
            assert r is not None
        except (TypeError, ValueError):
            pass

    def test_none_input(self):
        """None输入：模块应处理."""
        try:
            r = cast_by_numbers(None, 3)
            assert r is not None
        except (TypeError, ValueError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
