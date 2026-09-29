# -*- coding: utf-8 -*-
"""盲派 Rule Matcher V3.3
输入: BlindFeatureSet（来自Feature Calculator）
输出: 命中 Rule_ID 列表 + Assertion + Provenance
"""
from typing import Dict, List, Any
from .blind_rule_registry import RULE_REGISTRY, RuleDef
from .blind_feature_calculator import BlindFeatureSet


def _hit(rule_id: str, assertion: str, evidence_id: str, inputs: Dict[str, Any]) -> Dict:
    return {
        "rule_id": rule_id,
        "evidence_id": evidence_id,
        "assertion": assertion,
        "inputs": inputs,
        "provenance": f"{rule_id} <- {evidence_id} <- V3.3",
    }


def match_rules_v2(f: BlindFeatureSet) -> List[Dict]:
    """用BlindFeatureSet匹配29条Rule"""
    hits: List[Dict] = []

    # ── L1 结构层 ──
    # R-BZ-001 宾主
    hits.append(_hit("R-BZ-001",
        f"MAIN={sorted(f.main_branches)} GUEST={sorted(f.guest_branches)}",
        "EVD-BZ-001",
        {"main": sorted(f.main_branches), "guest": sorted(f.guest_branches)}))

    # R-TY-001 体用
    hits.append(_hit("R-TY-001",
        f"TI={sorted(f.ti_branches)} YONG={sorted(f.yong_branches)}",
        "EVD-TY-001",
        {"ti": sorted(f.ti_branches), "yong": sorted(f.yong_branches)}))

    # R-GF-001 功神废神
    hits.append(_hit("R-GF-001",
        f"GONG={sorted(f.working_branches)} TARGET={sorted(f.work_targets)}",
        "EVD-GF-001",
        {"gong_shen": sorted(f.working_branches), "targets": sorted(f.work_targets)}))

    # R-PJ-001/002 正局反局
    if f.zheng_fan_ju == "ZHENG":
        hits.append(_hit("R-PJ-001", "局型=ZHENG", "EVD-PJ-001", {"zheng_fan_ju": "ZHENG"}))
    elif f.zheng_fan_ju == "FAN":
        hits.append(_hit("R-PJ-002", "局型=FAN", "EVD-PJ-002", {"zheng_fan_ju": "FAN"}))

    # R-ZB-001 贼神捕神
    if f.zei_bu == "ZEI_BU":
        hits.append(_hit("R-ZB-001",
            f"贼捕结构成立",
            "EVD-ZB-001", {"zei_bu": "ZEI_BU"}))

    # R-HE-001 六合
    if f.he_pairs:
        hits.append(_hit("R-HE-001",
            f"HE={[sorted(pair) for pair in f.he_pairs]}",
            "EVD-HE-001", {"he_pairs": [list(p) for p in f.he_pairs]}))

    # R-MU-001 墓
    if f.muku_branches:
        hits.append(_hit("R-MU-001",
            f"MU={sorted(f.muku_branches)}",
            "EVD-MU-001", {"muku": sorted(f.muku_branches)}))

    # R-MUKU-001 墓库识别
    if f.muku_branches:
        hits.append(_hit("R-MUKU-001",
            f"MUKU_PRESENT={sorted(f.muku_branches)}",
            "EVD-MUKU-001", {"muku_branches": sorted(f.muku_branches)}))

    # R-MUKU-002 刑冲开库
    if f.muku_opened:
        hits.append(_hit("R-MUKU-002",
            f"MUKU_OPENED={sorted(f.muku_opened)} method=冲/刑",
            "EVD-MUKU-002", {"opened": sorted(f.muku_opened), "method": list(f.work_methods)}))

    # R-XING 三刑
    if f.xing_pairs:
        hits.append(_hit("R-XING-001",
            f"XING={[sorted(p) for p in f.xing_pairs]}",
            "EVD-XING-001", {"xing": [list(p) for p in f.xing_pairs]}))

    # R-CHONG 六冲
    if f.chong_pairs:
        hits.append(_hit("R-CHONG-001",
            f"CHONG={[sorted(p) for p in f.chong_pairs]}",
            "EVD-CHONG-001", {"chong": [list(p) for p in f.chong_pairs]}))

    # R-CHUAN 六穿
    if f.chuan_pairs:
        hits.append(_hit("R-CHUAN-001",
            f"CHUAN={[sorted(p) for p in f.chuan_pairs]}",
            "EVD-CHUAN-001", {"chuan": [list(p) for p in f.chuan_pairs]}))

    return hits


def match_rules(chart, blind_result, yingqi_result=None) -> List[Dict]:
    """兼容旧接口：从blind_result提取特征"""
    hits: List[Dict] = []

    # 基础宾主
    hits.append(_hit("R-BZ-001",
        f"MAIN={sorted(blind_result.main_branches)} GUEST={sorted(blind_result.guest_branches)}",
        "EVD-BZ-001",
        {"main": sorted(blind_result.main_branches), "guest": sorted(blind_result.guest_branches)}))

    # 体用
    hits.append(_hit("R-TY-001",
        f"TI={blind_result.ti_stems} YONG={blind_result.yong_stems}",
        "EVD-TY-001",
        {"ti": blind_result.ti_stems, "yong": blind_result.yong_stems}))

    # 功神废神
    hits.append(_hit("R-GF-001",
        f"GONG={sorted(blind_result.zuo_gong_actors)} TARGET={sorted(blind_result.zuo_gong_targets)}",
        "EVD-GF-001",
        {"gong_shen": sorted(blind_result.zuo_gong_actors), "targets": sorted(blind_result.zuo_gong_targets)}))

    # 正局反局
    zfj = getattr(blind_result, "zheng_fan_ju", "")
    if zfj == "ZHENG":
        hits.append(_hit("R-PJ-001", "局型=ZHENG", "EVD-PJ-001", {"zheng_fan_ju": zfj}))

    # 贼捕
    zb = getattr(blind_result, "zei_bu", "")
    if zb == "ZEI_BU":
        hits.append(_hit("R-ZB-001",
            f"贼捕结构={blind_result.zei_bu_reason}",
            "EVD-ZB-001", {"zei_bu": zb, "reason": blind_result.zei_bu_reason}))

    # 墓库
    all_branches = [chart.year_pillar.earthly_branch,
                    chart.month_pillar.earthly_branch,
                    chart.day_pillar.earthly_branch,
                    chart.hour_pillar.earthly_branch]
    muku_set = {"辰", "戌", "丑", "未"}
    muku_branches = [b for b in all_branches if b in muku_set]
    if muku_branches:
        hits.append(_hit("R-MUKU-001",
            f"MUKU_PRESENT={muku_branches}",
            "EVD-MUKU-001",
            {"muku_branches": muku_branches}))

    return hits


def coverage_report() -> dict:
    """Generate coverage report for blind rule registry."""
    from .blind_rule_registry import RULE_REGISTRY, FORBIDDEN_RULES, COUNTER_EXAMPLES
    return {
        'registry_total': len(RULE_REGISTRY),
        'established': sum(1 for r in RULE_REGISTRY.values() if getattr(r, 'status', '') == 'ESTABLISHED'),
        'forbidden': len(FORBIDDEN_RULES),
        'counter_examples': len(COUNTER_EXAMPLES),
        'rule_ids': sorted(RULE_REGISTRY.keys()),
    }
