# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'engines\common')
import pattern_success_rules as ps  # 模块已 wrap stdout

# GC-003：1992-07-15 12:00 → 壬申 丁未 壬辰 丙午（壬日主未月官格）
GC3 = {
    "pattern_state": "CANDIDATE(官格)",
    "day_master": "壬",
    "month_branch": "未",
    "stems": {"年": "壬", "月": "丁", "日": "壬", "时": "丙"},
    "branches": {"年": "申", "月": "未", "日": "辰", "时": "午"},
    "hidden": {"申": ["庚", "壬", "戊"], "未": ["己", "丁", "乙"], "辰": ["戊", "乙", "癸"], "午": ["丁", "己"]},
}

if __name__ == "__main__":
    import json
    print("==== GC-003 官格成败（RULE-035-04）====")
    r = ps.rule_035_all(GC3)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("\n==== 校验 ====")
    assert r["current_grid"] == "官格", r["current_grid"]
    assert r["applicable_rule"] == "RULE-035-04"
    assert r["result"]["pattern_success_state"].startswith("SUCCESS"), r["result"]["pattern_success_state"]
    print("  GC-003 判定通过：官格 SUCCESS（官逢財印又無刑衝破害）✓")
