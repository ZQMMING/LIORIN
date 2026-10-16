"""层 B：爻象层（Line Symbol）

职责：从六爻数组和元堂位置解析出爻的结构关系
约束：无 AI 介入，纯逻辑计算
"""

from __future__ import annotations
from .models import LineSymbol


def analyze_line_symbol(
    lines: list[int],
    yuantang_index: int,
) -> LineSymbol:
    """分析爻的完整结构关系。纯逻辑计算，无 AI 介入。"""
    if len(lines) != 6:
        raise ValueError("lines must have 6 elements")
    
    positions = []
    for i, line in enumerate(lines):
        position_names = ['初', '二', '三', '四', '五', '上']
        line_type = '九' if line == 1 else '六'
        
        positions.append({
            "index": i,
            "name": position_names[i],
            "type": "阳" if line == 1 else "阴",
            "standard_name": f"{line_type}{position_names[i]}",
            "dang_wei": check_dang_wei(line, i),
            "zhong": check_zhong(i),
        })
    
    relations = compute_cheng_cheng_bi_ying(lines)
    
    # 元堂名称
    position_names = ['初', '二', '三', '四', '五', '上']
    line_type = '九' if lines[yuantang_index] == 1 else '六'
    if yuantang_index in (0, 5):
        yuantang_name = f'{position_names[yuantang_index]}{line_type}'
    else:
        yuantang_name = f'{line_type}{position_names[yuantang_index]}'
    
    return LineSymbol(
        lines=lines.copy(),
        positions=positions,
        cheng_cheng=relations["cheng"],
        cheng=relations["cheng_cheng"],
        bi=relations["bi"],
        ying=relations["ying"],
        yuantang=yuantang_name,
        yuantang_index=yuantang_index,
    )


def check_dang_wei(line_type: int, position: int) -> bool:
    """
    当位/失位检查。
    阳爻居阳位（初/三/五）为当位（吉）
    阴爻居阴位（二/四/上）为当位（吉）
    """
    is_yang = line_type == 1
    is_odd_position = position in (0, 2, 4)
    return is_yang == is_odd_position


def check_zhong(position: int) -> bool:
    """
    中位检查。
    二爻（下卦中位）和五爻（上卦中位）为"中"
    """
    return position in (1, 4)


def compute_cheng_cheng_bi_ying(lines: list[int]) -> dict:
    """
    承乘比应关系计算。
    - 承：阴爻在阳爻之下（阴承阳，吉）
    - 乘：阴爻在阳爻之上（阴乘阳，凶）
    - 比：相邻两爻的关系
    - 应：初/四、二/五、三/上的对应关系
    """
    result = {"cheng": [], "cheng_cheng": [], "bi": [], "ying": []}
    
    # 承乘
    for i in range(5):
        if lines[i] == -1 and lines[i+1] == 1:
            result["cheng"].append(f"{i+1}承{i+2}")
        elif lines[i] == 1 and lines[i+1] == -1:
            result["cheng_cheng"].append(f"{i+1}乘{i+2}")
    
    # 比
    for i in range(5):
        if lines[i] == lines[i+1]:
            result["bi"].append(f"{i+1}比{i+2}")
    
    # 应
    for pair in [(0, 3), (1, 4), (2, 5)]:
        if lines[pair[0]] == lines[pair[1]]:
            result["ying"].append(f"{pair[0]+1}应{pair[1]+1}")
    
    return result
