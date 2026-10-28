# -*- coding: utf-8 -*-
"""PATCH-067 Climate Condition Runtime Contract
原文条件→谓词; 主次用拆分; 状态枚举(禁百分比/评分)
"""
import io, sys
# 顶层不wrap, 只在__main__时wrap(避免import后I/O closed)

# 状态枚举(068冻结)
CLIMATE_STATE_ENUM = ["PRIMARY", "SECONDARY", "SUPPORTING", "DEGRADED", "ABSENT"]

# 10x12 谓词表(主用/辅/忌/降级条件)
CLIMATE_PREDICATES = {
    ("乙", "戌"): {"primary": "癸", "secondary": "", "avoid": "戊制癸", "degrade_when": "壬透多", "degrade_target": "癸", "src": "QTBJ-022-001"},
    ("乙", "午"): {"primary": "癸", "secondary": "丙", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-018-001"},
    ("丙", "午"): {"primary": "壬", "secondary": "庚", "avoid": "戊己制壬", "degrade_when": "", "degrade_target": "", "src": "QTBJ-031-001"},
    ("庚", "申"): {"primary": "丁", "secondary": "甲", "avoid": "壬癸", "degrade_when": "", "degrade_target": "", "src": "QTBJ-068-001"},
    ("甲", "亥"): {"primary": "庚", "secondary": "丁", "avoid": "壬泛须戊制", "degrade_when": "", "degrade_target": "", "src": "QTBJ-011-001"},
    ("丙", "子"): {"primary": "壬", "secondary": "戊", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-037-001"},
    ("戊", "未"): {"primary": "癸", "secondary": "丙甲", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-050-001"},
    ("戊", "戌"): {"primary": "甲", "secondary": "癸", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-053-001"},
    ("庚", "巳"): {"primary": "壬", "secondary": "戊丙", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-065-001"},
    ("壬", "子"): {"primary": "丙", "secondary": "戊", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-092-001"},
    ("甲", "寅"): {"primary": "丙", "secondary": "癸", "avoid": "", "degrade_when": "", "degrade_target": "", "src": "QTBJ-003-001"},
}


def climate_eval(daymaster, month_branch, stems_present=None):
    """
    谓词求值: IF 日主 AND 月令 THEN primary/secondary
    降级: IF degrade_when条件成立 THEN target=DEGRADED
    """
    key = (daymaster, month_branch)
    if key not in CLIMATE_PREDICATES:
        return {"status": "ABSENT", "reason": "NOT_IN_REGISTRY", "namespace": "QTBJ.climate_use"}
    p = CLIMATE_PREDICATES[key]
    trace = [f"{daymaster}日", f"{month_branch}月"]
    out = {
        "state": "climate_use_state",
        "namespace": "QTBJ.climate_use",
        "primary": {"element": p["primary"], "status": "PRIMARY"},
        "secondary": {"element": p["secondary"], "status": "SECONDARY"} if p["secondary"] else [],
        "avoid": p["avoid"] or [],
        "evidence_chain": [p["src"]],
        "condition_trace": trace
    }
    # 降级判定(GC-001: 壬透多→癸降级)
    if p["degrade_when"] and stems_present:
        if "壬透多" in p["degrade_when"] and stems_present.count("壬") >= 2:
            out["primary"]["status"] = "DEGRADED"
            out["condition_trace"].append("壬透二")
            out["degraded_reason"] = "壬透多水难生乙"
    return out


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-067 调候运行时 ===")
    # GC-001: 乙木戌月, 天干壬癸壬(壬=2)
    r = climate_eval("乙", "戌", stems_present=["癸", "壬", "乙", "壬"])
    print("GC-001 乙戌(壬透二):")
    for k, v in r.items():
        print(f"  {k}: {v}")
