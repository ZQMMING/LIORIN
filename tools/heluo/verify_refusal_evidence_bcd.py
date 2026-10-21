# -*- coding: utf-8 -*-
"""B/C/D 三项的精确取证。

B. 阳数偏少(L992-995) vs 以弱敌强(L1073-1080) —— 诗断是否同向？
C. 「三阳交泰」全部出现处 + L714 是否为 L1121 的平行例证
D. 全库是否有「爻多寡」的计数门槛（三爻/过半/多数…）
"""
from __future__ import annotations

import io

ORIG = (r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
        r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt")
L = io.open(ORIG, encoding="utf-8").read().split("\n")


def block(title: str, a: int, b: int) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)
    for i in range(a - 1, min(b, len(L))):
        s = L[i].strip()
        if s:
            print(f"L{i+1}| {s}")
    print()


block("B-1　阳数偏少 L992–L995（含诗断）", 992, 995)
block("B-2　以弱敌强 L1073–L1080（含诗断）", 1073, 1080)
block("B-3　孤阳不偶 L974–L980（参照：同为余数分判，判语强弱如何）", 974, 980)

print("=" * 78)
print("C　「三阳交泰」全库全部出现处")
print("=" * 78)
for i, s in enumerate(L):
    if "三阳交泰" in s:
        print(f"L{i+1}| {s.strip()[:400]}")
print()
block("C-2　L714（疑为 L1121 的平行例证：冬至后—雨水前 + 天数余奇）", 714, 717)

print("=" * 78)
print("D　全库检索「爻多寡」是否有计数门槛")
print("=" * 78)
for kw in ["三爻", "过半", "多数", "爻数", "多寡", "四爻", "五爻", "阳爻三", "阴爻三",
           "爻之多少", "多少之爻", "爻多则", "得三爻"]:
    hits = [i for i, s in enumerate(L) if kw in s]
    print(f"\n【{kw}】命中 {len(hits)}")
    for i in hits[:4]:
        print(f"  L{i+1}| {L[i].strip()[:220]}")
