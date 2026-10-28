# -*- coding: utf-8 -*-
"""验证：sxtwl.getJieQiByYear 一次取全年节气，能否替代逐日扫描的 _find_jie。

先证明等价，再动生产代码 —— 不能拿「应该一样」当证据。
"""
import io
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import sxtwl  # noqa: E402


def find_jie_scan(year, month, jq):
    """现状：逐日扫整月（canonical.py:80 与 guajie.py:2036 两处相同实现）。"""
    d0 = date(year, month, 1)
    found = d0
    n = 0
    while d0.month == month:
        day = sxtwl.fromSolar(d0.year, d0.month, d0.day)
        n += 1
        if day.getJieQi() == jq:
            found = d0
        d0 += timedelta(days=1)
    return found, n


def find_jie_table(year, jq):
    """候选：一次 getJieQiByYear 拿全年节气，取 jq 命中项。"""
    for info in sxtwl.getJieQiByYear(year):
        jd, idx = (info.jd, info.jqIndex) if hasattr(info, "jd") else (info[0], info[1])
        if idx != jq:
            continue
        t = sxtwl.JD2DD(jd)
        if int(t.Y) == year:
            return date(int(t.Y), int(t.M), int(t.D)), 1
    return None, 0


out = []
bad = 0
total_scan = 0
total_tbl = 0
YEARS = list(range(1900, 2101, 7))          # 抽样 29 个年份
PAIRS = [(0, 12), (12, 6)]                    # (jq, 该节气所在月)

for y in YEARS:
    for jq, month in PAIRS:
        a, na = find_jie_scan(y, month, jq)
        b, nb = find_jie_table(y, jq)
        total_scan += na
        total_tbl += nb
        if b != a:
            bad += 1
            if bad <= 6:
                out.append("  ✗ %d jq=%d  扫描=%s  查表=%s" % (y, jq, a, b))

out.append("抽样年份 %d × 节气 %d = %d 组" % (len(YEARS), len(PAIRS),
                                                len(YEARS) * len(PAIRS)))
out.append("不一致 %d 组" % bad)
out.append("sxtwl.fromSolar 调用：逐日扫描 %d 次 vs 查表 %d 次"
           % (total_scan, total_tbl))
out.append("加速比：%.0f×" % (total_scan / max(total_tbl, 1)))

# 逐年全测，确认不是抽样巧合
out.append("")
out.append("== 逐年全测（1900-2100，jq=0 冬至）==")
bad2 = 0
for y in range(1900, 2101):
    a, _ = find_jie_scan(y, 12, 0)
    b, _ = find_jie_table(y, 0)
    if a != b:
        bad2 += 1
        if bad2 <= 4:
            out.append("  ✗ %d 扫描=%s 查表=%s" % (y, a, b))
out.append("不一致 %d / 201 组" % bad2)

io.open(ROOT / "tools" / "heluo" / "quzheng_20261008" / "jq_equiv.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))