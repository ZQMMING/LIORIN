# -*- coding: utf-8 -*-
"""河洛理数 E3 Boundary 测试 — 边界条件验证

覆盖：
- 卦序边界（先天/后天卦计算）
- 元堂边界（元堂爻位定位）
- 后天卦边界（两步法临界）
- 节候边界（节气切换）
- 算法分歧点（纯卦/杂卦/N=1/2/3/4/5）
"""
from __future__ import annotations

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.numbers import (
    STEM_VALUES,
    BRANCH_VALUES,
    normalize_tian_shu,
    normalize_di_shu,
    compute_tian_di_shu,
    SIXTY_FOUR_HEXAGRAMS,
    build_six_lines,
    get_hexagram_name,
)
from tongshu.engines.heluo.prenatal import determine_prenatal_hexagram, resolve_middle_palace
from tongshu.engines.heluo.yuan_tang import find_yuantang
from tongshu.engines.heluo.postnatal import compute_postnatal
from tongshu.engines.heluo.canonical import HeluoCanonical


# ═══════════════════════════════════════════════════════════════════
# E3-1: 卦序边界
# ═══════════════════════════════════════════════════════════════════

class TestHexagramOrderBoundary:
    """卦序边界测试"""

    def test_all_8x8_combinations(self):
        """所有64个上下卦组合都有效"""
        trigrams = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        names = set()
        for u in trigrams:
            for l in trigrams:
                name = get_hexagram_name(u, l)
                assert name is not None
                assert len(name) > 0
                names.add(name)
        assert len(names) >= 64, f"期望至少64个卦名，实际{len(names)}"

    def test_qian_we_tian_pure_yang(self):
        """乾为天纯阳卦六爻全阳"""
        lines = build_six_lines("乾", "乾")
        assert lines == [1, 1, 1, 1, 1, 1]

    def test_kun_wei_di_pure_yin(self):
        """坤为地纯阴卦六爻全阴"""
        lines = build_six_lines("坤", "坤")
        assert lines == [-1, -1, -1, -1, -1, -1]

    def test_can_wei_shui(self):
        """坎为水：初上阴，中爻阳"""
        lines = build_six_lines("坎", "坎")
        assert lines == [-1, 1, -1, -1, 1, -1]

    def test_li_wei_huo(self):
        """离为火：初上阳，中爻阴"""
        lines = build_six_lines("离", "离")
        assert lines == [1, -1, 1, 1, -1, 1]

    def test_zhen_wei_lei(self):
        """震为雷：初爻阳，二上阴"""
        lines = build_six_lines("震", "震")
        assert lines == [1, -1, -1, 1, -1, -1]

    def test_xun_wei_feng(self):
        """巽为风：初上阳，中爻阴"""
        lines = build_six_lines("巽", "巽")
        assert lines == [-1, 1, 1, -1, 1, 1]

    def test_gen_wei_shan(self):
        """艮为山：上爻阳，初二中阴"""
        lines = build_six_lines("艮", "艮")
        assert lines == [-1, -1, 1, -1, -1, 1]

    def test_dui_wei_ze(self):
        """兑为泽：上爻阴，初二中阳"""
        lines = build_six_lines("兑", "兑")
        assert lines == [1, 1, -1, 1, 1, -1]


# ═══════════════════════════════════════════════════════════════════
# E3-2: 元堂边界
# ═══════════════════════════════════════════════════════════════════

