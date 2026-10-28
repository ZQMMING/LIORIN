# -*- coding: utf-8 -*-
"""PATCH-076 六亲映射契约
铁律: 十神→六亲符号(relative_symbol), 不直接断人事吉凶
namespace=SIX_RELATIVE; 只消费ten_god, 禁strength/pattern_success/climate
"""
import io, sys

# 十神 -> 六亲符号候选(relative_symbol, 非吉凶结论)
SIX_RELATIVE_MAP = {
    # ★ V7.96b 符号名补原典别名(SMTH L3565「男取克干为子, 女取干生为息...克我者为夫」):
    #   男: 财=妻(我克者为妻) -> 增"妻"别名; 女: 官杀=夫(克我者为夫) -> 增"夫星"别名.
    #   保留原有"妻星"/"丈夫星"字样(下游若已引用不受影响).
    "男": {
        "财": ["父", "妻星", "妻"],
        "官杀": ["子女", "事业约束"],
        "印": ["母", "长辈", "学习"],
        "比劫": ["兄弟", "同辈"],
        "食伤": ["子女", "作品"]
    },
    "女": {
        "官杀": ["丈夫星", "夫星"],
        "食伤": ["子女"],
        "印": ["母", "学习"],
        "财": ["父", "资源"],
        "比劫": ["兄弟", "同辈"]
    }
}


def six_relative_producer(ten_god, gender="男", root_state="UNKNOWN",
                          constrained=False, activated=False):
    """
    十神->六亲符号+状态(presence/condition), 不生成吉凶
    """
    mp = SIX_RELATIVE_MAP.get(gender, {})
    symbols = mp.get(ten_god)
    if not symbols:
        return {"state": "six_relative_state", "namespace": "SIX_RELATIVE",
                "status": "NOT_REGISTERED", "ten_god": ten_god}
    condition = "SUPPORTED" if root_state in ("NORMAL_ROOT", "STRONG_ROOT") else ("CONSTRAINED" if constrained else "UNDETERMINED")
    return {
        "state": "six_relative_state",
        "namespace": "SIX_RELATIVE",
        "ten_god": ten_god,
        "gender": gender,
        "relative_symbols": symbols,
        "presence": "PRESENT",
        "condition": condition,
        "activated": activated,
        "note": "十神→六亲符号, 非人事吉凶结论",
        "evidence_chain": ["YHZP-062-005"]
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-076 六亲映射 ===")
    print("男命 财(父/妻星):", six_relative_producer("财", "男", "STRONG_ROOT"))
    print("女命 官杀(夫星):", six_relative_producer("官杀", "女", "NORMAL_ROOT"))
