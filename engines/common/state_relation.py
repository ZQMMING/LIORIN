# -*- coding: utf-8 -*-
"""PATCH-073 Classical State Relation Contract
输入各Producer状态 -> 输出relation_state
铁律: 不重新生产状态/不修改经典结论/无权重评分百分比
只回答: 是否支持/是否冲突/是否引动/是否改变条件
"""
import io, sys

RELATION_ENUM = ["SUPPORT", "CONFLICT", "ACTIVATED", "CONDITION_CHANGE", "INDEPENDENT", "DEPENDENCY"]


def state_relation(states):
    """
    states: 各Producer状态dict
    return: relation_state列表, 只读关系不重生产
    """
    rels = []
    # 财格 + 印相 -> SUPPORT
    if states.get("pattern") == "财格" and states.get("xiangshen") == "印":
        rels.append({"pair": ("财格", "印相"), "relation": "SUPPORT",
                     "note": "相神辅佐用神, 不改变格局结论"})
    # 病=财 药=印, 印不受制 -> SUPPORT; 印受制 -> CONDITION_CHANGE
    bing = states.get("bing")
    yao = states.get("medicine")
    if bing and yao:
        if states.get("medicine_blocked"):
            rels.append({"pair": (bing, yao), "relation": "CONDITION_CHANGE",
                         "note": "药存在但受制, 有效性降级(不修改病药结论)"})
        else:
            rels.append({"pair": (bing, yao), "relation": "SUPPORT",
                         "note": f"病={bing} 药={yao} 有效"})
    # 岁运引动格局 -> ACTIVATED
    if states.get("luck") and states.get("pattern"):
        rels.append({"pair": (states["luck"], states["pattern"]), "relation": "ACTIVATED",
                     "note": "岁运引动原局格局结构, 不直接断吉凶"})
    # 调候 vs 强弱 -> INDEPENDENT (DUAL_USE非冲突)
    if states.get("climate_use") and states.get("strength"):
        rels.append({"pair": ("climate_use", "strength"), "relation": "INDEPENDENT",
                     "note": "调候与强弱不同维度, 非冲突"})
    # DEPENDENCY: 七杀成立需食神制化条件
    if states.get("pattern") == "七杀格" and states.get("zhihua"):
        rels.append({"pair": ("七杀格", "制化条件"), "relation": "DEPENDENCY",
                     "note": "七杀成立requires制化条件, 非简单SUPPORT"})
    return {
        "state": "relation_state",
        "namespace": "RELATION.layer",
        "relations": rels,
        "guard": "不重新生产状态/不修改经典结论/无权重评分",
        "count": len(rels)
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-073 Relation Layer ===")
    gc = {"pattern": "财格", "xiangshen": "印", "bing": "财多", "medicine": "印",
          "medicine_blocked": False, "luck": "甲辰", "climate_use": "癸", "strength": "SLIGHTLY_WEAK"}
    for k, v in state_relation(gc).items():
        print(f"  {k}: {v}")
    print("\n=== 压力测试 ===")
    # Case A 格局强但身弱 -> pattern≠strength
    a = state_relation({"pattern": "财格SUCCESS", "strength": "WEAK", "climate_use": "水"})
    print("Case A 格强身弱:", [(x['pair'], x['relation']) for x in a['relations']])
    # Case B 调候喜水旺衰忌水 -> INDEPENDENT
    b = state_relation({"climate_use": "水", "strength": "WEAK"})
    print("Case B 调候vs旺衰:", [(x['pair'], x['relation']) for x in b['relations']])
    # Case C 岁运破格 -> ACTIVATED不改pattern_state
    c = state_relation({"pattern": "财格", "luck": "甲辰"})
    print("Case C 岁运引动:", [(x['pair'], x['relation']) for x in c['relations']])
    # Case D 病药与用神不同 -> 七杀制化 DEPENDENCY
    d = state_relation({"pattern": "七杀格", "zhihua": True, "use_god": "食"})
    print("Case D 七杀制化:", [(x['pair'], x['relation']) for x in d['relations']])