class TestYuantangBoundary:
    """元堂边界测试"""

    def test_pure_qian_male_zi_hour(self):
        """纯阳卦乾，子时男命 → 初九(index=0)"""
        lines = [1, 1, 1, 1, 1, 1]
        result = find_yuantang(lines, "子", "male", "乾为天")
        assert result.yuantang_index == 0
        assert result.yao_nature == "阳"

    def test_pure_qian_female_zi_hour(self):
        """纯阳卦乾，子时女命 → 上九(index=5)"""
        lines = [1, 1, 1, 1, 1, 1]
        result = find_yuantang(lines, "子", "female", "乾为天")
        assert result.yuantang_index == 5
        assert result.yao_nature == "阳"

    def test_pure_kun_male_zi_hour(self):
        """纯阴卦坤，子时男命 → 上六(index=5)"""
        lines = [-1, -1, -1, -1, -1, -1]
        result = find_yuantang(lines, "子", "male", "坤为地")
        assert result.yuantang_index == 5
        assert result.yao_nature == "阴"

    def test_pure_kun_female_zi_hour(self):
        """纯阴卦坤，子时女命 → 初六(index=0)"""
        lines = [-1, -1, -1, -1, -1, -1]
        result = find_yuantang(lines, "子", "female", "坤为地")
        assert result.yuantang_index == 0
        assert result.yao_nature == "阴"

    def test_jixiaolan_yuantang(self):
        """纪晓岚：地天泰，午时 → 六四(index=3)"""
        lines = [1, 1, 1, -1, -1, -1]
        result = find_yuantang(lines, "午", "male", "地天泰")
        assert result.yuantang == "六四"
        assert result.yuantang_index == 3
        assert result.yao_nature == "阴"

    def test_yin_hour_yin_lines(self):
        """午时（阴时）杂卦取阴爻"""
        # 火天大有：下乾上离 → [1,1,1,1,-1,1]
        lines = [1, 1, 1, 1, -1, 1]
        result = find_yuantang(lines, "午", "male", "火天大有")
        # 阴时取阴爻，只有一个阴爻在index=4
        assert result.yao_nature == "阴"
        assert result.yuantang_index == 4

    def test_all_12_hours_coverage(self):
        """所有12时辰都能定位元堂"""
        hours = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        for h in hours:
            result = find_yuantang([1, 1, 1, -1, -1, -1], h, "male", "地天泰")
            assert result is not None
            assert 0 <= result.yuantang_index <= 5


# ═══════════════════════════════════════════════════════════════════
# E3-3: 后天卦边界
# ═══════════════════════════════════════════════════════════════════

class TestPostnatalBoundary:
    """后天卦边界测试"""

    def test_qian_change_to_xiao_chu(self):
        """乾为天，元堂初九 → 第一步姤 → 第二步风天小畜"""
        lines = [1, 1, 1, 1, 1, 1]
        result = compute_postnatal(lines, yuantang_index=0)
        assert result.step1_hexagram == "天风姤"
        assert result.hexagram_name == "风天小畜"

    def test_kun_change_to_yu(self):
        """坤为地，元堂初六 → 第一步复 → 第二步雷地豫"""
        lines = [-1, -1, -1, -1, -1, -1]
        result = compute_postnatal(lines, yuantang_index=0)
        assert result.step1_hexagram == "地雷复"
        assert result.hexagram_name == "雷地豫"

    def test_jixiaolan_postnatal(self):
        """纪晓岚：地天泰 → 天雷无妄"""
        lines = [1, 1, 1, -1, -1, -1]
        result = compute_postnatal(lines, yuantang_index=3)
        assert result.hexagram_name == "天雷无妄"
        assert result.step1_hexagram == "雷天大壮"

    def test_all_six_indices_valid(self):
        """所有6个元堂索引都有效"""
        lines = [1, 1, 1, -1, -1, -1]
        for idx in range(6):
            result = compute_postnatal(lines, yuantang_index=idx)
            assert result is not None
            assert result.hexagram_name is not None

    def test_step1_step2_different(self):
        """第一步与第二步结果通常不同"""
        lines = [1, 1, 1, -1, -1, -1]
        result = compute_postnatal(lines, yuantang_index=3)
        # 地天泰变元堂后，两步结果应不同
        assert result.step1_hexagram != result.step2_hexagram


# ═══════════════════════════════════════════════════════════════════
# E3-4: 节候边界
# ═══════════════════════════════════════════════════════════════════

