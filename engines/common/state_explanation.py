# -*- coding: utf-8 -*-
"""PATCH-065 State Explanation / Trace Output Layer
铁律: 解释 ≠ 决策; 只解释已产生的state, 不重新推理
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def explain(state_pack):
    """
    075契约: 解释只消费State/Relation/Evidence, 不生产新state, 输出必带链
    state_pack: 已产生的各state(格局/成败/强弱/调候/用神/岁运)
    return: 人读解释 = 结论 + 依据链 + 限制
    """
    out = {"结论": [], "依据": [], "限制": [], "trace_chain": []}

    if state_pack.get("pattern"):
        out["结论"].append(f"格局: {state_pack['pattern']}")
        out["依据"].append("PZZQ月令专取用神, 透干会支成格")
    if state_pack.get("pattern_success"):
        out["结论"].append(f"格局成败: {state_pack['pattern_success']}")
    if state_pack.get("strength"):
        out["结论"].append(f"旺衰: {state_pack['strength']}")
        out["依据"] += ["YHZP-138-001 得时为旺/失令为衰",
                        "DTS-016-002 旺中有衰/衰中有旺",
                        "SFTK-008-001 财多身弱(若适用)"]
    if state_pack.get("climate_use"):
        out["结论"].append(f"调候用: {state_pack['climate_use']}")
        out["依据"].append("QTBJ四时寒暖燥湿, 调候用≠格局用")
    if state_pack.get("use_god"):
        out["结论"].append(f"格局用: {state_pack['use_god']}")
        out["依据"].append("PZZQ月令用神")
    if state_pack.get("luck"):
        out["结论"].append(f"岁运: {state_pack['luck']}")

    out["限制"] = [
        "非单因子判定",
        "非评分/百分比/权重模型",
        "调候用≠格局用(双用并存非冲突)",
        "解释层不重新推理, 只追溯已准入state"
    ]
    out["trace_chain"] = [
        {"statement": "格局财格透印, 印为相神辅助格局",
         "source_state": ["pattern_state", "xiangshen_state"], "relation": "SUPPORT",
         "evidence": ["PZZQ-007-004"]},
        {"statement": "失令财多身弱, 药取印比",
         "source_state": ["strength_state", "bingyao_state"], "relation": "SUPPORT",
         "evidence": ["YHZP-138-001", "SFTK-008-001"]}
    ]
    return out


if __name__ == '__main__':
    print("=== PATCH-065 解释层 ===")
    gc001 = {
        "pattern": "财格(戌月戊乙)", "pattern_success": "SUCCESS(透印)",
        "strength": "SLIGHTLY_WEAK", "climate_use": "癸(壬多降级)",
        "use_god": "财", "luck": "2024甲辰: 戊午大运, 戊财忌+甲比劫喜"
    }
    r = explain(gc001)
    for k, v in r.items():
        print(f"\n【{k}】")
        for x in v:
            print(f"  · {x}")
