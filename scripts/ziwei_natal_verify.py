#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微排盘准确率核验（生产适配器 vs 原生口诀实现）。

**为什么需要它**：生产排盘是 iztro（npm）的 subprocess 包装，而历史 Golden
数据集（cases/golden/ziwei_golden_set.json）本身也由 iztro 生成，
拿它验证 iztro 是自洽循环。本脚本用 `tongshu.engines.ziwei_natal`
（按《紫微斗数全书》通行安星诀独立实现，不依赖 iztro）作真值，
逐字段核对生产输出。

核对字段：
  命宫地支 / 身宫地支 / 五行局 / 紫微星宫 / 十四主星宫位 /
  14 辅煞（六吉六煞+禄存+天马）宫位 / 命宫主星（含空宫借对宫）/
  生年四化落命宫 / 亮度表是否注入

用法（Windows PowerShell）：
    $env:PYTHONPATH='src;.'; $env:PYTHONUTF8='1'
    python scripts/ziwei_natal_verify.py                 # 默认 120 盘抽样
    python scripts/ziwei_natal_verify.py 500             # 抽样 500 盘
    python scripts/ziwei_natal_verify.py 500 --year 1983

前置条件：
  - 生产适配器需要 node + iztro：`npm install`（node_modules 已在 .gitignore）
  - 若 node_modules 缺失，本脚本会明确报错，而不是拿到 stub 假绿。
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

JU = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
CORE_MINOR = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存",
              "擎羊", "陀罗", "火星", "铃星", "地空", "地劫", "天马"}


