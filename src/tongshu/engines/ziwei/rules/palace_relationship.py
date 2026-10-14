"""Z77: PalaceRelationship——三方四正机器可执行事实层。

抽象宫位关系，规则层不再各自手写"对宫""三合"判断。

关系类型：
- SAME_PALACE: 同宫
- OPPOSITE: 对宫（六冲，相差6位）
- TRINE_1: 三合前位（相差4位）
- TRINE_2: 三合后位（相差8位）
- THREE_SQUARE_FOUR: 三方四正（= 本宫+对宫+两个三合宫，共4宫）

12地支固定顺序：子丑寅卯辰巳午未申酉戌亥

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：可删/收敛 —— 三方四正事实层，与 ZiweiPalaceResolver.resolve_sanfang_sizheng 及 combinations._triple_of 重复
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

# 12地支固定顺序（紫微斗数排盘固定）
BRANCH_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 关系类型
SAME_PALACE = "SAME_PALACE"
OPPOSITE = "OPPOSITE"
TRINE_1 = "TRINE_1"   # 三合前位（+4）
TRINE_2 = "TRINE_2"   # 三合后位（+8）


def _idx(branch: str) -> int:
    return BRANCH_ORDER.index(branch)


def relation(a_branch: str, b_branch: str) -> str:
    """返回两宫地支关系。"""
    if a_branch == b_branch:
        return SAME_PALACE
    d = (_idx(b_branch) - _idx(a_branch)) % 12
    if d == 6:
        return OPPOSITE
    if d == 4:
        return TRINE_1
    if d == 8:
        return TRINE_2
    return "OTHER"


def three_square_four(branch: str) -> dict:
    """返回某宫的三方四正四宫地支。

    本宫 + 对宫 + 三合前位 + 三合后位
    """
    i = _idx(branch)
    return {
        "self": branch,
        "opposite": BRANCH_ORDER[(i + 6) % 12],
        "trine_1": BRANCH_ORDER[(i + 4) % 12],
        "trine_2": BRANCH_ORDER[(i + 8) % 12],
    }


def in_three_square_four(center_branch: str, target_branch: str) -> bool:
    """target 是否在 center 的三方四正内。"""
    tsf = three_square_four(center_branch)
    return target_branch in (tsf["self"], tsf["opposite"], tsf["trine_1"], tsf["trine_2"])