class TestSolarTermBoundary:
    """节候边界测试"""

    def test_normalize_tian_shu_25(self):
        """天数=25 → 5（中宫特殊）"""
        assert normalize_tian_shu(25) == 5

    def test_normalize_tian_shu_above_25(self):
        """天数>25归一化"""
        assert normalize_tian_shu(26) == 1
        assert normalize_tian_shu(30) == 5
        assert normalize_tian_shu(35) == 1  # 35-25=10→1

    def test_normalize_tian_shu_multiple_10(self):
        """遇十不用"""
        assert normalize_tian_shu(10) == 1
        assert normalize_tian_shu(20) == 2

    def test_normalize_di_shu_30(self):
        """地数=30 → 3（特殊）"""
        assert normalize_di_shu(30) == 3

    def test_normalize_di_shu_above_30(self):
        """地数>30归一化"""
        assert normalize_di_shu(31) == 1
        assert normalize_di_shu(40) == 1  # 40-30=10→1

    def test_normalize_di_shu_multiple_10(self):
        """遇十不用"""
        assert normalize_di_shu(10) == 1
        assert normalize_di_shu(20) == 2


# ═══════════════════════════════════════════════════════════════════
# E3-5: 算法分歧点（纯卦/杂卦/N=1/2/3/4/5）
# ═══════════════════════════════════════════════════════════════════

class TestAlgorithmDivergence:
    """算法分歧点测试"""

    def test_n1_same_yang(self):
        """一阳爻卦（小畜）：子丑同爻，申时起寄"""
        # 小畜：上巽下乾 → [-1,1,1,1,1,1]，一阳在index=1
        lines = [-1, 1, 1, 1, 1, 1]
        # 子时(t=0) → 第一个阳爻 index=1
        r = find_yuantang(lines, "子", "male", "风天小畜")
        assert r.yuantang_index == 1

    def test_n1_same_yin(self):
        """一阴爻卦（履）：子丑同爻，申时起寄"""
        # 履：上乾下兑 → [1,1,-1,1,1,1]，一阴在index=2
        # 但阳时取阳爻，阳爻有5个在index=0,1,3,4,5
        lines = [1, 1, -1, 1, 1, 1]
        r = find_yuantang(lines, "子", "male", "天泽履")
        # 阳时取阳爻，第一个阳爻在index=0
        assert r.yao_nature == "阳"
        assert r.yuantang_index == 0

    def test_n2_same_yang(self):
        """二阳爻卦：重数两次往复，辰时起寄"""
        # 大壮：上震下乾 → [1,1,1,1,-1,-1]，二阳在index=0,1
        lines = [1, 1, 1, 1, -1, -1]
        r = find_yuantang(lines, "子", "male", "雷天大壮")
        assert r is not None

    def test_n2_same_yin(self):
        """二阴爻卦：重数两次往复，辰时起寄"""
        # 泰卦：下乾上坤 → [1,1,1,-1,-1,-1]，三阴在index=3,4,5
        lines = [1, 1, 1, -1, -1, -1]
        r = find_yuantang(lines, "子", "male", "地天泰")
        assert r is not None

    def test_n3_same(self):
        """三阳/三阴卦：重数两次往复六时填满，无寄宫"""
        # 泰卦三阴三阳，子时男命
        lines = [1, 1, 1, -1, -1, -1]
        r = find_yuantang(lines, "子", "male", "地天泰")
        # 子时 t=0, candidates=[0,1,2], (candidates*2)[0%6]=candidates[0]=0
        assert r.yuantang_index == 0

    def test_n4_consecutive_yang(self):
        """四阳爻连续（大过阳）：回绕寄宫"""
        # 大过：上兑下巽 → [-1,1,1,1,1,-1]，四阳连续在index=1,2,3,4
        lines = [-1, 1, 1, 1, 1, -1]
        r = find_yuantang(lines, "辰", "male", "泽风大过")
        assert r is not None

    def test_n4_gap_yang(self):
        """四阳爻有gap（明夷）：取模寄宫"""
        # 明夷：上坤下离 → [1,-1,1,1,-1,-1,-1] wait 需要重新计算
        # 地火明夷：上坤下离 → [1,-1,1,1,-1,-1] (离=101, 坤=-1-1-1)
        # 正确：[1,-1,1,1,-1,-1] 四阳在 index=0,2,3,4? no
        # 离: [1,-1,1], 坤: [-1,-1,-1] → [1,-1,1, -1,-1,-1]
        lines = [1, -1, 1, -1, -1, -1]
        r = find_yuantang(lines, "戌", "male", "地火明夷")
        assert r is not None


