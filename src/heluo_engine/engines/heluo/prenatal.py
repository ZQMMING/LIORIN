"""河洛先天卦计算模块（Module 3）

负责：本命卦（先天卦）计算
冻结规则依据：Architecture Freeze V1.0 §2.3 模块3
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrenatalHexagram:
    """先天卦（本命卦）结果"""
    # 卦象
    upper_gua: str           # 上卦名（如"坤"）
    lower_gua: str           # 下卦名（如"乾"）
    hexagram_name: str       # 六十四卦名（如"地天泰"）
    # 洛书数
    upper_gua_num: int       # 上卦洛书数
    lower_gua_num: int       # 下卦洛书数
    # 寄宫信息
    middle_palace_resolved: bool  # 是否发生过寄宫
    palace_resolved_gua: tuple[str, str] | None  # 寄宫结果 (上, 下)


def resolve_middle_palace(
    tian_reduced: int,
    di_reduced: int,
    gender: str,
    birth_year_yang: bool,
    era: str = "zhong",
) -> tuple[int, int]:
    """
    中宫寄宫处理（HL-DISPUTE-003）
    返回 (天卦数, 地卦数)，其中归一化=5的项被替换为寄宫结果。
    
    冻结规则：
    - 上元：男寄艮(8)，女寄坤(2)
    - 中元：阳男阴女寄艮(8)，阴男阳女寄坤(2)
    - 下元：男寄离(9)，女寄兑(7)
    """
    tian_gua = tian_reduced
    di_gua = di_reduced

    if tian_reduced == 5:
        if era == "shang":
            tian_gua = 8 if gender == "male" else 2
        elif era == "zhong":
            if birth_year_yang:
                tian_gua = 8 if gender == "male" else 2
            else:
                tian_gua = 2 if gender == "male" else 8
        elif era == "xia":
            tian_gua = 9 if gender == "male" else 7

    if di_reduced == 5:
        if era == "shang":
            di_gua = 8 if gender == "male" else 2
        elif era == "zhong":
            if birth_year_yang:
                di_gua = 8 if gender == "male" else 2
            else:
                di_gua = 2 if gender == "male" else 8
        elif era == "xia":
            di_gua = 9 if gender == "male" else 7

    return tian_gua, di_gua


def determine_prenatal_hexagram(
    tian_reduced: int,
    di_reduced: int,
    gender: str,
    birth_year_yang: bool,
    era: str = "zhong",
) -> PrenatalHexagram:
    """
    确定本命卦（先天卦）（HL-DISPUTE-002 + HL-DISPUTE-003）

    冻结规则：
    
    1. 中宫寄宫（HL-DISPUTE-003）：
       - 上元：男寄艮(8)，女寄坤(2)
       - 中元：阳男阴女寄艮(8)，阴男阳女寄坤(2)
       - 下元：男寄离(9)，女寄兑(7)

    2. 天地卦方向（HL-DISPUTE-002）：
       - 阳年男命：天数在上，地数在下
       - 阳年女命：天数在下，地数在上
       - 阴年女命：天数在上，地数在下
       - 阴年男命：天数在下，地数在上
    """
    from .numbers import LUSHU_TO_TRIGRAM_NAME, get_hexagram_name, TRIGRAM_ELEMENT, TRIGRAM_NATURE

    # 处理中宫寄宫
    tian_gua_num, di_gua_num = resolve_middle_palace(
        tian_reduced, di_reduced, gender, birth_year_yang, era
    )
    middle_resolved = (tian_reduced == 5) or (di_reduced == 5)

    # 确定上下卦位置（HL-DISPUTE-002）
    if birth_year_yang:
        # 阳命
        if gender == "male":
            upper_num, lower_num = tian_gua_num, di_gua_num  # 男：天上地下
        else:
            upper_num, lower_num = di_gua_num, tian_gua_num  # 女：地下天上
    else:
        # 阴命
        if gender == "female":
            upper_num, lower_num = tian_gua_num, di_gua_num  # 女：天上地下
        else:
            upper_num, lower_num = di_gua_num, tian_gua_num  # 男：地下天上

    upper_name = LUSHU_TO_TRIGRAM_NAME[upper_num]
    lower_name = LUSHU_TO_TRIGRAM_NAME[lower_num]
    hexagram_name = get_hexagram_name(upper_name, lower_name)

    return PrenatalHexagram(
        upper_gua=upper_name,
        lower_gua=lower_name,
        hexagram_name=hexagram_name,
        upper_gua_num=upper_num,
        lower_gua_num=lower_num,
        middle_palace_resolved=middle_resolved,
        palace_resolved_gua=(upper_name, lower_name) if middle_resolved else None,
    )
