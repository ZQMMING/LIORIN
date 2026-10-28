# -*- coding: utf-8 -*-
"""PATCH-034-02：旺衰边界完整覆盖（旺/强/偏强/中和/偏弱/弱/极弱）

在 RULE-034-01 基础上补全六级边界，仍无评分/权重/计数，全部经典谓词组合。
证据链同 034-01：YHZP-138-001(A) / DTS-016-002(B1) / DTS-017-001(A 中和) / SFTK-008-001(A)。

边界矩阵（无单因子触发）：
  VERY_STRONG  旺极=WANG+根极强+满盘印比+无克泄  → YHZP 旺極/DTS 旺中有衰之反面
  STRONG       旺+根强+帮身足                     → 034-01 已有
  SLIGHTLY_STRONG 旺+根中/帮身不足                → 衰旺相間偏強
  NEUTRAL      DTS 中和: 旺衰相停, 根帮克泄均衡    → DTS-017-001
  SLIGHTLY_WEAK 衰+帮身+有根(衰中有旺)            → 034-01 已有
  WEAK         衰+无帮+无根                        → 034-01 已有
  VERY_WEAK    衰+无根+无帮+财官杀攻身无救         → SFTK 弱極
  CONG         從格 → 交 special_pattern_runtime, 不進 strength_state
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def rule_034_02_strength_full(cs):
    """cs: CHART_STATE 扩展版
    字段: shuai_state/wang_state/qiang_state/support_state/root_state/
          bijie_tou(天干比劫数)/attack_state(财官杀攻身)/transformed
    """
    ev, chain = [], []

    # 從格独立：交外格 Resolver，不进 strength_state
    if cs.get("transformed") in ("CONG", "ZHUANWANG"):
        return {"strength_state": "HAND_OFF_TO_WAI_GE",
                "evidence": ["special_pattern_resolver"],
                "chain": ["從格/专旺已由外格Resolver裁决"], "note": "不进strength_state"}

    # 1. 旺極 VERY_STRONG
    if cs["wang_state"] == "WANG" and cs["root_state"] == "STRONG_ROOT" \
       and cs["support_state"] in ("SUPPORT_EXCESSIVE", "SUPPORT_PRESENT") \
       and cs.get("attack_state") in ("NONE", "WEAK_ATTACK"):
        return {"strength_state": "VERY_STRONG",
                "evidence": ["YHZP-138-001", "DTS-016-002"],
                "chain": ["WANG得时", "根极强", "印比成势", "无克泄"],
                "note": "旺極；DTS旺中有衰反向提示仍须查克泄"}

    # 2. STRONG（034-01）
    if cs["qiang_state"] == "QIANG":
        return {"strength_state": "STRONG", "evidence": ["YHZP-138-001"],
                "chain": ["無氣+遇劫双条件"], "note": "日干無氣遇劫為強"}
    if cs["wang_state"] == "WANG" and cs["root_state"] in ("STRONG_ROOT", "NORMAL_ROOT"):
        return {"strength_state": "STRONG", "evidence": ["YHZP-138-001"],
                "chain": ["WANG+根强"]}

    # 3. SLIGHTLY_STRONG：旺但根中/帮身不足
    if cs["wang_state"] == "WANG" and cs["root_state"] in ("WEAK_ROOT", "NORMAL_ROOT"):
        return {"strength_state": "SLIGHTLY_STRONG",
                "evidence": ["YHZP-138-001", "DTS-016-002"],
                "chain": ["WANG得时", "根不極", "衰旺相間偏強"],
                "note": "旺而根不極，偏強非極強"}

    # 4. NEUTRAL：DTS 中和
    if cs["wang_state"] == "PING" and cs["root_state"] in ("NORMAL_ROOT", "WEAK_ROOT") \
       and cs["support_state"] == "SUPPORT_PRESENT":
        return {"strength_state": "NEUTRAL",
                "evidence": ["DTS-017-001", "YHZP-138-001"],
                "chain": ["DTS中和: 旺衰相停", "根幫克泄均衡"],
                "note": "中和，非強非弱"}

    # 5. SLIGHTLY_WEAK（034-01）
    if cs["shuai_state"] == "SHUAI" and cs["support_state"] == "SUPPORT_PRESENT" \
       and cs["root_state"] in ("WEAK_ROOT", "NORMAL_ROOT", "STRONG_ROOT"):
        return {"strength_state": "SLIGHTLY_WEAK",
                "evidence": ["YHZP-138-001", "SFTK-008-001", "DTS-016-002"],
                "chain": ["shuai=SHUAI", "印比帮身", "有根", "衰中有旺→不极弱"],
                "note": "失令+帮身+有根→偏弱非极弱"}

    # 6. VERY_WEAK：衰+无根+无帮+财官杀攻身无救（先于WEAK，攻身者加重）
    if cs["shuai_state"] == "SHUAI" and cs["support_state"] in ("NONE", "UNKNOWN") \
       and cs["root_state"] in ("NO_ROOT", "UNKNOWN") \
       and cs.get("attack_state") == "STRONG_ATTACK":
        return {"strength_state": "VERY_WEAK",
                "evidence": ["YHZP-138-001", "SFTK-008-001"],
                "chain": ["shuai=SHUAI", "无根", "无帮", "财官杀攻身无救"],
                "note": "弱極；若無克泄反歸WEAK"}

    # 7. WEAK（034-01）
    if cs["shuai_state"] == "SHUAI" and cs["support_state"] in ("NONE", "UNKNOWN") \
       and cs["root_state"] in ("NO_ROOT", "UNKNOWN"):
        return {"strength_state": "WEAK", "evidence": ["YHZP-138-001"],
                "chain": ["shuai=SHUAI", "无帮", "无根"]}

    return {"strength_state": "UNDETERMINED", "evidence": [],
            "chain": ["无授权谓词命中"], "note": "FAIL_CLOSED"}


if __name__ == "__main__":
    print("=== 034-02 旺衰边界完整覆盖自测 ===")
    cases = {
        "GC-001 1983(衰+帮+有根)": {"shuai_state": "SHUAI", "wang_state": "UNKNOWN",
            "qiang_state": "UNKNOWN", "support_state": "SUPPORT_PRESENT",
            "root_state": "WEAK_ROOT", "attack_state": "WEAK_ATTACK"},
        "旺極测试": {"shuai_state": "NOT_SHUAI", "wang_state": "WANG", "qiang_state": "UNKNOWN",
            "support_state": "SUPPORT_EXCESSIVE", "root_state": "STRONG_ROOT", "attack_state": "NONE"},
        "中和测试": {"shuai_state": "NOT_SHUAI", "wang_state": "PING", "qiang_state": "UNKNOWN",
            "support_state": "SUPPORT_PRESENT", "root_state": "NORMAL_ROOT", "attack_state": "WEAK_ATTACK"},
        "极弱测试": {"shuai_state": "SHUAI", "wang_state": "UNKNOWN", "qiang_state": "UNKNOWN",
            "support_state": "NONE", "root_state": "NO_ROOT", "attack_state": "STRONG_ATTACK"},
    }
    for name, cs in cases.items():
        r = rule_034_02_strength_full(cs)
        print(f"  {name}: {r['strength_state']}")
