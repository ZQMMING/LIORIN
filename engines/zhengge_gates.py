# -*- coding: utf-8 -*-
"""正格族F0总闸+L1/L2/L3"""
import sys
sys.path.insert(0, '.')
from spec.root_qi import STEM_WUXING, BENQI


# 六冲表
LIU_CHONG = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 六合表
LIU_HE = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}


def zhengge_f0(branches):
    """
    正格族F0总闸：月令是否被冲/克且无救应

    返回：(是否通过, reason_tag)
    """
    month_branch = branches[1]

    # 检查月令是否被冲
    for i, b in enumerate(branches):
        if i == 1: continue
        if LIU_CHONG.get(month_branch) == b:
            # 被冲——检查有无合解
            has_he = False
            for b2 in branches:
                if LIU_HE.get(month_branch) == b2:
                    has_he = True
                    break
            if not has_he:
                return False, f"F0·月令{month_branch}被{b}冲无合解"

    return True, f"月令{month_branch}完好"
