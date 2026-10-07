# -*- coding: utf-8 -*-
"""对四条拒算裁决做本地全库互证（20158 行原著 + 三卷转录）。

裁决清单：
  A. L38「天数一十有五」 vs L42「天数二十五为正」
  B. L56 阳数偏少 vs L83 以弱敌强 判语相反且重叠
  C. L36「自正月立春后…三阳交泰」 vs L99「自冬至后至雨水前，正三阳交泰之时」
  D. 「太过有尤」「有悔」需卦爻四元组入参
"""
from __future__ import annotations

import io
import re
from pathlib import Path

ORIG = Path(r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
            r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt")
RAW = Path(r"D:\shuntian_heluo\data\heluo\guajie_raw")

lines = io.open(ORIG, encoding="utf-8").read().split("\n")
print(f"全库 {len(lines)} 行\n")


def show(title: str, kws: list[str], limit: int = 14, ctx: int = 0) -> None:
    print("=" * 78)
    print(title)
    print("=" * 78)
    seen = set()
    for kw in kws:
        hits = [i for i, s in enumerate(lines) if kw in s]
        print(f"\n【{kw}】 命中 {len(hits)} 行")
        for i in hits[:limit]:
            if i in seen:
                continue
            seen.add(i)
            frag = lines[i]
            # 截断长句
            frag = frag if len(frag) <= 230 else frag[:230] + "…"
            print(f"  L{i+1}| {frag}")
            if ctx:
                for j in range(i + 1, min(i + 1 + ctx, len(lines))):
                    if lines[j].strip():
                        print(f"      L{j+1}| {lines[j][:230]}")
    print()


# ── A. 天数正数到底是几 ──
show("A. 天数至弱 L38「天数一十有五」——天数之正是 15 还是 25？",
     ["一十有五", "天数十五", "至弱", "不满一策", "天数二十五", "天数之正", "正数"])

# ── A2. 「策」到底是什么 ──
show("A2.「策」的定义——一策等于几（决定「四五六七八不满一策」怎么解）",
     ["一策", "策数", "论九", "两策", "二策", "十八", "为正"])

# ── B. 阳数偏少 vs 以弱敌强 ──
show("B. L56 阳数偏少 vs L83 以弱敌强——判语是否真的相反？有无裁决文字？",
     ["阳数偏少", "以弱敌强", "孤阳不偶", "以强伏弱", "有阴无阳", "灭顶", "孤睽",
      "有福无寿", "判其轻重", "轻重"])

# ── C. 三阳交泰 ──
show("C.「三阳交泰」的两种窗口——原典自身是否给过统一口径？",
     ["三阳交泰", "三阳", "交泰", "未泰", "立春", "冬至后", "雨水前"])

# ── D. 有尤 / 有悔 ──
show("D.「太过有尤」「有悔」——原典是否给过「爻多寡」的计数法？",
     ["有尤", "有悔", "阳爻多", "阴爻多", "爻多", "立阳爻", "立阴爻", "居阳", "居阴",
      "爻位辞理无援", "无援"])

# ── 转录件保真度 ──
print("=" * 78)
print("转录件 vs 全库：三条关键句是否一字不差（判断讹在底本还是在转录）")
print("=" * 78)
KEY = [
    "天数一十有五，如只得四五六七八数，此不满一策，是谓至弱",
    "天数二十五为正",
    "阳数偏少　天数二十有五，只得四、五、六至二十四，地数三十是也",
    "以弱敌强　地数三十至四十、五十、六十以上，天数只得二十四以下是也",
    "自正月立春后，三阳交泰",
    "自冬至后至雨水前，正三阳交泰之时",
    "太过有尤　阳数胜阴数，卦中阳爻多，又值月令立阳爻",
]
full = "\n".join(lines)
for name in ("河洛真数_起例卷之上.txt", "河洛真数_起例卷之中.txt", "河洛真数_起例卷之下.txt"):
    p = RAW / name
    if not p.exists():
        continue
    t = io.open(p, encoding="utf-8").read()
    print(f"\n--- {name} ---")
    for k in KEY:
        print(f"  全库={k in full!s:<5} 转录={k in t!s:<5}  {k[:34]}")
