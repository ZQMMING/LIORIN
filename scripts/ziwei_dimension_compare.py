#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""8 维 vs 12 维 实际输出对照 — 案例实跑。

目的
----
不看表结构、不看映射图，直接跑真实命盘，把两套体系的**实际文案输出**
并排打印出来，回答：「同一张盘，8 维给什么、12 维给什么、差在哪」。

用法
----
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_dimension_compare.py
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_dimension_compare.py --case 2
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.CRITICAL)

from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402
from tongshu.engines.ziwei.rules.answer_layer import build_answer  # noqa: E402
from tongshu.engines.ziwei.rules.dimension_bridge import (  # noqa: E402
    align_answer_to_dimensions,
)
from tongshu.engines.ziwei.rules.interpretation import (  # noqa: E402
    build_life_reading,
)
from tongshu.engines.ziwei.rules.multi_method import (  # noqa: E402
    compute_multi_method_signals,
)

# 案例：(名称, 农历年月日, 时辰, 性别)
CASES = [
    ("文章盘 1983.11.3 午时女（千文千问基准盘）", (1983, 9, 29), 12, "female"),
    ("男命 1980.6.22 午时男（项目基准盘）",        (1980, 5, 10), 12, "male"),
    ("女命 1990.3.15 巳时女",                     (1990, 2, 19), 10, "female"),
]


def _truncate(text: str, n: int = 150) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + "…"


def run_case(name: str, lunar, hour: int, gender: str, show_full: bool) -> None:
    print("\n" + "═" * 78)
    print(f"案例：{name}")
    print(f"输入：农历 {lunar[0]}-{lunar[1]:02d}-{lunar[2]:02d}  {hour}时  {gender}")
    print("═" * 78)

    eng = ZiweiEngine()
    chart = eng.full_chart(lunar, hour, gender)
    sig = compute_multi_method_signals(chart)

    # ── 8 维 ──
    answer = build_answer(chart)
    print("\n" + "─" * 78)
    print("【8 维体系】answer_layer.build_answer()")
    print("─" * 78)
    counts = answer["summary"]["dimension_counts"]
    for dim in answer["dimensions"]:
        items = answer["answer"][dim]
        print(f"\n▎{dim}  （{counts[dim]} 条）")
        if not items:
            print("    （空）")
            continue
        limit = len(items) if show_full else 2
        for it in items[:limit]:
            src = it.get("source", "?")
            rid = it.get("rule_id", "")
            print(f"    [{src}] {rid}")
            print(f"      {_truncate(it.get('text', ''))}")
        if len(items) > limit:
            print(f"    … 另有 {len(items) - limit} 条")

    # ── 12 维 ──
    reading = build_life_reading(chart, sig, target_year=2026)
    print("\n" + "─" * 78)
    print("【12 维体系】interpretation.build_life_reading()")
    print("─" * 78)
    for d in reading.dimensions:
        conc = d.conclusion or ""
        n_parts = conc.count("；") + 1 if conc else 0
        print(f"\n▎{d.dimension}  （宫位={d.palace}，{n_parts} 段）")
        print(f"    {_truncate(conc, 400 if show_full else 180)}")

    # ── 对齐桥 ──
    al = align_answer_to_dimensions(answer)
    print("\n" + "─" * 78)
    print("【对齐桥】8 维 → 12 维 投射结果")
    print("─" * 78)
    cov = al.coverage
    print(f"  mapped_items={cov['mapped_items']}  "
          f"cross_items={cov['cross_items']}  "
          f"unmapped={cov['unmapped_dimensions']}")
    print(f"\n  有投射来源的 12 维：")
    for dim in reading_order():
        items = al.by_dimension.get(dim, [])
        if items:
            srcs = {it["from_answer_dimension"] for it in items}
            print(f"    {dim:<8} ← {sorted(srcs)}  （{len(items)} 条）")
    print(f"\n  无投射来源的 12 维（由 12 维层自身覆盖）：")
    empty = [d for d in reading_order() if not al.by_dimension.get(d)]
    print(f"    {empty}")
    print(f"\n  跨维池（无 12 维对应）：")
    from collections import Counter
    cc = Counter(c.dimension for c in al.cross_dimension)
    print(f"    {dict(cc)}")


def reading_order():
    from tongshu.engines.ziwei.rules.interpretation import DIMENSION_ORDER
    return DIMENSION_ORDER


def main() -> int:
    ap = argparse.ArgumentParser(description="8维 vs 12维 输出对照")
    ap.add_argument("--case", type=int, default=None,
                    help="只跑第 N 个案例（从 1 开始）")
    ap.add_argument("--full", action="store_true",
                    help="打印完整文本（不截断）")
    args = ap.parse_args()

    cases = CASES
    if args.case is not None:
        cases = [CASES[args.case - 1]]

    for name, lunar, hour, gender in cases:
        run_case(name, lunar, hour, gender, args.full)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
