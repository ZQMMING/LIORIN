# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'engines\common')
import pattern_success_rules as ps  # 已 wrap stdout（不要再 wrap）

HIDDEN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '庚', '戊'], '午': ['丁', '己'], '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'], '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}


def chart(ymd_h, pillars, dm, mb):
    stems = {}; branches = {}
    order = ["年", "月", "日", "时"]
    for k, p in zip(order, pillars.split()):
        stems[k], branches[k] = p[0], p[1]
    hidden = {b: HIDDEN[b] for b in branches.values()}
    return {"pattern_state": "CANDIDATE", "day_master": dm, "month_branch": mb,
            "stems": stems, "branches": branches, "hidden": hidden}


CASES = [
    ("GC-004 食神格", "1993-04-15 04:00", "癸酉 丙辰 丙寅 庚寅", "丙", "辰", "SUCCESS(食神生財)"),
    ("GC-005 七煞格", "1990-05-15 14:00", "庚午 辛巳 庚辰 癸未", "庚", "巳", "SUCCESS(身強七煞逢伏)"),
    ("GC-006 伤官格", "1991-05-15 10:00", "辛未 癸巳 乙酉 辛巳", "乙", "巳", "SUCCESS(傷官帶煞而無財)"),
    ("GC-007 阳刃格", "1991-03-15 14:00", "辛未 辛卯 甲申 辛未", "甲", "卯", "SUCCESS(陽刃透官煞而露財印不見傷官)"),
]

for name, dt, pl, dm, mb, expect in CASES:
    print(f"==== {name}  {dt}  {pl} ====")
    r = ps.rule_035_all(chart(dt, pl, dm, mb))
    print(f"  current_grid={r['current_grid']}  rule={r['applicable_rule']}")
    print(f"  success={r['result']['pattern_success_state']}")
    print(f"  daiji={r['result']['daiji_state']}  rescue={r['result']['rescue_state']}  xiangshen={r['result']['xiangshen_state']}")
    ok = r["result"]["pattern_success_state"].startswith(expect.split("(")[0])
    print(f"  预期={expect.split('(')[0]}  → {'PASS' if ok else 'FAIL'}")
    print()
