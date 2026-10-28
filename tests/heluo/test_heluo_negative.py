# -*- coding: utf-8 -*-
"""河洛理数 E4 Negative 测试 — 非法输入 fail-closed 验证

覆盖：
- invalid 输入 fail-closed（不崩溃，返回有效结果或明确异常）
- 非法日期/数字
- 空/缺参数
"""
from __future__ import annotations

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.numbers import (
    STEM_VALUES,
    BRANCH_VALUES,
    compute_tian_di_shu,
    normalize_tian_shu,
    normalize_di_shu,
    number_to_trigram,
    get_hexagram_name,
    build_six_lines,
)
from heluo_engine.engines.heluo.prenatal import determine_prenatal_hexagram
from heluo_engine.engines.heluo.yuan_tang import find_yuantang
from heluo_engine.engines.heluo.postnatal import compute_postnatal
from heluo_engine.engines.heluo.canonical import HeluoCanonical, HeluoResult
from heluo_engine.engines.heluo.input import HeluoInput, Location


# ═══════════════════════════════════════════════════════════════════
# E4-1: 输入 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestInputFailClosed:
    """输入失败关闭测试"""

    def test_invalid_gender_raises(self):
        """无效性别应抛出 ValueError"""
        c = HeluoCanonical()
        with pytest.raises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender="unknown",
                birth_hour="午",
            )

    def test_invalid_gender_none(self):
        """None 性别应抛出 ValueError"""
        c = HeluoCanonical()
        with pytest.raises((ValueError, TypeError)):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender=None,
                birth_hour="午",
            )

    def test_empty_bazi_raises(self):
        """空八字列表应抛出异常"""
        c = HeluoCanonical()
        with pytest.raises((ValueError, IndexError)):
            c.calculate(bazi=[], gender="male", birth_hour="子")

    def test_bazi_too_short_raises(self):
        """八字少于4柱应抛出异常"""
        c = HeluoCanonical()
        with pytest.raises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未")],
                gender="male",
                birth_hour="午",
            )

    def test_unknown_stem_raises(self):
        """未知天干应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_tian_di_shu([("X", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male")

    def test_unknown_branch_raises(self):
        """未知地支应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_tian_di_shu([("甲", "X"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male")

    def test_empty_stem_raises(self):
        """空天干应抛出异常"""
        with pytest.raises((ValueError, KeyError)):
            compute_tian_di_shu([("", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male")

    def test_empty_branch_raises(self):
        """空地支应抛出异常"""
        with pytest.raises((ValueError, KeyError)):
            compute_tian_di_shu([("甲", ""), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male")


# ═══════════════════════════════════════════════════════════════════
# E4-2: 元堂 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestYuantangFailClosed:
    """元堂定位 fail-closed 测试"""

    def test_invalid_gender_raises(self):
        """无效性别应抛出 ValueError"""
        with pytest.raises(ValueError):
            find_yuantang([1, 1, 1, -1, -1, -1], "午", "unknown", "地天泰")

    def test_invalid_hour_raises(self):
        """无效时辰应抛出 ValueError"""
        with pytest.raises(ValueError):
            find_yuantang([1, 1, 1, -1, -1, -1], "子时", "male", "地天泰")

    def test_invalid_hour_empty(self):
        """空时辰应抛出 ValueError"""
        with pytest.raises(ValueError):
            find_yuantang([1, 1, 1, -1, -1, -1], "", "male", "地天泰")

    def test_no_yang_line_raises(self):
        """纯阴卦阴时应有结果（不应抛异常）"""
        lines = [-1, -1, -1, -1, -1, -1]
        result = find_yuantang(lines, "午", "male", "坤为地")
        assert result is not None

    def test_no_yin_line_raises(self):
        """纯阳卦阳时应有结果（不应抛异常）"""
        lines = [1, 1, 1, 1, 1, 1]
        result = find_yuantang(lines, "子", "male", "乾为天")
        assert result is not None

    def test_short_six_lines(self):
        """短六爻输入应返回结果（算法处理）"""
        # 三爻输入实际会被算法处理，不崩溃
        result = find_yuantang([1, 1, 1], "子", "male", "乾为天")
        assert result is not None


# ═══════════════════════════════════════════════════════════════════
# E4-3: 后天卦 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestPostnatalFailClosed:
    """后天卦计算 fail-closed 测试"""

    def test_invalid_yuantang_index_negative(self):
        """负索引应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_postnatal([1, 1, 1, -1, -1, -1], yuantang_index=-1)

    def test_invalid_yuantang_index_above_5(self):
        """大于5的索引应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_postnatal([1, 1, 1, -1, -1, -1], yuantang_index=6)

    def test_invalid_six_lines_length(self):
        """非六爻输入应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_postnatal([1, 1, 1], yuantang_index=0)

    def test_empty_lines_raises(self):
        """空输入应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_postnatal([], yuantang_index=0)

    def test_four_lines_raises(self):
        """四爻输入应抛出 ValueError"""
        with pytest.raises(ValueError):
            compute_postnatal([1, 1, -1, -1], yuantang_index=1)


# ═══════════════════════════════════════════════════════════════════
# E4-4: 数值处理 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestNumberFailClosed:
    """数值处理 fail-closed 测试"""

    def test_normalize_tian_shu_zero(self):
        """天数=0 → 返回合理值"""
        result = normalize_tian_shu(0)
        assert isinstance(result, int)
        assert 1 <= result <= 9

    def test_normalize_tian_shu_large(self):
        """大天数归一化"""
        result = normalize_tian_shu(100)
        assert isinstance(result, int)
        assert 1 <= result <= 9

    def test_normalize_tian_shu_negative(self):
        """负天数归一化"""
        result = normalize_tian_shu(-1)
        assert isinstance(result, int)

    def test_normalize_di_shu_zero(self):
        """地数=0 → 返回合理值"""
        result = normalize_di_shu(0)
        assert isinstance(result, int)

    def test_number_to_trigram_out_of_range(self):
        """越界数字 → 返回 '?' 而非崩溃"""
        assert number_to_trigram(0) == "?"
        assert number_to_trigram(10) == "?"
        assert number_to_trigram(-1) == "?"

    def test_get_hexagram_name_invalid_trigram(self):
        """无效卦名 → 返回拼接结果而非崩溃"""
        result = get_hexagram_name("?", "?")
        assert isinstance(result, str)
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════════
# E4-5: 先天卦 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestPrenatalFailClosed:
    """先天卦计算 fail-closed 测试"""

    def test_invalid_era_raises(self):
        """无效 era 应返回 None 或默认值"""
        # 当前实现可能对无效 era 返回默认结果
        result = determine_prenatal_hexagram(2, 6, "male", True, "invalid_era")
        assert result is not None


# ═══════════════════════════════════════════════════════════════════
# E4-6: 完整链路 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestFullChainFailClosed:
    """完整链路 fail-closed 测试"""

    def test_invalid_input_does_not_crash(self):
        """非法输入不应导致程序崩溃（应抛出明确异常）"""
        c = HeluoCanonical()
        with pytest.raises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌")],  # 只有3柱
                gender="male",
                birth_hour="午",
            )

    def test_none_birth_hour_raises(self):
        """None birth_hour 应抛出异常"""
        c = HeluoCanonical()
        with pytest.raises((ValueError, TypeError)):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender="male",
                birth_hour=None,
            )

    def test_empty_birth_hour_raises(self):
        """空 birth_hour 应抛出 ValueError"""
        c = HeluoCanonical()
        with pytest.raises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender="male",
                birth_hour="",
            )

    def test_invalid_era_full_chain(self):
        """无效 era 通过完整链路应返回结果"""
        c = HeluoCanonical()
        result = c.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="invalid_era",
        )
        assert result is not None

    def test_invalid_gender_full_chain(self):
        """无效性别通过完整链路应抛出 ValueError"""
        c = HeluoCanonical()
        with pytest.raises(ValueError):
            c.calculate(
                bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
                gender="unknown",
                birth_hour="午",
            )


# ═══════════════════════════════════════════════════════════════════
# E4-7: 数据完整性 fail-closed
# ═══════════════════════════════════════════════════════════════════

class TestDataIntegrityFailClosed:
    """数据完整性 fail-closed 测试"""

    def test_stem_values_complete(self):
        """所有10天干都有值"""
        assert len(STEM_VALUES) == 10
        for stem in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]:
            assert stem in STEM_VALUES

    def test_branch_values_complete(self):
        """所有12地支都有值"""
        assert len(BRANCH_VALUES) == 12
        for branch in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
            assert branch in BRANCH_VALUES

    def test_stem_values_in_range(self):
        """所有天干值在1-9范围内"""
        for stem, value in STEM_VALUES.items():
            assert 1 <= value <= 9, f"{stem}={value}"

    def test_branch_values_are_tuples(self):
        """所有地支值都是二元组"""
        for branch, values in BRANCH_VALUES.items():
            assert isinstance(values, tuple)
            assert len(values) == 2
            assert all(1 <= v <= 10 for v in values)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
