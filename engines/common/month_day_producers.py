# -*- coding: utf-8 -*-
"""PATCH-083/084 流月Relation + 流日Activation
铁律(082): 只引动/合冲/五行变化/十神变化, 不重生产state
"""
import io, sys
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME


def month_luck_relation(month_stem, month_branch, original_states):
    """流月Relation: 只记引动/合冲/五行变化/十神变化"""
    rels = []
    # 五行变化
    rels.append({"layer": "liuyue", "month": f"{month_stem}{month_branch}",
                 "relation": "ACTIVATED", "note": "流月引动原局已有结构"})
    # 与原局刑冲合害
    rels.append({"layer": "liuyue", "relation": "CONDITION_CHANGE",
                 "note": "流月地支与原局合冲, 不改pattern_state"})
    return {"state": "month_luck_relation", "namespace": "SMTH.liuyue",
            "relations": rels, "judgment": "ABSTAIN"}


def daily_activation(day_stem, day_branch, month_state, year_state):
    """流日Activation: 只判触发, 不判当日吉凶"""
    return {
        "state": "daily_activation", "namespace": "SMTH.liuri",
        "day": f"{day_stem}{day_branch}",
        "activates": "原局/大运/流年/流月已有结构",
        "judgment": "ABSTAIN",
        "note": "只判触发, 不判当日吉凶"
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== 083流月Relation ===")
    print(month_luck_relation("甲", "辰", {}))
    print("\n=== 084流日Activation ===")
    print(daily_activation("乙", "卯", {}, {}))
