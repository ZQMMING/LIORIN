# -*- coding: utf-8 -*-
"""PATCH-072 六域补全: PZZQ相神/SFTK病药/YHZP十神/SMTH岁运改格/QTBJ制化"""
import io, sys

# === 2. PZZQ 相神 (PZZQ-007-004) ===
XIANGSHEN = {
    "官逢财生": {"用": "官", "相": "财"},
    "财旺生官": {"用": "财", "相": "官"},
    "煞逢食制": {"用": "煞", "相": "食"},
}


def xiangsheng_producer(pattern_rel):
    p = XIANGSHEN.get(pattern_rel)
    if not p:
        return {"state": "xiangshen_state", "namespace": "PZZQ.xiangshen",
                "status": "NOT_REGISTERED", "evidence": "PZZQ-007-004"}
    return {"state": "xiangshen_state", "namespace": "PZZQ.xiangshen",
            "use": p["用"], "xiang": p["相"],
            "note": f"輔我用神者為相: {p['用']}為用, {p['相']}為相",
            "evidence_chain": ["PZZQ-007-004"]}


# === 4. SFTK 病药有效性 (SFTK-008-001) ===
def bingyao_validity(harm_god, medicine_god):
    """病=原有所害之神; 药=得一字去之"""
    if not harm_god:
        return {"state": "bingyao_state", "namespace": "SFTK.qu_yong",
                "status": "NO_DISEASE"}
    if not medicine_god:
        return {"state": "bingyao_state", "namespace": "SFTK.qu_yong",
                "status": "DISEASE_NO_MEDICINE", "disease": harm_god,
                "note": "有病無藥, 格不高"}
    return {"state": "bingyao_state", "namespace": "SFTK.qu_yong",
            "status": "DISEASE_HAS_MEDICINE", "disease": harm_god, "medicine": medicine_god,
            "note": f"有病方為貴, 病={harm_god}, 藥={medicine_god}",
            "evidence_chain": ["SFTK-008-001"]}


# === 5. YHZP 十神作用 (YHZP-062) ===
SHISHEN_ACTION = {
    "比肩": "同類扶身", "劫財": "同類奪財",
    "食神": "洩秀生財", "傷官": "洩氣傷官",
    "正財": "我克為財", "七殺": "克我為煞",
    "正官": "克我為官", "正印": "生我為印",
}


def shishen_action(god):
    a = SHISHEN_ACTION.get(god, "未註冊")
    return {"state": "shishen_action", "namespace": "YHZP.ten_god",
            "god": god, "action": a, "evidence_chain": ["YHZP-062-005"]}


# === 6. QTBJ 调候制化细化 ===
def tiaohou_zhihua(primary, over_element):
    """主用五行過旺→需制化, 不直接斷吉凶"""
    return {"state": "tiaohou_zhihua", "namespace": "QTBJ.climate_zhihua",
            "primary": primary, "over": over_element,
            "zhihua_needed": bool(over_element),
            "judgment": "ABSTAIN"}


# === 3. SMTH 岁运改变格局 ===
def luck_alter_pattern(luck_stem_branch, current_pattern):
    """岁运引动格局變化, 只標記不決斷"""
    return {"state": "pattern_luck_change", "namespace": "SMTH.luck_pattern",
            "current_pattern": current_pattern, "luck": luck_stem_branch,
            "effect": "MARKED", "judgment": "ABSTAIN"}


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PZZQ相神 ===")
    print(xiangsheng_producer("官逢财生"))
    print("=== SFTK病药 ===")
    print(bingyao_validity("财多身弱之财", "印"))
    print("=== YHZP十神 ===")
    print(shishen_action("食神"))
    print("=== SMTH岁运改格 ===")
    print(luck_alter_pattern("甲辰", "财格"))
