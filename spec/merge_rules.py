# -*- coding: utf-8 -*-
"""三族共用合并规则配置表

结构：
  hard_gates: 命中即REJECT，不进档位计算
  promote:    满足即升档
  conditional: 条件升档/降档
  demote:     减项，叠加降档
  floor:      最低档位（不低于此）
"""

from typing import Dict, List, Tuple, Any

# 档位枚举
CONFIRMED = "CONFIRMED"
MID = "MID"
REJECT = "REJECT"

MERGE_SPEC = {
    "专旺型": {
        "hard_gates": [],  # 无真硬闸，主星成局即可
        "promote": [
            # (条件, 档位)
            ("主星成局且无破", CONFIRMED),
        ],
        "conditional": [],
        "demote": [
            ("财星超标(cai_po)", MID),
        ],
        "floor": MID,
    },
    "化气型": {
        "hard_gates": [
            ("合干不俱透", REJECT),
            ("财透两位/根深(b7=False)", REJECT),
        ],
        "promote": [
            ("b5支局全 + 无其他减项", CONFIRMED),
        ],
        "conditional": [
            # 局不全+不见龙 → REJECT（先硬条件）
            ("b5=False & b3=False", REJECT),
            # 逢龙代局：局不全但见辰 → MID
            ("b5=False & b3=True", MID),
        ],
        "demote": [
            ("争合(b1b)", MID),
            ("浊化神透干(b6=False)", MID),
            ("日主有根(b8)", MID),
        ],
        "floor": MID,  # 有减项时最低MID
    },
    "从格型": {
        "hard_gates": [
            ("日主有根未破(F0不满足)", REJECT),
        ],
        "promote": [
            ("日主无根无气 + 从神独盛无破", CONFIRMED),
        ],
        "conditional": [
            ("假从：根气微存未被尽破", MID),
        ],
        "demote": [
            ("运破格", MID),  # 大运层，预留接口
        ],
        "floor": MID,
    },
}


def apply_merge(spec_name: str, gates: Dict[str, bool], score: int = 0) -> Tuple[str, int]:
    """
    通用合并判定引擎
    返回 (confidence, score)

    语义：
    1. 先过硬闸：任一hard_gate命中 → 直接REJECT，不走floor
    2. 检查conditional条件分支
    3. 检查demote减项
    4. 检查promote升档
    5. 默认走floor
    """
    spec = MERGE_SPEC[spec_name]

    # 1. 先过硬闸：任一命中 → 直接REJECT，不受floor保护
    for gate_cond, _ in spec["hard_gates"]:
        gate_key = gate_cond.split("(")[0].strip()
        if gates.get(gate_key, False):  # True=命中硬闸（需修正：gates里True=通过闸）
            # TODO: 修正语义：gates里存的是「闸是否通过」
            # 这里临时处理：硬闸条件名=F0不满足
            pass

    # 2. 检查conditional
    for cond, conf in spec["conditional"]:
        if _eval_conditional(cond, gates):
            return (conf, score)

    # 3. 检查降档
    demoted = False
    for demote_cond, demote_conf in spec["demote"]:
        cond_key = demote_cond.split("(")[0].strip()
        if gates.get(cond_key, False):
            demoted = True

    # 4. 检查promote
    if not demoted:
        for promote_cond, conf in spec["promote"]:
            if _eval_promote(promote_cond, gates):
                return (conf, score)

    # 5. 默认floor
    return (spec["floor"], score)


def _eval_conditional(cond: str, gates: Dict[str, bool]) -> bool:
    """简化版条件求值，后续扩展"""
    if "b5=False & b3=True" in cond:
        return not gates.get("b5", True) and gates.get("b3", False)
    if "b5=False & b3=False" in cond:
        return not gates.get("b5", True) and not gates.get("b3", False)
    return False


def _eval_promote(cond: str, gates: Dict[str, bool]) -> bool:
    if "b5支局全" in cond:
        return gates.get("b5", False)
    return False
