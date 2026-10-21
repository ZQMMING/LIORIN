# -*- coding: utf-8 -*-
"""校正版：按「节换月」口径，实测四正卦窗口（L558–567）逐日归属。"""
import io
from datetime import date, timedelta

import sxtwl

JQ = ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏",
      "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露",
      "霜降", "立冬", "小雪", "大雪")
WINDOWS = (("坎", 0, 5), ("震", 6, 11), ("离", 12, 17), ("兑", 18, 23))

# 通行「正月建寅」：以十二节换月，子月起冬至、丑月起大寒……每支约 30.4 天
JQ_START_BRANCH = {0: "子", 2: "丑", 3: "寅", 5: "卯", 7: "辰", 9: "巳",
                   11: "午", 13: "未", 15: "申", 17: "酉", 19: "戌", 21: "亥"}

pts = []
cur = date(2025, 11, 1)
while cur <= date(2027, 4, 30):
    jq = sxtwl.fromSolar(cur.year, cur.month, cur.day).getJieQi()
    if jq is not None and jq != 255 and 0 <= jq < 24:
        pts.append((cur, jq))
    cur += timedelta(days=1)
pts.sort()


def jq_of(d):
    cur_jq = 0
    for dd, jq in pts:
        if dd <= d:
            cur_jq = jq
        else:
            break
    return cur_jq


def branch_of(d):
    b = "子"
    for dd, jq in pts:
        if jq in JQ_START_BRANCH and dd <= d:
            b = JQ_START_BRANCH[jq]
    return b


def owner(j):
    for n, a, b in WINDOWS:
        if a <= j <= b:
            return n
    return ""


out = []
out.append("== 逐月支实测（2026 全年 365 天）==")
agg = {}
for k in range(365):
    d = date(2026, 1, 1) + timedelta(days=k)
    agg.setdefault(branch_of(d), {}).setdefault(owner(jq_of(d)) or "【空档】", 0)
    agg[branch_of(d)][owner(jq_of(d)) or "【空档】"] += 1

BR = "子丑寅卯辰巳午未申酉戌亥"
total_gap = 0
for b in BR:
    seg = agg.get(b, {})
    parts = ["%s %d天" % (k or "【空档】", v) for k, v in sorted(seg.items())]
    total_gap += seg.get("【空档】", 0)
    out.append("   %s月：%s" % (b, " | ".join(parts)))
out.append("   全年空档合计：%d 天" % total_gap)

out.append("")
out.append("== 现行近似表（hua_gong.SEASON_BRANCH_TO_HUAGONG）vs 原典窗口 ==")
LEGACY = {"亥": "坎", "子": "坎", "丑": "坎", "寅": "震", "卯": "震", "辰": "震",
          "巳": "离", "午": "离", "未": "离", "申": "兑", "酉": "兑", "戌": "兑"}
out.append("   月支  近似表  原典窗口(逐日)          差异")
diff_n = 0
for b in BR:
    seg = agg.get(b, {})
    real = {k for k in seg if k != "【空档】"}
    leg = LEGACY[b]
    if real == {leg}:
        verdict = "一致"
    elif leg in real and len(real) > 1:
        verdict = "**部分不符**：该月跨 %s" % "/".join(sorted(real))
        diff_n += 1
    elif leg not in real:
        verdict = "**整月不符**"
        diff_n += 1
    else:
        verdict = "?"
    out.append("   %s   %s     %-22s %s"
               % (b, leg, "/".join(sorted(real)) or "（全月空档）", verdict))
out.append("   → 现行近似表有 %d 个月支与原典窗口不符" % diff_n)

out.append("")
out.append("== L585–594「化工相反」窗口与正窗口对照 ==")
FAN = (("坎反离", 12, 18, "夏至以后秋分前"), ("离反坎", 0, 6, "冬至以后春分前"),
       ("兑反震", 6, 12, "春分以后夏至前"), ("震反兑", 18, 24, "秋分以后冬至前"))
for name, a, b, txt in FAN:
    match = [w[0] for w in WINDOWS if w[1] >= a and w[2] < b]
    out.append("   %s「%s」jq[%d,%d) → 正窗口 %s" % (name, txt, a, b, match))

io.open("probe_jq2.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))