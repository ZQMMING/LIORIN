# -*- coding: utf-8 -*-
"""PATCH-082 时间层Consumer Contract
铁律: 大运/流年/流月/流日 只能引动/改条件/触发关系
不能重新生产 格局/旺衰/调候/用神
"""
import io, sys

TIME_CONSUMER = {
    "dayun": {"consume": ["原局状态", "格局状态"], "can": ["引动", "改条件"], "cannot": ["重算格局", "重算旺衰", "重算调候", "重算用神"]},
    "liunian": {"consume": ["大运状态", "原局状态"], "can": ["引动", "合冲", "五行变化"], "cannot": ["改pattern_state", "改strength_state"]},
    "liuyue": {"consume": ["流年状态", "大运状态", "原局状态"], "can": ["引动", "合冲", "十神变化"], "cannot": ["重生产任何state"]},
    "liuri": {"consume": ["流月状态", "流年", "大运"], "can": ["daily_activation触发"], "cannot": ["判当日吉凶"]}
}


def time_contract(layer):
    c = TIME_CONSUMER.get(layer)
    if not c:
        return {"status": "NOT_REGISTERED", "layer": layer}
    return {
        "state": "time_consumer_contract",
        "namespace": f"SMTH.{layer}",
        "can_consume": c["consume"],
        "can_do": c["can"],
        "cannot": c["cannot"],
        "note": "时间层只引动不重生产原局结论"
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-082 时间层Consumer ===")
    for layer in ["dayun", "liunian", "liuyue", "liuri"]:
        c = TIME_CONSUMER[layer]
        print(f"[{layer}] 可消费={c['consume']} | 禁止={c['cannot'][:2]}")
    print("\n铁律: 流月流日接入前必先冻结此Contract")
