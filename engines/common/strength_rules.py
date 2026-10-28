# -*- coding: utf-8 -*-
"""PATCH-034：strength_state 综合裁决（RULE-034-01，COMPOSITE 授权）

024 契约：strength=COMPOSITE（多经典证据链），无单经典直产，authorized producers 0→1。
本规则用「经典谓词组合」裁决，非评分/权重/计数（FORBIDDEN-13 禁 factor_count→strength）。

证据链：
- YHZP-138-001（A）：得時俱為旺論／失令便作衰看／日干無氣遇劫為強
- SFTK-008-001（A）：財多身弱（木日干四柱土重）
- DTS-016-002（B1 辅助）：旺中有衰／衰中有旺者存
- DTS-017-001/002（A+B1，RULE-022C-05 中和原则）

裁决谓词（无单因子触发）：
1. qiang=強（無氣+遇劫，双条件）→ STRONG/SLIGHTLY_STRONG 候选
2. wang=旺 且 根强 且 帮身充足 → STRONG 方向候选
3. shuai=SHUAI 且 帮身（印比）充足 且 有根 → 「衰中有旺」→ SLIGHTLY_WEAK
4. shuai=SHUAI 且 无帮身 且 无根 → WEAK
5. 病药=財多身弱（SFTK A）→ 佐证身弱方向
6. 其他 → UNDETERMINED
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1983-1103 已冻结状态（024/022B/033 输出）
CHART_STATE = {
    "shuai_state": "SHUAI",          # CAND-SHUAI-001 YHZP 失令
    "wang_state": "UNKNOWN",         # CAND-WANG-001 ABSTAIN（失令非旺）
    "qiang_state": "UNKNOWN",        # CAND-QIANG-001 ABSTAIN（有印生非無氣，且无比劫透）
    "support_state": "SUPPORT_PRESENT",  # 印透三
    "root_state": "WEAK_ROOT",       # 亥甲长生+未乙余气
    "bingyao": "財多身弱",           # RULE-033-01 SFTK
    "bijie_tou": 0,                  # 天干无比劫透
}


def rule_034_01_strength(cs):
    evidence, chain = [], []
    # 1. qiang 触发 → 强方向（1983 不触发：有印生非無氣，无比劫透）
    if cs["qiang_state"] == "QIANG":
        evidence.append("YHZP-138-001")
        chain.append("qiang=强(無氣+遇劫双条件)")
        return {"strength_state": "STRONG", "evidence": evidence, "chain": chain, "note": "YHZP 日干無氣遇劫為強"}
    # 2. wang+根强+帮身 → 强方向（1983 失令非旺，不触发）
    if cs["wang_state"] == "WANG" and cs["root_state"] in ("STRONG_ROOT", "NORMAL_ROOT"):
        evidence.append("YHZP-138-001")
        chain.append("wang=旺+根强+帮身")
        return {"strength_state": "STRONG", "evidence": evidence, "chain": chain, "note": "得時為旺+根强"}
    # 3. shuai+帮身充足+有根 → 衰中有旺 → SLIGHTLY_WEAK
    if cs["shuai_state"] == "SHUAI" and cs["support_state"] == "SUPPORT_PRESENT" and cs["root_state"] in ("WEAK_ROOT", "NORMAL_ROOT", "STRONG_ROOT"):
        evidence = ["YHZP-138-001", "SFTK-008-001", "DTS-016-002"]
        chain = ["shuai=SHUAI(失令)", "印透三帮身(SUPPORT_PRESENT)", "有根(亥甲/未乙)", "DTS 衰中有旺→不极弱", "SFTK 財多身弱佐证身弱方向"]
        return {"strength_state": "SLIGHTLY_WEAK", "evidence": evidence, "chain": chain,
                "note": "失令衰+印比帮身充足+有根→『衰中有旺』→偏弱（非极弱）；禁 shuai→WEAK 直映射"}
    # 4. shuai+无帮身+无根 → WEAK
    if cs["shuai_state"] == "SHUAI" and cs["support_state"] in ("NONE", "UNKNOWN") and cs["root_state"] in ("NO_ROOT", "UNKNOWN"):
        evidence = ["YHZP-138-001"]
        chain = ["shuai=SHUAI", "无帮身", "无根"]
        return {"strength_state": "WEAK", "evidence": evidence, "chain": chain}
    # 6. 其他 → UNDETERMINED（FAIL_CLOSED）
    return {"strength_state": "UNDETERMINED", "evidence": [], "chain": ["无授权谓词命中"], "note": "证据不足或冲突，FAIL_CLOSED"}


if __name__ == "__main__":
    print("==== PATCH-034：strength_state 综合裁决（RULE-034-01） ====")
    print("\n==== 1983-1103 输入状态 ====")
    print(json.dumps(CHART_STATE, ensure_ascii=False, indent=1))
    print("\n==== 裁决结果 ====")
    r = rule_034_01_strength(CHART_STATE)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("\n==== 治理核对 ====")
    print("  无评分/权重/百分比 ✓｜无 factor_count→strength ✓｜无单因子触发（shuai 单独不映射 WEAK）✓")
    print("  authorized producers：0 → RULE-034-01（YHZP+SFTK+DTS COMPOSITE）")
