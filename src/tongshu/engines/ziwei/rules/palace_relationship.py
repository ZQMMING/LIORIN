"""Z77: PalaceRelationship——三方四正机器可执行事实层。

抽象宫位关系，规则层不再各自手写"对宫""三合"判断。

关系类型：
- SAME_PALACE: 同宫
- OPPOSITE: 对宫（六冲，相差6位）
- TRINE_1: 三合前位（相差4位）
- TRINE_2: 三合后位（相差8位）

Z80-H 收敛（2026-10-15，原 Z80-G 待裁决项「可删/收敛」）：
  本模块此前自带一份 12 地支表（BRANCH_ORDER），与
  ``ziwei_palace_resolution.EARTHLY_BRANCHES`` 及
  ``ZiweiPalaceResolver.resolve_sanfang_sizheng`` 的偏移算法**重复**。
  现收敛为「复用 canonical 常量」：地支序直接引用 EARTHLY_BRANCHES，
  不再自持副本；本模块仅保留「地支级」关系判定的薄封装 API，
  宫位级三方四正仍以 ``ZiweiPalaceResolver.resolve_sanfang_sizheng``
  为唯一事实源（本模块不参与生产匹配，属抽象事实层工具）。

依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md（11 未接线模块处置）
"""
from __future__ import annotations

# 地支序：直接复用 canonical 定义（Z80-H 收敛，消除重复副本）
from ...ziwei_palace_resolution import EARTHLY_BRANCHES as BRANCH_ORDER

# 关系类型
SAME_PALACE = "SAME_PALACE"
OPPOSITE = "OPPOSITE"
TRINE_1 = "TRINE_1"   # 三合前位（+4）
TRINE_2 = "TRINE_2"   # 三合后位（+8）

# 关系类型 → 偏移量（三方四正偏移的单一事实源）
_TRINE_OFFSETS = {"trine_1": 4, "trine_2": 8, "opposite": 6}


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

    本宫 + 对宫 + 三合前位 + 三合后位（偏移复用 _TRINE_OFFSETS 单一事实源）。
    """
    i = _idx(branch)
    return {
        "self": branch,
        "opposite": BRANCH_ORDER[(i + _TRINE_OFFSETS["opposite"]) % 12],
        "trine_1": BRANCH_ORDER[(i + _TRINE_OFFSETS["trine_1"]) % 12],
        "trine_2": BRANCH_ORDER[(i + _TRINE_OFFSETS["trine_2"]) % 12],
    }


def in_three_square_four(center_branch: str, target_branch: str) -> bool:
    """target 是否在 center 的三方四正内。"""
    tsf = three_square_four(center_branch)
    return target_branch in (tsf["self"], tsf["opposite"], tsf["trine_1"], tsf["trine_2"])
