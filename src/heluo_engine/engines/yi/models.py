"""Yi Engine 共享数据模型"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

# ========== 层 A：卦象层 ==========

@dataclass(frozen=True)
class HexagramSymbol:
    """卦象符号结构"""
    # 基本标识
    name: str                    # 六十四卦名
    hexagram_number: int         # 卦序（1-64）
    sequence_position: int       # 上经/下经位置
    
    # 卦德
    upper_trigram: str           # 上卦名
    lower_trigram: str           # 下卦名
    upper_symbol: str            # 上卦符号
    lower_symbol: str            # 下卦符号
    upper_element: str           # 上卦五行
    lower_element: str           # 下卦五行
    
    # 卦关系
    cuo_gua: str                 # 错卦
    zong_gua: str                # 综卦
    hu_gua: str                  # 互卦
    
    # 体用
    ti: str                      # 体卦（下卦）
    yong: str                    # 用卦（上卦）
    ti_yong_relation: str        # 体用生克关系


# ========== 层 B：爻象层 ==========

@dataclass(frozen=True)
class LineSymbol:
    """爻象结构"""
    lines: list[int]             # 六爻（-1阴, 1阳）
    positions: list[dict]        # 每爻详细信息
    cheng_cheng: list[str]       # 承（阴承阳）
    cheng: list[str]             # 乘（阴乘阳）
    bi: list[str]                # 比（相邻爻）
    ying: list[str]              # 应（初/四等）
    yuantang: str                # 元堂名称
    yuantang_index: int          # 元堂索引


# ========== 层 C：经典层 ==========

@dataclass(frozen=True)
class ClassicalText:
    """经典原文结构"""
    hexagram_name: str
    
    # 卦辞
    gua_ci: str
    gua_ci_source: str
    
    # 彖辞
    tuan_ci: str
    tuan_ci_source: str
    
    # 大象辞
    da_xiang_ci: str
    da_xiang_ci_source: str
    
    # 爻辞（可选）
    yao_ci: str | None
    yao_ci_source: str | None
    yao_position: str | None
    
    # 小象辞（可选）
    xiao_xiang_ci: str | None
    xiao_xiang_ci_source: str | None


# ========== 层 D：象扩展层 ==========

@dataclass(frozen=True)
class ImageItem:
    """象义条目"""
    image: str                   # 象
    source: str                  # 来源
    level: int                   # 证据等级（1-5）
    description: str             # 解释
    confidence: float            # 置信度（0-1）


@dataclass(frozen=True)
class ImageExpansion:
    """象扩展结构"""
    hexagram_name: str
    level_1_classical: list[ImageItem] = field(default_factory=list)
    level_2_contextual: list[ImageItem] = field(default_factory=list)
    level_3_traditional: list[ImageItem] = field(default_factory=list)
    level_4_structural: list[ImageItem] = field(default_factory=list)
    level_5_modern: list[ImageItem] = field(default_factory=list)


# ========== LLM 介入层 ==========

@dataclass(frozen=True)
class InterpretationInput:
    """LLM 解释输入"""
    heluo_result: dict
    hexagram_symbol: HexagramSymbol
    line_symbol: LineSymbol
    classical_text: ClassicalText
    image_expansion: ImageExpansion


@dataclass(frozen=True)
class InterpretationOutput:
    """LLM 解释输出"""
    state: str
    opportunity: str
    attention: str
    suggestion: str
    source_references: list[str]
    confidence: float
