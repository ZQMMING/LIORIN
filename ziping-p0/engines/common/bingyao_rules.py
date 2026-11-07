# -*- coding: utf-8 -*-
"""PATCH-033：SFTK 病药规则（RULE-033-01，qu_yong_state 出值）

依据 SFTK-008-001（病藥說，A 级）：
- 「何以爲之病？原八字中原有所害之神也。何以爲之藥？如八字原有所害之字而得一字以去之之謂也」
- 「四柱純土……水日干則爲財多身弱」（底本；按五行生克应为『木日干』——木克土=财，登记异文待取证）
- 「如用財見比肩爲病，喜官殺爲藥也」
依据 SFTK-009-002（雕枯旺弱四病）：「日主太弱宜行身旺之地」
"""
import io, sys, json
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CHART = {
    "pillars": "癸亥 壬戌 乙未 壬午", "day_master_element": "WOOD", "day_master_wuxing": "木",
    "month_order": "戌", "month_benqi_wuxing": "土",
    "stems": {"年": "癸", "月": "壬", "日": "乙", "时": "壬"},
    "hidden": {"亥": ["壬", "甲"], "戌": ["戊", "辛", "丁"], "未": ["己", "丁", "乙"], "午": ["丁", "己"]},
}
ELEM_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
# 日主五行→该五行所克（财）

def rule_033_01_sftk_bingyao(c):
    dm = c["day_master_wuxing"]                       # 木
    wealth_wuxing = KE[dm]                            # 财=土
    month_benqi = c["month_benqi_wuxing"]             # 月令本气五行
    # 病1（主）：财多身弱——月令本气=财（日主所克）→ 财星当令
    wealth_dangling = (month_benqi == wealth_wuxing)
    # 病2（次）：用财见比肩为病（SFTK-008-001）——比劫透（日干自身≠比肩）
    stems = list(c["stems"].values())                          # [年,月,日,时]
    bijie_tou = sum(1 for i, s in enumerate(stems) if i != 2 and ELEM_WUXING[s] == dm)
    # 药：SFTK-009-002 日主太弱宜行身旺之地 → 印（生身）/比劫（帮身）
    yin_count = sum(1 for s in stems if ELEM_WUXING[s] in ("水",)) if dm == "木" else 0  # 木日主印=水
    if wealth_dangling:
        bing = "财多身弱" if True else "财星当令"
        yao = f"印比帮身（{c['pillars'].split()[0]}癸透+月壬+时壬，印透3已在局中）" if yin_count >= 3 else "印比帮身（印透不足，宜行身旺之地）"
        return {
            "rule_id": "RULE-033-01", "namespace": "SFTK.qu_yong",
            "qu_yong_state": "DETERMINED(病=财多身弱,药=印比帮身)",
            "bing": bing, "yao": yao,
            "wealth_dangling": True, "bijie_tou": bijie_tou,
            "secondary": "用財見比肩爲病→喜官殺爲藥（SFTK-008-001；本命比劫仅支藏为日主之根，未成夺财重病，登记次病）" if bijie_tou == 0 else "比肩透，夺财之病成立",
            "text_variant": "SFTK-008-001 底本『水日干則爲財多身弱』疑为『木日干』（木克土=财，水日干土=杀见前句『殺重身輕』）；本规则按木日干采信，登记异文待 Human 取证裁决",
            "evidence": ["SFTK-008-001", "SFTK-009-002"],
        }
    return {"qu_yong_state": "UNDETERMINED", "note": "月令本气非财，病药不按财多身弱论"}


if __name__ == "__main__":
    print("==== PATCH-033：SFTK 病药（RULE-033-01） ====")
    r = rule_033_01_sftk_bingyao(CHART)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("\n==== 1983-1103 病药解读 ====")
    print(f"  病：月令戌土=乙木之财，财星当令；日主失令弱根 → 财多身弱")
    print(f"  药：印比帮身——印透三（癸壬壬）已在局中（SFTK-009-002 日主太弱宜行身旺之地）")
    print(f"  次病：比劫仅支藏（亥甲/未乙）为日主之根，未成夺财重病（SFTK-008-001 用财见比肩喜官杀，登记）")
    print(f"  异文：底本『水日干財多身弱』→按五行应为『木日干』，登记待取证")