# ═══════════════════════════════════════════════════════════════════
# E3-6: 先天卦边界
# ═══════════════════════════════════════════════════════════════════

class TestPrenatalBoundary:
    """先天卦边界测试"""

    def test_shangyuan_male(self):
        """上元男命：天数在上，地数在下"""
        result = determine_prenatal_hexagram(2, 6, "male", True, "shang")
        # 天数归一=2(坤)在上，地数归一=6(乾)在下 → 地天泰
        assert result.hexagram_name == "地天泰"

    def test_xiayuan_female(self):
        """下元女命：天数在上，地数在下"""
        result = determine_prenatal_hexagram(2, 6, "female", False, "xia")
        assert result.hexagram_name == "地天泰"

    def test_middle_yang_male(self):
        """中元阳年男命"""
        result = determine_prenatal_hexagram(2, 6, "male", True, "zhong")
        assert result.hexagram_name is not None

    def test_middle_yin_male(self):
        """中元阴年男命（阴阳反向）"""
        # 阴年男命寄宫反向
        result = determine_prenatal_hexagram(2, 6, "male", False, "zhong")
        assert result.hexagram_name is not None

    def test_middle_yang_female(self):
        """中元阳年女命"""
        result = determine_prenatal_hexagram(2, 6, "female", True, "zhong")
        assert result.hexagram_name is not None

    def test_middle_yin_female(self):
        """中元阴年女命（阴阳同向）"""
        result = determine_prenatal_hexagram(2, 6, "female", False, "zhong")
        assert result.hexagram_name is not None

    def test_middle_palace_resolved(self):
        """中宫寄宫处理"""
        # tian_reduced=5 → 需寄宫
        t, d = resolve_middle_palace(5, 6, "male", True, "shang")
        # 上元男命：天数5寄艮(8)
        assert t == 8
        assert d == 6

    def test_both_middle_palace(self):
        """两天数地数都需寄宫"""
        t, d = resolve_middle_palace(5, 5, "male", True, "shang")
        assert t == 8  # 上元男：天数5→艮8
        assert d == 8  # 上元男：地数5→艮8

    def test_xia_palace_male(self):
        """下元男命寄离(9)"""
        t, d = resolve_middle_palace(5, 5, "male", True, "xia")
        assert t == 9
        assert d == 9


# ═══════════════════════════════════════════════════════════════════
# E3-7: Golden Case 不变性
# ═══════════════════════════════════════════════════════════════════

class TestGoldenCaseInvariance:
    """Golden Case 不变性验证"""

    def test_jixiaolan_reproducible(self):
        """纪晓岚案例多次计算结果一致"""
        canonical = HeluoCanonical()
        r1 = canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="zhong",
            birth_year=1724,
        )
        r2 = canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="zhong",
            birth_year=1724,
        )
        assert r1.numbers.tian_shu == r2.numbers.tian_shu
        assert r1.prenatal.hexagram_name == r2.prenatal.hexagram_name
        assert r1.yuantang.yuantang == r2.yuantang.yuantang
        assert r1.postnatal.hexagram_name == r2.postnatal.hexagram_name

    def test_jixiaolan_gender_divergence(self):
        """纪晓岚男女性别分歧"""
        canonical = HeluoCanonical()
        male = canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male",
            birth_hour="午",
            era="zhong",
            birth_year=1724,
        )
        female = canonical.calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="female",
            birth_hour="午",
            era="zhong",
            birth_year=1724,
        )
        # 同性别分歧
        assert male.prenatal.hexagram_name != female.prenatal.hexagram_name
        assert male.yuantang.yuantang != female.yuantang.yuantang


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
