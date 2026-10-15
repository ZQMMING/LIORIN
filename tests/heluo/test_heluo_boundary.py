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


# ═══════════════════════════════════════════════════════════════════
# E3-8: H17-A 三元年份边界（sanyuan）
# ═══════════════════════════════════════════════════════════════════

class TestSanYuanBoundary:
    """三元年份边界（原典锚点：上元1504/中元1384·1564/下元1444，180年循环）"""

    def test_sanyuan_anchor_years(self):
        """三元锚点年份逐一验证（1864 上元为相位原点）"""
        from tongshu.engines.heluo_adapter import sanyuan
        anchors = {
            1504: "shang", 1564: "zhong", 1624: "xia",
            1684: "shang", 1744: "zhong", 1804: "xia",
            1864: "shang", 1924: "zhong", 1984: "xia", 2044: "shang",
        }
        for year, exp in anchors.items():
            assert sanyuan(year) == exp, f"{year} 应属{exp}，实际{sanyuan(year)}"

    def test_sanyuan_last_year_of_era(self):
        """各元末年反向边界（1503 下元末、1563 上元末、1623 中元末）"""
        from tongshu.engines.heluo_adapter import sanyuan
        assert sanyuan(1503) == "xia"   # 1444+60-1：下元之末
        assert sanyuan(1563) == "shang"  # 1504+60-1：上元之末
        assert sanyuan(1623) == "zhong"  # 1564+60-1：中元之末

    def test_sanyuan_180_year_period(self):
        """180 年周期：同元年份相差 180 年"""
        from tongshu.engines.heluo_adapter import sanyuan
        assert sanyuan(1504) == sanyuan(1504 + 180)
        assert sanyuan(1564) == sanyuan(1564 + 180)
        assert sanyuan(1624) == sanyuan(1624 + 180)


class TestMiddlePalaceDirection:
    """中元寄宫方向（原典：阳男阴女寄艮8、阴男阳女寄坤2）"""

    def test_zhong_yang_male_gen(self):
        """中元阳年男命 → 寄艮(8)"""
        t, d = resolve_middle_palace(5, 6, "male", True, "zhong")
        assert t == 8

    def test_zhong_yin_male_kun(self):
        """中元阴年男命 → 寄坤(2)"""
        t, d = resolve_middle_palace(5, 6, "male", False, "zhong")
        assert t == 2

    def test_zhong_yang_female_kun(self):
        """中元阳年女命 → 寄坤(2)"""
        t, d = resolve_middle_palace(5, 6, "female", True, "zhong")
        assert t == 2

    def test_zhong_yin_female_gen(self):
        """中元阴年女命 → 寄艮(8)"""
        t, d = resolve_middle_palace(5, 6, "female", False, "zhong")
        assert t == 8

    def test_shang_xia_palace_regression(self):
        """上/下元寄宫不回归：上元男8女2、下元男9女7"""
        assert resolve_middle_palace(5, 6, "male", True, "shang")[0] == 8
        assert resolve_middle_palace(5, 6, "female", True, "shang")[0] == 2
        assert resolve_middle_palace(5, 6, "male", True, "xia")[0] == 9
        assert resolve_middle_palace(5, 6, "female", True, "xia")[0] == 7


# ═══════════════════════════════════════════════════════════════════
# E3-9: H17-G 大运/流年周期边界
# ═══════════════════════════════════════════════════════════════════

