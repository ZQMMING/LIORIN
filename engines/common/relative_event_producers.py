# -*- coding: utf-8 -*-
"""PATCH-077/078 六亲Relation + 事件层
铁律: 六亲/事件只映射不预测; 接075解释契约(只消费不生产)
"""
import io, sys

# === 077 六亲 Relation ===
def six_relative_relation(relative_states):
    """六亲状态间关系, 只读关系"""
    rels = []
    for i, s in enumerate(relative_states):
        if s.get("condition") == "CONSTRAINED":
            rels.append({"relative": s.get("relative_symbols"),
                         "relation": "CONDITION_CHANGE",
                         "note": "六亲星受制, 不改人事吉凶"})
        if s.get("activated"):
            rels.append({"relative": s.get("relative_symbols"),
                         "relation": "ACTIVATED",
                         "note": "岁运引动六亲星"})
    return {"state": "six_relative_relation", "namespace": "SIX_RELATIVE",
            "relations": rels, "count": len(rels)}


# === 078 事件层(事业/婚姻/财) 只映射不预测 ===
EVENT_SYMBOL = {
    "事业": ["官杀", "格局成败"],
    "婚姻": ["男:财星", "女:官杀", "日支夫妻宫"],
    "财": ["财星", "财格"]
}


def event_symbol_map(event_type):
    """事件->符号映射, 不生成吉凶结论"""
    syms = EVENT_SYMBOL.get(event_type)
    if not syms:
        return {"state": "event_symbol", "namespace": "EVENT.layer",
                "status": "NOT_REGISTERED"}
    return {"state": "event_symbol", "namespace": "EVENT.layer",
            "event": event_type, "symbols": syms,
            "judgment": "ABSTAIN",
            "note": "事件→符号映射, 吉凶结论依赖完整六域Producer+Relation"}


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== 077六亲Relation ===")
    states = [
        {"relative_symbols": ["父", "妻星"], "condition": "SUPPORTED", "activated": False},
        {"relative_symbols": ["母"], "condition": "CONSTRAINED", "activated": True}
    ]
    print(six_relative_relation(states))
    print("\n=== 078事件符号 ===")
    for e in ["事业", "婚姻", "财"]:
        print(e, event_symbol_map(e))
