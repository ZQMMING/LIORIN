# -*- coding: utf-8 -*-
"""PATCH-085~088 稳定性工程
085六亲深化/086事件marker/087规则覆盖审计/088冲突压力测试
"""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === 085 六亲深化 ===
def relative_deepen(relative_type, symbol_source, palace_source,
                     relation_to_daymaster, activated=False, condition="UNDETERMINED"):
    return {
        "state": "relative_state", "namespace": "SIX_RELATIVE",
        "relative_type": relative_type,
        "symbol_source": symbol_source,
        "palace_source": palace_source,
        "relation_to_daymaster": relation_to_daymaster,
        "activation": activated,
        "condition": condition,
        "note": "六亲深化=符号+宫位+生克+引动, 不直接断婚姻吉凶"
    }


# === 086 事件marker(符号→条件, 不预测) ===
def event_marker(event_type, inputs):
    marker = {"career_marker": "事业", "relationship_activation": "婚姻"}.get(event_type)
    return {
        "state": event_type, "namespace": "EVENT.layer",
        "marker": marker or event_type,
        "inputs": inputs,
        "judgment": "ABSTAIN",
        "note": "事件marker非预测, 不输出升职/结婚/发财"
    }


# === 088 冲突压力测试(同namespace A成功B失败) ===
def conflict_stress(rule_a_out, rule_b_out):
    if rule_a_out == rule_b_out:
        return {"state": "conflict_result", "result": "RESOLVED"}
    return {"state": "conflict_result",
            "result": "CONFLICT_UNRESOLVED",
            "forbid": ["平均", "投票", "概率"],
            "note": "同namespace相反→CONFLICT_UNRESOLVED, 不平均不投票"}


if __name__ == '__main__':
    print("=== 085六亲深化(妻) ===")
    print(relative_deepen("妻", "财星", "日支夫妻宫", "我克", activated=True, condition="SUPPORTED"))
    print("\n=== 086事件marker ===")
    print(event_marker("career_marker", ["官杀", "印", "格局", "岁运激活"]))
    print("\n=== 088冲突压力 ===")
    print("A=SUCCESS B=FAILURE:", conflict_stress("SUCCESS", "FAILURE"))
    print("A=SUPPORT B=SUPPORT:", conflict_stress("SUPPORT", "SUPPORT"))