def _check_node() -> None:
    if not (ROOT / "node_modules" / "iztro").exists():
        raise SystemExit(
            "node_modules/iztro 缺失：生产适配器无法排盘。先在本仓库执行 npm install，"
            "或设置 TONGSHU_ALLOW_ZIWEI_STUB=1 只会得到 stub（本脚本拒绝在 stub 上判定准确率）。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("count", nargs="?", type=int, default=120)
    ap.add_argument("--year", type=int, default=None, help="限定出生年份（缺省 1950-2005 随机）")
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    _check_node()

    from lunar_python import Solar

    from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter
    from tongshu.engines.ziwei_natal import build_natal_chart

    rng = random.Random(args.seed)
    adapter = ZiweiSolarAdapter()

    fields = ["命宫支", "身宫支", "五行局", "紫微星", "十四主星", "辅煞星", "命宫主星",
              "生年四化", "亮度注入", "长生十二神", "博士十二神", "将前十二神", "岁前十二神"]
    miss = {f: 0 for f in fields}
    failures: list[str] = []
    n = 0
    leap_counted = 0

    for _ in range(args.count):
        y = args.year or rng.randint(1950, 2005)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28)
        h = rng.choice([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22])
        g = rng.choice(["male", "female"])

        ch = adapter.compute(y, m, d, h, g)
        lun = Solar.fromYmd(y, m, d).getLunar()
        is_leap = lun.getMonth() < 0
        if is_leap:
            leap_counted += 1
        hour_idx = (h + 1) // 2 % 12
        nat = build_natal_chart(lun.getYear(), abs(lun.getMonth()), lun.getDay(),
                                hour_idx, g, is_leap=is_leap)
        nd = nat.to_dict()

        probs = []
        if ch.soul_earthly_branch != nd["soul_branch"]:
            miss["命宫支"] += 1
            probs.append(f"命宫支 {nd['soul_branch']}→{ch.soul_earthly_branch}")
        if ch.body_earthly_branch != nd["body_branch"]:
            miss["身宫支"] += 1
            probs.append(f"身宫支 {nd['body_branch']}→{ch.body_earthly_branch}")
        if JU.get(ch.fiveElementsClass) != nat.ju:
            miss["五行局"] += 1
            probs.append(f"五行局 {nat.ju}→{ch.fiveElementsClass}")

        # 生产盘 palaces 主星是拼音键，转回中文对照
        from tongshu.engines.ziwei_engine import CHINESE_STAR_TO_KEY
        key2zh = {v: k for k, v in CHINESE_STAR_TO_KEY.items()}
        prod_major = {}
        prod_minor = {}
        for name, p in ch.palaces.items():
            br = p.get("branch", "")
            prod_major[br] = [key2zh.get(k, k) for k in (p.get("major") or [])]
            prod_minor[br] = list(p.get("minor") or [])

        ziwei_prod = next((br for br, stars in prod_major.items() if "紫微" in stars), "")
        if ziwei_prod != nd["ziwei_branch"]:
            miss["紫微星"] += 1
            probs.append(f"紫微 {nd['ziwei_branch']}→{ziwei_prod}")

        by_branch = {p["branch"]: p for p in nd["palaces"].values()}
        for br, stars in by_branch.items():
            want = set(stars["major"])
            have = set(prod_major.get(br, []))
            # 空宫借星后命宫会带对宫主星，属口径差异，不判错
            if want != have and br != BRANCHES[nat.soul]:
                miss["十四主星"] += 1
                probs.append(f"{br}宫主星 {sorted(want)}→{sorted(have)}")
            want_minor = {s for s in stars["minor"] if s in CORE_MINOR}
            have_minor = {s for s in prod_minor.get(br, []) if s in CORE_MINOR}
            if want_minor != have_minor:
                miss["辅煞星"] += 1
                probs.append(f"{br}宫辅煞 {sorted(want_minor)}→{sorted(have_minor)}")

        # 命宫主星：空宫必借对宫（生产应已借星）
        soul_br = nd["soul_branch"]
        soul_majors = set(by_branch[soul_br]["major"])
        if not soul_majors:
            soul_majors = set(by_branch[BRANCHES[(BRANCHES.index(soul_br) + 6) % 12]]["major"])
        if {key2zh.get(k, k) for k in ch.soul_palace_main_stars} != soul_majors:
            miss["命宫主星"] += 1
            probs.append(f"命宫主星 {sorted(soul_majors)}→{ch.soul_palace_main_stars}")

        # 生年四化入命宫：按**命宫实际星曜**（主星+四化相关辅星）判定，
        # 不借用对宫——借星是论事口径，不改变「化星是否落在命宫」的事实。
        phys_major = set(by_branch[soul_br]["major"])
        phys_minor = {s for s in by_branch[soul_br]["minor"] if s in CORE_MINOR}
        expected_sihua = []
        for star, kind in nat.sihua.items():
            if star in phys_major or star in phys_minor:
                expected_sihua.append({"禄": "HUA_LU", "权": "HUA_QUAN",
                                       "科": "HUA_KE", "忌": "HUA_JI"}[kind])
        if sorted(expected_sihua) != sorted(ch.soul_palace_sihua):
            miss["生年四化"] += 1
            probs.append(f"四化 {expected_sihua}→{ch.soul_palace_sihua}")

        # 亮度注入（格式：庙/旺/利/陷）
        bright_ok = all(
            set(p.get("brightness") or {}) == set(p.get("major") or [])
            for p in ch.palaces.values() if p.get("major")
        ) and any(p.get("brightness") for p in ch.palaces.values())
        if not bright_ok:
            miss["亮度注入"] += 1
            probs.append("brightness 缺失或不完整")

        # 四组十二神（生产 palace_data 里逐宫携带）
        god_map = {"长生十二神": ("changsheng", "changsheng12"),
                   "博士十二神": ("boshi", "boshi12"),
                   "将前十二神": ("jiangqian", "jiangqian12"),
                   "岁前十二神": ("suiqian", "suiqian12")}
        for field, (nat_key, prod_key) in god_map.items():
            want_by_branch = {BRANCHES[b]: name for b, name in nat.twelve_gods[nat_key].items()}
            got_by_branch = {p.get("branch"): p.get(prod_key) for p in ch.palaces.values()}
            if {k: v for k, v in want_by_branch.items()} != {k: v for k, v in got_by_branch.items() if k}:
                miss[field] += 1
                probs.append(f"{field} 不一致")

        n += 1
        if probs:
            failures.append(f"{y}-{m}-{d} {h}h {g}: " + "; ".join(probs))

    print(f"核验盘数 = {n}（原生口诀实现 vs 生产适配器）；其中闰月盘 {leap_counted}（按「前半月本月/后半月次月」折算）")
    for f in fields:
        bad = miss[f]
        print(f"  {f:6s}  不一致 {bad:4d}  准确率 {100 * (n - bad) / n:6.1f}%")
    if args.verbose or failures:
        print(f"\n明细（最多 25 条，共 {len(failures)} 条）：")
        for line in failures[:25]:
            print("  " + line)
    return 0 if sum(miss.values()) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
