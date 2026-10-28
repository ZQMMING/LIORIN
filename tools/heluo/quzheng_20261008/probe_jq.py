# -*- coding: utf-8 -*-
"""实测：L558–567 四正卦化工窗口在节气轴上的真实跨度与空档。"""
import io
from datetime import date, timedelta

import sxtwl

JQ = ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏",
      "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露",
      "霜降", "立冬", "小雪", "大雪")
WINDOWS = (("坎", 0, 5), ("震", 6, 11), ("离", 12, 17), ("兑", 18, 23))

# 扫 2026 全年每日，记录节气索引
out = []
days = []
cur = date(2025, 11, 1)
prev = None
while cur <= date(2027, 3, 31):
    jq = sxtwl.fromSolar(cur.year, cur.month, cur.day).getJieQi()
    if jq is not None and jq != 255:
        days.append((cur, jq, JQ[jq]))
        prev = (cur, jq)
    cur += timedelta(days=1)

out.append("2026 年节气实测（%d 个节气点）：" % len(days))
for d, jq, name in days:
    out.append("   %s  jq=%2d  %s" % (d, jq, name))

out.append("")
out.append("== 四窗口覆盖天数（2026 实测）==")
tot = 0
for name, a, b in WINDOWS:
    n = sum(1 for d in days if a <= d[1] <= b and d[0].year == 2026)
    tot += n
    out.append("   %s  jq %2d–%2d  (%s → %s)  %3d 天" % (name, a, b, JQ[a], JQ[b], n))
out.append("   四窗口合计 %d 天；2026 全年 365 天" % tot)
out.append("   → **空档 %d 天**" % (365 - tot))

out.append("")
out.append("== 空档落在哪几个月支 ==")
# 节起月支：子←冬至 丑←小寒 寅←立春 卯←惊蛰 辰←清明 巳←立夏 午←芒种
#           未←小暑 申←立秋 酉←白露 戌←秋分 亥←立冬
JQ_START_BRANCH = {0: "子", 1: "丑", 3: "寅", 5: "卯", 7: "辰", 9: "巳",
                   11: "午", 13: "未", 15: "申", 17: "酉", 18: "戌", 21: "亥"}
BR = "子丑寅卯辰巳午未申酉戌亥"


def branch_of(d: date) -> str:
    """该日所属月支（以「节」起月）。"""
    seq = sorted(days, key=lambda x: x[0])
    b = "子"
    for dd, jq, _ in seq:
        if jq in JQ_START_BRANCH and dd <= d:
            b = JQ_START_BRANCH[jq]
    return b


def jq_of(d: date) -> int:
    seq = sorted(days, key=lambda x: x[0])
    cur_jq = 24
    for dd, jq, _ in seq:
        if dd <= d:
            cur_jq = jq
        else:
            break
    return cur_jq


gaps = []
cur = date(2026, 1, 1)
while cur <= date(2026, 12, 31):
    j = jq_of(cur)
    if not any(a <= j <= b for _n, a, b in WINDOWS):
        gaps.append((cur, branch_of(cur), j))
    cur += timedelta(days=1)

if gaps:
    out.append("   空档共 %d 天，首日 %s（%s月，月支%s）"
               % (len(gaps), gaps[0][0], gaps[0][0].month, gaps[0][1]))
    seen = []
    for d, b, j in gaps:
        if not seen or seen[-1] != (b, JQ[j]):
            seen.append((b, JQ[j]))
    for b, j in seen:
        n = sum(1 for d, bb, _ in gaps if bb == b)
        out.append("     %s月：%d 天（起于 %s）" % (b, n, j))

out.append("")
out.append("== 月支 → 窗口归属（按窗口实算，非近似）==")
for i, b in enumerate(BR):
    ds = [d for d in (date(2026, 1, 1) + timedelta(n) for n in range(365))
          if branch_of(d) == b]
    owners = {}
    for d in ds:
        j = jq_of(d)
        for n2, a, bb in WINDOWS:
            if a <= j <= bb:
                owners[n2] = owners.get(n2, 0) + 1
    out.append("   %s月：%s" % (b, owners if owners else "**无窗口**"))

io.open("probe_jq.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))