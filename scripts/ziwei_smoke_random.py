#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微随机盘冒烟测试（Z80-E 续）——跨盘写死残留 / 文实一致性 / 重复句 / 领域污染。

背景
----
Z80-B/C/D（千问会话）已修复跨盘假语义（借宫/对宫写死案例盘），并跑过 30 盘
冒烟，但**冒烟脚本未落盘**。本脚本把该冒烟固化为可复用工具，并扩大盘数与
检查维度，用于持续防回归。

检查项
------
A. 崩溃        —— 算/辨/解任一层抛异常
B. 文实一致性  —— 断语提到的主星/辅星是否在本盘实际存在（抓"硬编造"）
C. 借宫真实性  —— "借对宫X宫A、B之气"：A/B 须在本盘存在
D. 重复句      —— 同一条结论内出现重复片段（>=8 字）
E. 领域污染    —— 领域断语混入其他领域主题词（如健康里谈事业）

用法
----
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_smoke_random.py
    D:/shuntian/.venv/Scripts/python.exe scripts/ziwei_smoke_random.py --n 60 --seed 20261014
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402
from tongshu.engines.ziwei.rules.interpretation import build_life_reading  # noqa: E402
from tongshu.engines.ziwei.rules.multi_method import (  # noqa: E402
    compute_multi_method_signals,
)
from tongshu.engines.ziwei.rules.domain_reading import (  # noqa: E402
    build_domain_readings,
)

MAIN_STARS = ["紫微", "天府", "太阳", "天梁", "武曲", "太阴", "天同", "天机",
              "贪狼", "廉贞", "破军", "七杀", "巨门", "天相"]
AUX_STARS = ["文昌", "文曲", "左辅", "右弼", "天魁", "天钺", "擎羊", "陀罗",
             "火星", "铃星", "地空", "地劫", "禄存", "天马", "红鸾", "天喜",
             "天姚", "天刑", "咸池"]
ALL_STARS = MAIN_STARS + AUX_STARS

# 领域主题词：用于检测领域污染（他领域词大量出现）
DOMAIN_FOREIGN = {
    "健康": ["项目管理", "技术研发", "升迁", "投资", "婚姻配偶"],
    "学业": ["破财", "慢性病"],
    "事业": ["慢性病", "妇科"],
    "财运": ["慢性病", "妇科"],
}

BORROW_RE = re.compile(r"借对宫[\u4e00-\u9fa5]{2}宫([\u4e00-\u9fa5、]+)之气")


def gen_chart(rng: random.Random):
    """生成一张随机盘参数（农历）。"""
    y = rng.randint(1950, 2005)
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)
    h = rng.randint(0, 23)
    g = rng.choice(["male", "female"])
    return (y, m, d), h, g


def collect_present_stars(chart) -> set:
    """本盘实际出现的所有星曜。"""
    present = set()
    for _p, pd in (chart.palaces or {}).items():
        present |= set(pd.get("major", []) or [])
        present |= set(pd.get("minor", []) or [])
        present |= set(pd.get("adjective", []) or [])
    return present


def split_sentences(text: str) -> list:
    return [s for s in re.split(r"[；;。\n]", text) if s.strip()]


def check_text_facts(text: str, present: set) -> list:
    """断语提到的星曜是否在本盘存在（全局存在性，抓硬编造）。"""
    bad = []
    for s in ALL_STARS:
        if s in text and s not in present:
            bad.append(s)
    return bad


def check_borrow(text: str, present: set) -> list:
    """'借对宫X宫A、B之气' → A/B 须在本盘存在。"""
    bad = []
    for m in BORROW_RE.finditer(text):
        stars = [s for s in m.group(1).split("、") if s]
        missing = [s for s in stars if s not in present]
        if missing:
            bad.append(f"借宫提到不存在的星: {missing}")
    return bad


def check_dup(text: str) -> list:
    """同一条结论内的重复片段（>=8 字）。"""
    sents = split_sentences(text)
    seen, dups = set(), []
    for s in sents:
        key = s.strip()
        if len(key) >= 8:
            if key in seen:
                dups.append(key)
            seen.add(key)
    return dups


def check_domain_pollution(domain: str, text: str) -> list:
    hits = []
    for kw in DOMAIN_FOREIGN.get(domain, []):
        if kw in text:
            hits.append(kw)
    return hits


