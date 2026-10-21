"""⚠️ DEPRECATED — 旧版大运实现（干支排盘思路）

已被 timeline_yun.py:compute_dayun_liyao（爻位值运）替代。
保留本文件仅作为历史参考，生产代码请勿 import 此模块。
"""
from __future__ import annotations
import warnings
warnings.warn(
    "dayu.py is deprecated. Use timeline_yun.compute_dayun_liyao instead.",
    DeprecationWarning,
    stacklevel=2,
)
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════════════════════════
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干五行
STEM_ELEMENTS = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 地支五行
BRANCH_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 卦象映射 (河图数 → 卦象)
# 上卦: 1=乾, 2=兑, 3=离, 4=震, 5=巽, 6=坎, 7=艮, 8=坤
# 下卦: 同上
TRIGRAM_NAMES = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}


# ═══════════════════════════════════════════════════════════════════
# 输入输出类型
# ═══════════════════════════════════════════════════════════════════
@dataclass
class HeluoBirthInput:
    """河洛计算输入：出生信息。"""
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str  # 'male' | 'female'
    longitude: float = 120.0
    latitude: float = 31.0
    
    @property
    def is_yang_male(self) -> bool:
        stem_idx = (self.birth_year - 4) % 10
        yang_stems = [0, 2, 4, 6, 8]  # 甲丙戊庚壬
        return stem_idx in yang_stems and self.gender == 'male'
    
    @property
    def is_yin_female(self) -> bool:
        stem_idx = (self.birth_year - 4) % 10
        yin_stems = [1, 3, 5, 7, 9]  # 乙丁己辛癸
        return stem_idx in yin_stems and self.gender == 'female'
    
    @property
    def is_shun_pai(self) -> bool:
        return self.is_yang_male or self.is_yin_female
    
    @property
    def year_stem_idx(self) -> int:
        return (self.birth_year - 4) % 10
    
    @property
    def year_branch_idx(self) -> int:
        return (self.birth_year - 4) % 12
    
    @property
    def month_stem_offset(self) -> int:
        """月干起算偏移（根据年干推算月干）。"""
        # 年干决定月干起算
        # 甲己之年丙作首，乙庚之岁戊为头
        stem_starts = {0: 2, 1: 4, 2: 0, 3: 2, 4: 4, 5: 0, 6: 2, 7: 4, 8: 0, 9: 2}
        return stem_starts.get(self.year_stem_idx, 0)
    
    @property
    def month_branch_idx(self) -> int:
        """月支索引（简化的节气月支映射）。"""
        # 简化: 以寅月为正月（立春后）
        month_map = {1: 11, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 
                     7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10}
        return month_map.get(self.birth_month, 0)


@dataclass
class DaYunEntry:
    """单步大运。"""
    step: int
    age_start: int
    age_end: int
    stem_branch: str
    hexagram: str
    trigram_upper: str
    trigram_lower: str
    element: str  # 大运五行


@dataclass
class DaYunResult:
    """大运计算结果。"""
    input: HeluoBirthInput
    is_shun_pai: bool
    qi_yun_age: int
    da_yun_sequence: List[DaYunEntry]
    warnings: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# HL-09 核心算法
# ═══════════════════════════════════════════════════════════════════
def compute_da_yun(input_data: HeluoBirthInput) -> DaYunResult:
    """
    计算大运序列。
    
    算法依据: 《河洛理数·卷之四》论大运
    规则: 阳男阴女顺排，阴男阳女逆排
    """
    warnings = []
    
    # Step 1: 计算年柱月柱
    year_ganzhi = get_ganzhi(input_data.year_stem_idx, input_data.year_branch_idx)
    month_ganzhi = get_ganzhi(
        (input_data.month_stem_offset + input_data.birth_month - 1) % 10,
        input_data.month_branch_idx
    )
    
    log.info(f"年柱: {year_ganzhi}, 月柱: {month_ganzhi}")
    
    # Step 2: 计算起运年龄
    # TODO: 需要节气数据支持精确计算
    # 简化版: 使用固定值演示
    qi_yun_age = 3  # 待实现
    
    # Step 3: 生成大运干支序列
    sequence = generate_da_yun_sequence(input_data, qi_yun_age)
    
    # Step 4: 映射卦象
    sequence = map_hexagrams(input_data, sequence)
    
    return DaYunResult(
        input=input_data,
        is_shun_pai=input_data.is_shun_pai,
        qi_yun_age=qi_yun_age,
        da_yun_sequence=sequence,
        warnings=warnings
    )


def get_ganzhi(stem_idx: int, branch_idx: int) -> str:
    """计算干支字符串。"""
    return f"{STEMS[stem_idx % 10]}{BRANCHES[branch_idx % 12]}"


def generate_da_yun_sequence(input_data: HeluoBirthInput, qi_yun_age: int) -> List[DaYunEntry]:
    """
    生成大运干支序列。
    
    算法:
    1. 从月柱开始
    2. 顺排: 天干地支各加1
    3. 逆排: 天干地支各减1
    """
    sequence = []
    
    # 起始月柱干支索引
    start_stem = (input_data.month_stem_offset + input_data.birth_month - 1) % 10
    start_branch = input_data.month_branch_idx
    
    direction = 1 if input_data.is_shun_pai else -1
    
    for step in range(10):
        age_start = qi_yun_age + step * 10
        age_end = age_start + 9
        
        stem_idx = (start_stem + direction * step) % 10
        branch_idx = (start_branch + direction * step) % 12
        
        stem_branch = get_ganzhi(stem_idx, branch_idx)
        
        # 计算大运五行（取干支五行之和）
        element = calculate_dayun_element(stem_idx, branch_idx)
        
        sequence.append(DaYunEntry(
            step=step + 1,
            age_start=age_start,
            age_end=age_end,
            stem_branch=stem_branch,
            hexagram="",  # TODO: 映射卦象
            trigram_upper="",
            trigram_lower="",
            element=element
        ))
    
    return sequence


def calculate_dayun_element(stem_idx: int, branch_idx: int) -> str:
    """计算大运五行。"""
    stem_element = STEM_ELEMENTS[STEMS[stem_idx]]
    branch_element = BRANCH_ELEMENTS[BRANCHES[branch_idx]]
    # 取天干五行作为大运主五行
    return stem_element


def map_hexagrams(input_data: HeluoBirthInput, sequence: List[DaYunEntry]) -> List[DaYunEntry]:
    """
    将大运干支映射到六十四卦。
    
    算法: 取干支河图数，转换为上下卦
    TODO: 需要完整的数→卦映射算法
    """
    for entry in sequence:
        # 简化版: 暂时留空
        pass
    return sequence


# ═══════════════════════════════════════════════════════════════════
# 测试入口
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 测试用例: 1990年5月15日12时 男性（阳男）
    test_input = HeluoBirthInput(
        birth_year=1990,
        birth_month=5,
        birth_day=15,
        birth_hour=12,
        gender="male"
    )
    
    result = compute_da_yun(test_input)
    
    print(json.dumps({
        "algorithm": "HL-09",
        "input": {
            "birth_year": result.input.birth_year,
            "gender": result.input.gender,
            "is_shun_pai": result.is_shun_pai,
        },
        "qi_yun_age": result.qi_yun_age,
        "da_yun_count": len(result.da_yun_sequence),
        "first_5_steps": [
            {
                "step": s.step,
                "age_range": f"{s.age_start}-{s.age_end}",
                "stem_branch": s.stem_branch,
                "element": s.element
            }
            for s in result.da_yun_sequence[:5]
        ]
    }, ensure_ascii=False, indent=2))
