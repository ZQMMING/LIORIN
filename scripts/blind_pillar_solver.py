#!/usr/bin/env python
"""四柱 → 公历日期求解器（盲派真值案例补录用）.

给定四柱（如 "丁亥 癸丑 己未 癸酉"）在 [start, end] 年内扫描，
输出所有四柱完全吻合的 (年, 月, 日, 时) 候选。

说明：年柱取当年 7 月 1 日（避开立春/年界歧义），月柱/日柱用 sxtwl 的节气/干支，
时柱由日干按五鼠遁推出；时支取该支的中间小时（子=0, 丑=2, …, 亥=22）。

    python scripts/blind_pillar_solver.py "丁亥 癸丑 己未 癸酉" --start 1850 --end 2030
"""
from __future__ import annotations

import argparse
import datetime as dt

import sxtwl

STEM = "甲乙丙丁戊己庚辛壬癸"
BRANCH = "子丑寅卯辰巳午未申酉戌亥"
STEM_IDX = {c: i for i, c in enumerate(STEM)}
BRANCH_IDX = {c: i for i, c in enumerate(BRANCH)}
# 五鼠遁：日干 → 子时干序
HOUR_STEM_BASE = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4,
                  "丁": 6, "壬": 6, "戊": 8, "癸": 8}
HOUR_BY_BRANCH = {i: (0 if i == 0 else 2 * i) for i in range(12)}
HOUR_BY_BRANCH[0] = 0


def gz_letters(dz_day, kind: str):
    if kind == "year":
        tg, dz = dz_day.getYearGZ().tg, dz_day.getYearGZ().dz
    elif kind == "month":
        tg, dz = dz_day.getMonthGZ().tg, dz_day.getMonthGZ().dz
    else:
        tg, dz = dz_day.getDayGZ().tg, dz_day.getDayGZ().dz
    return STEM[tg] + BRANCH[dz]


def hour_pillar(day_stem: str, branch_idx: int) -> str:
    hs = (HOUR_STEM_BASE[day_stem] + branch_idx) % 10
    return STEM[hs] + BRANCH[branch_idx]


def solve(pillars: str, start: int, end: int, limit: int = 12):
    want = pillars.split()
    if len(want) != 4:
        raise ValueError("需要四柱，如 '丁亥 癸丑 己未 癸酉'")
    hour_branch = BRANCH_IDX[want[3][1]]
    hour_pillar_want = want[3]
    hits = []
    for year in range(start, end + 1):
        d = sxtwl.fromSolar(year, 7, 1)
        if gz_letters(d, "year") != want[0]:
            continue
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    d = sxtwl.fromSolar(year, month, day)
                except Exception:
                    continue
                if gz_letters(d, "month") != want[1]:
                    continue
                if gz_letters(d, "day") != want[2]:
                    continue
                day_stem = gz_letters(d, "day")[0]
                if hour_pillar(day_stem, hour_branch) != hour_pillar_want:
                    continue
                hits.append((year, month, day, HOUR_BY_BRANCH[hour_branch]))
                if len(hits) >= limit:
                    return hits
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pillars")
    ap.add_argument("--start", type=int, default=1850)
    ap.add_argument("--end", type=int, default=2035)
    args = ap.parse_args()
    hits = solve(args.pillars, args.start, args.end)
    if not hits:
        print(f"无解：{args.pillars} 在 {args.start}-{args.end} 内")
        return 1
    for y, m, d, h in hits:
        print(f"{y}-{m:02d}-{d:02d} {h:02d}:00")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
