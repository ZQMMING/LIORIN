# -*- coding: utf-8 -*-
"""案例锚点批量验证（审计用）— 验证当前引擎输出与已确证锚点一致，修复后作回归对照。"""
import sys, io, json
sys.path.insert(0, r"D:\shuntian")
sys.path.insert(0, r"D:\shuntian\src")
from tongshu.engines.heluo_adapter import HeluoAdapter

# (年,月,日,时, gender, 预期先天, 预期元堂, 预期后天, 预期节气, 预期月支, 预期化工卦, 预期化工状态)
ANCHORS = [
    ((1983, 11, 3, 12), "male",   "风山渐", "初六", "火风鼎", "霜降", "戌", "兑", "UNRESOLVED"),
    ((2026, 2, 3, 6),   "male",   "山火贲", "初九", "艮为山", "大寒", "丑", "坎", "REVERSE"),
    ((2026, 12, 7, 10), "female", "坤为地", "上六", "地山谦", "大雪", "亥", "坎", "UNRESOLVED"),
    ((1990, 5, 15, 18), "female", "风火家人", "六四", "火天大有", "立夏", "巳", "离", "NORMAL"),
    ((2000, 12, 25, 2), "male",   "风地观", "上九", "地水师", "冬至", "子", "坎", "NORMAL"),
    ((1945, 8, 20, 6),  "male",   "天地否", "九四", "地风升", "立秋", "申", "兑", "UNRESOLVED"),
    ((1980, 6, 22, 10), "male",   "风地观", "六二", "水风井", "夏至", "午", "离", "REVERSE"),
    ((1724, 6, 5, 12),  "male",   "水风井", "初六", "天水讼", "芒种", "巳", "离", "REVERSE"),
]

adapter = HeluoAdapter()
ok = True
for (ymdh, gender, pre, yt, post, jq, branch, hg, state) in ANCHORS:
    try:
        r = adapter.compute(ymdh, gender=gender)
        yt_name = r.yuantang.yuantang
        jq_name = (r.seasonal_hexagram or {}).get("jq_name", "?")
        hg_info = r.hua_gong
        hg_tri = hg_info.huagong_trigram if hg_info else "?"
        hg_state = hg_info.state.value if hg_info else "?"
        hg_branch = hg_info.birth_month_branch if hg_info else "?"
        line = f"{ymdh} {gender}: 先天={r.prenatal.hexagram_name} 元堂={yt_name} 后天={r.postnatal.hexagram_name} 节气={jq_name} 月支={hg_branch} 化工卦={hg_tri} 状态={hg_state}"
        exp = f"先天={pre} 元堂={yt} 后天={post} 节气={jq} 月支={branch} 化工卦={hg} 状态={state}"
        match = (r.prenatal.hexagram_name == pre and yt_name == yt and r.postnatal.hexagram_name == post
                 and jq_name == jq and hg_branch == branch and hg_tri == hg and hg_state == state)
        flag = "OK " if match else "**MISMATCH**"
        if not match:
            ok = False
        print(f"[{flag}] {line}")
        print(f"      expected: {exp}")
    except Exception as e:
        ok = False
        print(f"[**ERROR**] {ymdh} {gender}: {type(e).__name__}: {e}")
print("ALL ANCHORS PASS" if ok else "ANCHORS FAILED")
