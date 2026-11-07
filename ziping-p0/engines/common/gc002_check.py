# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'engines\common')
import pattern_success_rules as ps  # 该模块已自行 wrap stdout（UTF-8）

# GC-002：1990-01-15 10:00 → 己巳 乙丑 庚辰 辛巳（庚日主丑月印格）
GC2 = {
    "pattern_state": "CANDIDATE(印格)",
    "day_master": "庚",
    "month_branch": "丑",
    "stems": {"年": "己", "月": "乙", "日": "庚", "时": "辛"},
    "hidden": {"巳": ["丙", "庚", "戊"], "丑": ["己", "癸", "辛"], "辰": ["戊", "乙", "癸"], "未": []},  # 时支巳单独给
}

if __name__ == "__main__":
    import json
    print("==== GC-002 印格成败（RULE-035-02）====")
    # 修正 hidden（四支：年巳/月丑/日辰/时巳）
    GC2["hidden"] = {"年": ["丙", "庚", "戊"], "月": ["己", "癸", "辛"], "日": ["戊", "乙", "癸"], "时": ["丙", "庚", "戊"]}
    r = ps.rule_035_all(GC2)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("\n==== 校验 ====")
    assert r["current_grid"] == "印格"
    assert r["applicable_rule"] == "RULE-035-02"
    assert r["result"]["pattern_success_state"].startswith("SUCCESS")
    print("  GC-002 判定通过：印格 SUCCESS（印多逢財而財透根輕）✓")
