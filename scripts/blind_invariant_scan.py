# -*- coding: utf-8 -*-
"""盲派引擎全量不变式扫描（质量护栏，不产真值）。

用途：在随机样本上检查「枚举取值合法 + 结构自洽（无互斥状态并存）+ 应期层
不崩溃」。只报问题，不改判定；发现问题再回引擎定位。

用法：
    $env:PYTHONPATH='D:\\shuntian\\src'
    python scripts/blind_invariant_scan.py 200
"""
from __future__ import annotations

import random
import sys
import traceback

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine
from tongshu.engines.blind_yingqi import BlindYingqiEngine, EVENT_DOMAINS

# ---- 枚举白名单（与引擎常量一致；新增取值必须先登记）----
ENUM_OK = {
    "zheng_fan_ju": {"ZHENG", "FAN_JU"},
    "marriage_state": {"BROKEN", "HARMONIOUS", "CHALLENGED", "UNDETERMINED"},
    "wealth_state": {
        "SUBSTITUTED_ROBBED", "SUBSTITUTED_AND_ESTABLISHED", "SUBSTITUTED_CANDIDATE",
        "DIRECTED_WITH_ROBBERY", "DIRECTED_AND_ESTABLISHED", "DIRECTED_PARTIAL",
        "PRESENT_ROBBED", "PRESENT_UNTAKEN", "ABSENT_NO_SUBSTITUTION", "UNDETERMINED",
    },
    "official_state": {
        "DAMAGED", "ROBBED", "CONTROLLED_PARTIAL", "CONTROLLED_AND_CLEAN",
        "UNCONTROLLED", "LU_SUBSTITUTED", "UNDETERMINED",
    },
    "control_completeness": {"CLEAN", "PARTIAL", "UNDETERMINED", "NONE"},
    "work_efficiency": {"NONE", "SMALL", "MEDIUM", "LARGE", "UNDETERMINED"},
    "work_level": {
        "LARGE_NOBLE", "MEDIUM_NOBLE", "SMALL_NOBLE", "POOR", "UNDETERMINED",
    },
    "shi_direction": {
        "FIRE_EARTH→METAL_WATER", "METAL_WATER→FIRE_EARTH",
        "WOOD_FIRE→EARTH_METAL", "EARTH_METAL→WOOD_FIRE",
        "METAL→WOOD", "WOOD→EARTH", "EARTH→WATER", "WATER→FIRE",
        "FIRE→METAL", "UNDETERMINED",
    },
    "blind_wangshuai": {"WANG", "WANG_JI", "RUO", "TAI_RUO", "ZHONG_HE_PIAN_RUO", "UNDETERMINED"},
    "shi_zhi_jing": {"ZHI_JING", "ZHI_BU_JING", "UNDETERMINED"},
    "body_candidate": {
        "LU_UNDER_ATTACK", "YANG_REN_CLASHED", "YANG_REN", "YANG_REN_PRESENT", "LU", "LU_PRESENT",
        "NONE", "UNDETERMINED",
    },
    "child_state": {"POSITIVE", "NEGATIVE", "UNDETERMINED"},
}
GONG_ROLES = {"WORKING", "SUPPORTING", "TARGET", "BLOCKING", "IDLE", "WASTE", "UNDETERMINED"}
# palace_state 是 flag 拼接枚举，按固定次序 CLASHED→HARMED→PUNISHED→PO_BROKEN→HE_BANNED，
# 逐段校验而不是维护全排列白名单
PALACE_FLAGS = ("CLASHED", "HARMED", "PUNISHED", "PO_BROKEN", "HE_BANNED")

def _palace_state_ok(value: str) -> bool:
    if value == "STABLE":
        return True
    toks = value.split("_AND_")
    return all(t in PALACE_FLAGS for t in toks) and toks == sorted(
        toks, key=PALACE_FLAGS.index)


def _check_enum(issues, cid, field, value):
    allowed = ENUM_OK.get(field)
    if value is None:
        return
    if allowed is not None and value not in allowed:
        issues.append((cid, "enum", f"{field}={value!r} 非法"))