def _bigrams(s: str) -> set:
    s = re.sub(r"[\s；;。，,、（）()]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def similarity(a: str, b: str) -> float:
    """字符 bigram Jaccard 相似度（0~1）。"""
    ga, gb = _bigrams(a), _bigrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="随机盘数量")
    ap.add_argument("--seed", type=int, default=20261014, help="随机种子")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    eng = ZiweiEngine()

    crashes, fact_bads, borrow_bads, dup_bads, poll_bads = [], [], [], [], []
    ok_charts = 0
    # F: 跨盘区分性 —— (宫名, 断语句) → 出现过的「不同宫内星组合」集合。
    #    若同一宫位的同一句断语对应 >=2 个不同星组合，说明该句与星曜无关
    #    （= 写死盘面），是跨盘写死残留的强信号。
    palace_text_stars = defaultdict(set)
    # G: 同宫不同星组合的断语相似度 —— {宫名: {frozenset(星): 断语}}
    #    不同星组合本应产出不同断语；若两句高度雷同，说明该段文字与星曜
    #    弱相关（模板化过度/写死），是 F 之外的加严检查。
    palace_star_text = defaultdict(dict)

    for i in range(args.n):
        lunar, hour, gender = gen_chart(rng)
        tag = f"#{i+1} 农历{lunar} {hour}时 {gender}"
        try:
            chart = eng.full_chart(lunar, hour, gender)
            present = collect_present_stars(chart)
            sig = compute_multi_method_signals(chart)
            reading = build_life_reading(chart, sig, target_year=2026)
            domains = build_domain_readings(chart, eng.get_all_zihua(chart))
            ok_charts += 1

            # 12 维断语
            for d in reading.dimensions:
                txt = (d.conclusion or "").strip()
                if not txt:
                    continue
                for s in check_text_facts(txt, present):
                    fact_bads.append((tag, d.dimension, s))
                for b in check_borrow(txt, present):
                    borrow_bads.append((tag, d.dimension, b))
                for x in check_dup(txt):
                    dup_bads.append((tag, d.dimension, x))

            # 宫位逐宫解读（用于 F/G 跨盘区分性检测）
            for pr in getattr(domains, "palace_readings", []) or []:
                txt = (pr.conclusion or "").strip()
                if txt:
                    star_key = frozenset(pr.stars or [])
                    palace_text_stars[(pr.palace, txt)].add(star_key)
                    palace_star_text[pr.palace].setdefault(star_key, txt)

            # 领域断语
            for dr in getattr(domains, "domain_readings", []) or []:
                txt = (dr.conclusion or "").strip()
                if not txt:
                    continue
                for s in check_text_facts(txt, present):
                    fact_bads.append((tag, f"领域-{dr.domain}", s))
                for b in check_borrow(txt, present):
                    borrow_bads.append((tag, f"领域-{dr.domain}", b))
                for x in check_dup(txt):
                    dup_bads.append((tag, f"领域-{dr.domain}", x))
                for kw in check_domain_pollution(dr.domain, txt):
                    poll_bads.append((tag, dr.domain, kw))
        except Exception as e:  # noqa: BLE001
            crashes.append((tag, f"{type(e).__name__}: {e}"))

    print("=" * 72)
    print(f"紫微随机盘冒烟 — {args.n} 盘（seed={args.seed}）")
    print("=" * 72)
    print(f"  成功排盘+全链路: {ok_charts}/{args.n}")
    print(f"  A 崩溃        : {len(crashes)}")
    print(f"  B 文实不一致  : {len(fact_bads)}")
    print(f"  C 借宫失真    : {len(borrow_bads)}")
    # F 跨盘写死：同一宫位的同一句断语对应 >=2 个不同星组合
    hardcoded = sorted(
        [(pal, txt, len(c)) for (pal, txt), c in palace_text_stars.items()
         if len(c) >= 2 and len(txt) >= 10],
        key=lambda x: -x[2],
    )
    print(f"  D 重复句      : {len(dup_bads)}")
    print(f"  E 领域污染    : {len(poll_bads)}")
    # G 断语雷同：同宫不同星组合的断语相似度 >= 阈值（模板化过度/写死）
    SIM_THRESH = 0.85
    near_dup = []
    for pal, mapping in palace_star_text.items():
        items = [(s, t) for s, t in mapping.items() if len(t) >= 20]
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                s1, t1 = items[i]
                s2, t2 = items[j]
                if s1 == s2:
                    continue
                # 主星相同、仅辅星不同 → 主体文案本就应一致（差异部分正是
                # 辅星语句），不算「雷同」。只比较主星组合不同的样本。
                m1 = {x for x in s1 if x in MAIN_STARS}
                m2 = {x for x in s2 if x in MAIN_STARS}
                if m1 == m2:
                    continue
                sim = similarity(t1, t2)
                if sim >= SIM_THRESH:
                    near_dup.append(
                        (pal, f"sim={sim:.2f}",
                         "／".join(sorted(s1)), "／".join(sorted(s2)),
                         t1[:34]))
    near_dup.sort(key=lambda x: -float(x[1].split("=")[1]))

    print(f"  F 跨盘写死    : {len(hardcoded)}")
    print(f"  G 断语雷同    : {len(near_dup)}  (同宫不同星组合 sim>={SIM_THRESH})")
    print()

    for label, rows in (("A 崩溃", crashes), ("B 文实不一致", fact_bads),
                        ("C 借宫失真", borrow_bads), ("D 重复句", dup_bads),
                        ("E 领域污染", poll_bads), ("F 跨盘写死", hardcoded),
                        ("G 断语雷同", near_dup)):
        if not rows:
            continue
        print(f"── {label}（前 10 条）──")
        for r in rows[:10]:
            print("   ", " | ".join(str(x) for x in r))
        if len(rows) > 10:
            print(f"    ... 共 {len(rows)} 条")
        print()

    total = (len(crashes) + len(fact_bads) + len(borrow_bads)
             + len(dup_bads) + len(poll_bads) + len(hardcoded) + len(near_dup))
    print("=" * 72)
    print(f"结论：{'★ 全绿（0 缺陷）' if total == 0 else f'⚠ 共 {total} 条待查'}")
    print("=" * 72)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
