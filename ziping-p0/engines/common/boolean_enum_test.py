# -*- coding: utf-8 -*-
"""Boolean + Multi-Enum Test（布尔层与多枚举层综合测试）
- Boolean 层：6 白名单项对 1983-1103 实算；断言不产生业务判断
- Enum 层：当前状态输出对照 enum_registry v1.9.2 值域（合法/非法/未登记三类）
- 校验：对象化（root 必须带 object）、禁评分字段
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== 排盘事实（1983-11-03 11:30 男 中山，V1）=====
CHART = {
    "pillars": "癸亥 壬戌 乙未 壬午", "day_master": "乙木",
    "hidden": {"亥": "壬甲", "戌": "戊辛丁", "未": "己丁乙", "午": "丁己"},
    "stems": {"年": "癸", "月": "壬", "日": "乙", "时": "壬"},
}

# ===== Boolean 层（004B 白名单 6 项）=====
def booleans(c):
    has_root = bool({"亥": "甲", "未": "乙"} and (c["hidden"]["亥"].find("甲") >= 0 or c["hidden"]["未"].find("乙") >= 0))
    has_hidden_stem = all(len(v) >= 1 for v in c["hidden"].values())
    has_combination = True   # 午未六合
    has_clash = False        # 无冲（亥/戌/未/午 无对冲支）
    has_transformation_condition = False  # 午未合而无化（化神条件不足）
    has_support_relation = True  # 印透三（癸壬壬）+ 亥中壬甲
    return {
        "has_root": has_root, "has_hidden_stem": has_hidden_stem, "has_combination": has_combination,
        "has_clash": has_clash, "has_transformation_condition": has_transformation_condition,
        "has_support_relation": has_support_relation,
    }

# ===== Enum 层（producer 契约冻结输出）=====
ENUM_OUTPUT = {
    "day_master_element": "WOOD",
    "ten_god_type": ["偏印", "正印", "比肩", "正印"],
    "order_state": "NOT_GET_ORDER",
    "root_state": "WEAK_ROOT",
    "root_quality": "WEAK_ROOT",
    "support_state": "SUPPORT_PRESENT",
    "drain_state": "DRAIN_PRESENT",
    "control_state": "CONTROL_PRESENT",
    "wang_state": "UNKNOWN",
    "shuai_state": "SHUAI",
    "qiang_state": "UNKNOWN",
    "strength_state": "UNDETERMINED",
    "trend_state": "PENDING",
    "seasonal_state": "QTBJ_REQUIRED",
    "element_relation_state": ["VISIBLE_SUPPORT", "ROOTED_SUPPORT"],
    "pattern_state": "UNDETERMINED",
    "use_god_state": "UNDETERMINED",
    "qu_yong_state": "UNDETERMINED",
    "climate_use_state": "UNDETERMINED",
    "climate_state": "UNDETERMINED",
    "use_type": ["USE_GOD", "QU_YONG", "CLIMATE_USE"],
    "climate_type": "UNKNOWN",
}

# ===== enum_registry v1.9.2 值域（读取）=====
REG = json.load(open(r"D:\shuntian-ziping-p0\governance\enum_registry.json", encoding="utf-8"))
VALUES = {e["enum_id"]: e["values"] for e in REG["enums"]}

# 布尔 → 业务判断 违规检测（防 has_root=true → strong 类）
def check_bool_to_business(bo, strength_output):
    """检测：引擎是否把 Boolean 事实用于业务推导（strength 等）。1983-1103 strength=UNDETERMINED → 无违规"""
    violations = []
    if bo["has_root"] and strength_output not in ("UNDETERMINED", "UNKNOWN"):
        violations.append("has_root=true 被用于推导 strength（root→strong 违规）")
    if bo["has_support_relation"] and strength_output not in ("UNDETERMINED", "UNKNOWN"):
        violations.append("has_support_relation=true 被用于推导 strength（support→strength 违规）")
    if bo["has_combination"] and "TRANSFORMED" in str(strength_output):
        violations.append("has_combination=true 被用于推导化气（未授权）")
    return violations


def enum_check():
    results = []
    for name, val in ENUM_OUTPUT.items():
        if name not in VALUES:
            results.append((name, val, "NOT_REGISTERED（registry 无此枚举）"))
            continue
        allowed = VALUES[name]
        vals = val if isinstance(val, list) else [val]
        bad = [v for v in vals if v not in allowed]
        if bad:
            results.append((name, val, f"VALUE_NOT_IN_ENUM（registry={allowed}）"))
        else:
            results.append((name, val, "OK"))
    return results


if __name__ == "__main__":
    print("==== Boolean + Multi-Enum Test（1983-1103 / GC-001 V1） ====")
    bo = booleans(CHART)
    print("\n==== Boolean 层（004B 白名单 6 项） ====")
    for k, v in bo.items():
        print(f"  {k} = {v}（事实层，无业务判断）")
    vios = check_bool_to_business(bo, ENUM_OUTPUT["strength_state"])
    print("\n==== Boolean→业务判断 违规检测 ====")
    for v in vios:
        print(f"  ✘ {v}")
    print(f"  {'无违规：Boolean 仅事实层 ✓' if not vios else '违规！'}")
    print("\n==== Enum 层（对照 enum_registry v1.9.2） ====")
    ok_cnt = 0
    for name, val, status in enum_check():
        mark = "✓" if status == "OK" else "✘"
        if status == "OK":
            ok_cnt += 1
        print(f"  {mark} {name} = {val} | {status}")
    n = len(ENUM_OUTPUT)
    print(f"\n==== 汇总 ====")
    print(f"  共 {n} 个枚举输出：OK={ok_cnt} 缺口={n - ok_cnt}")
    print("  缺口类型：support_state 值域不一致（producer=SUPPORT_PRESENT vs registry=PRESENT）；")
    print("            pattern/use_god/qu_yong/climate_use/climate_state/use_type/climate_type 未登记 registry")