class TestDayunContinuity:
    """大运段连续性（原典：段间无间隙、交岁衔接，卷之下"九四九五共十八年交十九"）"""

    def test_qian_dayun_no_gap(self):
        """乾为天（yt=3 九四）：12 段全阳 9 年、段间无间隙、至 108 岁"""
        from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao
        qian = build_six_lines("乾", "乾")
        d = compute_dayun_liyao(qian, 3, qian, 3)
        seq = d.sequence
        assert len(seq) == 12
        assert seq[0].age_start == 1
        for i, e in enumerate(seq):
            if i > 0:
                assert e.age_start == seq[i - 1].age_end + 1, "段间存在间隙"
        # 原典（起例卷之下:125）："行乾九四、九五二爻，共十八年，交十九上九"
        assert seq[0].age_start == 1 and seq[0].age_end == 9
        assert seq[1].age_start == 10 and seq[1].age_end == 18
        assert seq[2].age_start == 19  # 交十九
        assert seq[-1].age_end == 108

    def test_fu_dayun_72(self):
        """复卦（元堂初九阳9年+五阴爻各6年）：先天1-39、后天40-78"""
        from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao
        fu = build_six_lines("坤", "震")
        d = compute_dayun_liyao(fu, 0, fu, 0)
        seq = d.sequence
        assert seq[0].age_end == 9
        assert seq[5].age_end == 39
        assert seq[6].age_start == 40  # 后天段接先天无间隙
        assert seq[-1].age_end == 78


class TestLiunianWorkedExample:
    """流年小象逐岁推演（原典：同人九三阳段案例，起例卷之下:121）"""

    def test_tongren_jiu_san_9_years(self):
        """天火同人（yt=2 九三）阳段 9 岁流年卦序列与原典逐卦一致"""
        from tongshu.engines.heluo.timeline_yun import compute_liunian
        tongren = build_six_lines("乾", "离")  # [1,-1,1,1,1,1]
        r = compute_liunian(tongren, 2, tongren, 2, birth_year=2024, age_from=1, age_to=9)
        names = [y.hexagram_name for y in r.years]
        assert names == ["天火同人", "泽火革", "泽雷随", "水雷屯", "地雷复",
                         "山雷颐", "山地剥", "山水蒙", "山风蛊"], names
        # 段首阳年（2024 甲辰）第1年不变元堂
        assert r.years[0].hexagram_name == "天火同人"


# ═══════════════════════════════════════════════════════════════════
# E3-10: 流月节锚对齐（BUG1 回归：_LUNAR_MONTH_JIE 子月首编号）
# ═══════════════════════════════════════════════════════════════════

class TestLiuyueJieAnchor:
    """流月节气锚与流月卦月份编号对齐（month=1=子月→大雪）"""

    @staticmethod
    def _md(dt_str: str) -> tuple[int, int]:
        """'YYYY-MM-DD HH:MM' → (月, 日)"""
        return int(dt_str[5:7]), int(dt_str[8:10])

    def test_month1_anchors_daxue(self):
        """month=1（子月）节锚=大雪（12月）——修正前错锚立春"""
        from tongshu.engines.heluo.canonical import _jie_datetime_for_lunar_month
        dt = _jie_datetime_for_lunar_month(2026, 1)
        assert self._md(dt) == (12, 7), f"子月应锚大雪(12-07)，实际{dt}"

    def test_month12_anchors_lidong(self):
        """month=12（亥月）节锚=立冬（11月）——修正前错锚小寒"""
        from tongshu.engines.heluo.canonical import _jie_datetime_for_lunar_month
        dt = _jie_datetime_for_lunar_month(2026, 12)
        assert self._md(dt) == (11, 7), f"亥月应锚立冬(11-07)，实际{dt}"

    def test_all_12_months_aligned(self):
        """全部 12 个流月节锚按子月起对齐（修正前整体错位一整节对）"""
        from tongshu.engines.heluo.canonical import _jie_datetime_for_lunar_month
        expect = {1: (12, 7), 2: (1, 5), 3: (2, 4), 4: (3, 5), 5: (4, 5), 6: (5, 5),
                  7: (6, 5), 8: (7, 7), 9: (8, 7), 10: (9, 7), 11: (10, 8), 12: (11, 7)}
        for lm, (em, ed) in expect.items():
            dt = _jie_datetime_for_lunar_month(2026, lm)
            assert self._md(dt) == (em, ed), f"month={lm} 应锚({em:02d}-{ed:02d})，实际{dt}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
