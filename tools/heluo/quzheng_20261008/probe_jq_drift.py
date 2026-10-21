# -*- coding: utf-8 -*-
"""判定漂移：solar_jq_index vs jiehhou.get_current_jieqi_info，逐日对 sxtwl 原始表。"""
import io
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, "src")
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

import sxtwl

from tongshu.engines.heluo.jiehhou import get_current_jieqi_info
from tongshu.engines.heluo.yue_ling_shu_ge import solar_jq_index

JQ = ("冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏",
      "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露",
      "霜降", "立冬", "小雪", "大雪")
out = []

# ── 建权威基准：2025+2026 全部节气真值 ────────────────────────
truth = []
for yy in (2025, 2026):
    for info in sxtwl.getJieQiByYear(yy):
        jd, idx = (info.jd, info.jqIndex) if hasattr(info, "jd") else (info[0], info[1])
        t = sxtwl.JD2DD(jd)
        truth.append((date(int(t.Y), int(t.M), int(t.D)), idx))
truth.sort()


def truth_jq(d: date) -> int:
    """当日所处的节气 = 最后一个 <= d 的节气点。"""
    cur = None
    for dd, idx in truth:
        if dd <= d:
            cur = idx
        else:
            break
    return cur


out.append("== 权威基准抽样（sxtwl.getJieQiByYear 原始表）==")
for dd, idx in truth[:6]:
    out.append("   %s → jq=%d %s" % (dd, idx, JQ[idx]))
out.append("   ...")

out.append("")
out.append("== 2026 全年 365 日三方比对 ==")
bad_a = bad_b = 0
sample_a = []
sample_b = []
d = date(2026, 1, 1)
for k in range(365):
    dd = d + timedelta(days=k)
    t = truth_jq(dd)
    a = solar_jq_index(dd.isoformat())
    info = get_current_jieqi_info(dd.year, dd.month, dd.day)
    b = info.jq_index if info else None
    if a != t:
        bad_a += 1
        if len(sample_a) < 4:
            sample_a.append((dd, a, t))
    if b != t:
        bad_b += 1
        if len(sample_b) < 4:
            sample_b.append((dd, b, t))
out.append("   solar_jq_index（yue_ling_shu_ge，我本轮用的那份）：错 %d/365" % bad_a)
for dd, a, t in sample_a:
    out.append("      %s  得到 %s，真值 %s(%s)" % (dd, a, t, JQ[t]))
out.append("   jiehhou.get_current_jieqi_info（节候卦在用的那份）：错 %d/365" % bad_b)
for dd, b, t in sample_b:
    out.append("      %s  得到 %s，真值 %s(%s)" % (dd, b, t, JQ[t]))

out.append("")
out.append("== 定位 jiehhou 的偏差形状 ==")
# 看偏差是否恒为 +1/-1（跨年建表漏前一年导致）
diffs = {}
d = date(2026, 1, 1)
for k in range(365):
    dd = d + timedelta(days=k)
    t = truth_jq(dd)
    info = get_current_jieqi_info(dd.year, dd.month, dd.day)
    b = info.jq_index if info else None
    if b != t:
        diffs[(b, t)] = diffs.get((b, t), 0) + 1
for (b, t), n in sorted(diffs.items(), key=lambda x: -x[1])[:8]:
    out.append("   得到 %s → 真值 %s(%s)  共 %d 天" % (b, t, JQ[t], n))

out.append("")
out.append("== 交节日当天是否正确（快路径）==")
for dd, idx in truth:
    if not (date(2025, 12, 1) <= dd <= date(2026, 12, 31)):
        continue
    info = get_current_jieqi_info(dd.year, dd.month, dd.day)
    b = info.jq_index if info else None
    if b != idx:
        out.append("   ✗ %s 交节日 得到 %s 应为 %s(%s)" % (dd, b, idx, JQ[idx]))
        break
else:
    out.append("   24 个交节日全部正确（快路径无误）→ 偏差只发生在「非交节日」查表分支")

io.open("tools/heluo/quzheng_20261008/probe_jq_drift.txt", "w",
        encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))