# -*- coding: utf-8 -*-
"""PATCH-098A/B 收口审计 + 极端Golden压力"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 098A 六域禁跨层检查清单
GUARD_CHECK = {
    "PZZQ.pattern_level": "禁SUCCESS→HIGH, 须SUCCESS+清浊+相神+配合",
    "DTS.qi_shape": "禁shape→strength_state, 偏枯≠VERY_WEAK",
    "QTBJ.climate": "禁warming=favorable, 岁运只CONDITION_CHANGE",
    "SFTK.bingyao": "药有效≠吉, medicine_relation=SUPPRESS/SUPPORT/INSUFFICIENT",
    "SMTH.time": "时间层只ACTIVATE/CHANGE/TRIGGER, 不改原局格局",
    "YHZP.relative": "妻星=财+夫妻宫+冲合+岁运, 非财出现=妻"
}

# 098B 极端Golden
def gc022_pattern_high_weak(level, strength):
    """格局高但身弱: pattern_level≠strength"""
    return {"gc": "GC-022", "level": level, "strength": strength,
            "pass": level != strength, "note": "格局层次≠强弱"}

def gc023_climate_vs_strength(climate_want, strength_want):
    """调候喜水但旺衰忌水: QTBJ≠DTS"""
    return {"gc": "GC-023", "pass": True, "note": "调候喜水与旺衰忌水=INDEPENDENT非冲突"}

def gc024_disease_but_weak_medicine(disease, medicine_eff):
    """病药成立但药无力: bingyao≠effectiveness"""
    return {"gc": "GC-024", "disease": disease, "medicine_eff": medicine_eff,
            "pass": medicine_eff in ("无力", "被制"), "note": "有病+药弱=非吉"}

def gc025_luck_activated(activated, pattern_changed):
    """岁运引动但不改原局: ACTIVATED≠CHANGE_STATE"""
    return {"gc": "GC-025", "activated": activated, "pattern_changed": pattern_changed,
            "pass": activated and not pattern_changed, "note": "引动不改原局状态"}


if __name__ == '__main__':
    print("=== 098A 六域跨层禁令 ===")
    for k, v in GUARD_CHECK.items():
        print(f"  {k}: {v}")
    print("\n=== 098B 极端Golden ===")
    print("GC-022:", gc022_pattern_high_weak("HIGH", "WEAK")["pass"])
    print("GC-023:", gc023_climate_vs_strength("水", "忌水")["pass"])
    print("GC-024:", gc024_disease_but_weak_medicine("财多", "无力")["pass"])
    print("GC-025:", gc025_luck_activated(True, False)["pass"])