def check_result(issues, cid, b, r):
    d = r.to_dict() if hasattr(r, "to_dict") else {}
    for f in ("zheng_fan_ju", "control_completeness", "work_efficiency",
              "work_level", "shi_direction", "blind_wangshuai", "shi_zhi_jing"):
        _check_enum(issues, cid, f, d.get(f))
    m = d.get("marriage_event_structure") or {}
    w = d.get("wealth_event_structure") or {}
    o = d.get("official_event_structure") or {}
    body = d.get("body_event_candidate") or {}
    child = d.get("child_event_structure") or {}
    _check_enum(issues, cid, "marriage_state", m.get("marriage_state"))
    _check_enum(issues, cid, "wealth_state", w.get("wealth_state"))
    _check_enum(issues, cid, "official_state", o.get("official_state"))
    _check_enum(issues, cid, "body_candidate", body.get("candidate") or body.get("body_state"))
    _check_enum(issues, cid, "child_state", child.get("child_state"))
    palace = m.get("palace_state")
    if palace is not None and not _palace_state_ok(palace):
        issues.append((cid, "enum", f"palace_state={palace!r} 非法"))
    for role in (d.get("gong_shen") or {}):
        if role not in GONG_ROLES:
            issues.append((cid, "enum", f"gong_shen role={role!r} 非法"))
    # ---- 结构自洽 ----
    if m.get("marriage_state") == "HARMONIOUS" and d.get("zhenfu_risk") == "DIVORCE":
        issues.append((cid, "contradiction", "marriage=HARMONIOUS 但 zhenfu_risk=DIVORCE"))
    if w.get("wealth_state") == "DIRECTED_AND_ESTABLISHED" and not w.get("wealth_present"):
        issues.append((cid, "contradiction", "wealth=ESTABLISHED 但 wealth_present=False"))
    if w.get("wealth_state") == "PRESENT_UNTAKEN" and not w.get("wealth_present"):
        issues.append((cid, "contradiction", "wealth=PRESENT_UNTAKEN 但 wealth_present=False"))
    if o.get("official_state") == "CONTROLLED_AND_CLEAN" and o.get("officer_damaged"):
        issues.append((cid, "contradiction", "official=CLEAN 但 officer_damaged=True"))
    if o.get("official_state") == "ROBBED" and o.get("officer_damaged"):
        issues.append((cid, "contradiction", "official 同时 ROBBED/DAMAGED"))
    if d.get("work_level") and d.get("work_efficiency") == "NONE" and d.get("work_level") != "POOR":
        issues.append((cid, "contradiction", f"work_efficiency=NONE 但 work_level={d.get('work_level')}"))
    # ---- 应期层不崩 ----
    try:
        yq = BlindYingqiEngine(BaziEngine())
        for age in (1, 18, 36, 55, 80):
            yr = (b[0] or 0) + age
            if yr < 1900 or yr > 2100:
                continue
            res = yq.analyze(b, gender="male" if cid % 2 == 0 else "female", target_year=yr)
            if not isinstance(res.age, int):
                issues.append((cid, "yingqi", f"age 非整数: {res.age!r}"))
            for e in res.yingqi_events:
                dom = e.get("domain")
                if dom not in EVENT_DOMAINS:
                    issues.append((cid, "yingqi", f"domain={dom!r} 非法"))
                if e.get("year") != yr:
                    issues.append((cid, "yingqi", f"event year={e.get('year')!r} 与 target {yr} 不符"))
    except Exception:
        issues.append((cid, "yingqi", "analyze 异常: " + traceback.format_exc().splitlines()[-1]))


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    random.seed(20261105)
    be = BaziEngine()
    bl = BlindBaziEngine(bazi_engine=be)
    issues: list[tuple] = []
    done = 0
    for i in range(n):
        y = random.randint(1930, 2010)
        mo = random.randint(1, 12)
        day = random.randint(1, 28)
        h = random.randint(0, 23)
        b = (y, mo, day, h)
        try:
            chart = be.compute(b, gender="male" if i % 2 == 0 else "female")
            r = bl.compute_from_chart(chart)
            check_result(issues, i, b, r)
            done += 1
        except Exception:
            issues.append((i, "compute", "异常: " + traceback.format_exc().splitlines()[-1]))
    enum_n = sum(1 for x in issues if x[1] == "enum")
    contra_n = sum(1 for x in issues if x[1] == "contradiction")
    yq_n = sum(1 for x in issues if x[1] == "yingqi")
    compute_n = sum(1 for x in issues if x[1] == "compute")
    print(f"测盘 {done} / 请求 {n}")
    print(f"枚举非法 {enum_n} | 结构互斥 {contra_n} | 应期异常 {yq_n} | 计算异常 {compute_n}")
    for cid, kind, msg in issues[:25]:
        print(f"  [{kind}] #{cid}: {msg}")
    if len(issues) > 25:
        print(f"  … 其余 {len(issues) - 25} 条")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
