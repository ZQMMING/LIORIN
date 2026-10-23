# -*- coding: utf-8 -*-
"""真实命例全量对拍（河洛引擎地基验收）。

**用途**
用公开真实命例库（`bazi_cases_full.json`，1681 例）验收河洛引擎的
**历法口径 / 节气边界 / 时柱推断**整条链 —— 这是引擎的地基：
它错了，后面所有判据全错，而表结构/接口形状/变异演练**全都发现不了**。

**两条路径**
- A 独立入口 `HeluoAdapter.compute()` → `BaziEngine`：**不做真太阳时**（标准时口径）
- B 正式链路 `compute_from_context()` → `TimeResolver`：**做真太阳时**（按出生地经度）

**判读**
- 路径A 的可复现率 = **地基正确性**（公开命例多按北京时间排定，与 A 同口径）；
- 路径B 与命例的差 = **真太阳时口径 vs 标准时口径**的差（西部尤显），
  **不是缺陷** —— 详见 `docs/heluo/河洛引擎案例验证报告_20261024.md` §4。

**用法**
```
python tools/heluo/verify_real_cases.py                # 全量 1681 例
python tools/heluo/verify_real_cases.py --limit 200    # 快跑
```

⚠ 本脚本依赖**包外**原始命例库（`D:\\顺天系统资料\\...`），
不是随包守卫；随包可跑的是 `tests/heluo/test_heluo_case_regression.py`
（内嵌 58 条样本）。
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from heluo_engine.adapter import HeluoAdapter
from heluo_engine.engines.bazi_engine import BaziEngine
from heluo_engine.engines.time.resolver import TimeResolver

RAW = pathlib.Path(
    r"D:\顺天系统资料\GitHub命例案例\bazi-case-list\bazi_cases_full.json")
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
MAX_PLAUSIBLE = 2025
MIN_AGE_AT_EVENT = 16


def gz_str(gz):
    return GAN[gz.tg] + ZHI[gz.dz]


def build_index(y0=1900, y1=2100):
    import sxtwl
    hour_map = collections.defaultdict(list)
    dt = datetime.date(y0, 1, 1)
    end = datetime.date(y1, 12, 31)
    while dt <= end:
        d = sxtwl.fromSolar(dt.year, dt.month, dt.day)
        ymd = (gz_str(d.getYearGZ()), gz_str(d.getMonthGZ()), gz_str(d.getDayGZ()))
        for h in range(0, 24):
            hg = gz_str(d.getHourGZ(h, bool(h >= 23)))
            hour_map[(ymd, hg)].append((dt.year, dt.month, dt.day, h))
        dt += datetime.timedelta(days=1)
    return hour_map


def event_years(c):
    txt = " ".join(str(c.get(k) or "") for k in ("jobInfo", "job", "caseDetail"))
    if isinstance(c.get("caseDetail"), list):
        txt += " " + " ".join(map(str, c["caseDetail"]))
    import re
    return sorted({int(y) for y in re.findall(r"(19\d{2}|20[0-2]\d)\s*年", txt)})


def resolve(raw, hour_map):
    """四柱 → (公历日期, 候选小时)；60 年一轮 ⇒ 用事件年份消歧。"""
    out = []
    for c in raw:
        bz = (c.get("bazi") or "").split()
        if len(bz) != 4:
            continue
        cands = hour_map.get((tuple(bz[:3]), bz[3]))
        if not cands:
            continue
        plausible = [x for x in cands if x[0] <= MAX_PLAUSIBLE] or cands
        ev = event_years(c)
        if ev:
            ok = [x for x in plausible if x[0] <= min(ev) - MIN_AGE_AT_EVENT]
            pool = ok or plausible
        else:
            pool = plausible
        y, m, dd, h = max(pool, key=lambda x: x[0])
        out.append({**c, "date": [y, m, dd], "hours": sorted({x[3] for x in cands if x[0] == y})})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 例")
    ap.add_argument("--raw", default=str(RAW), help="原始命例库路径")
    args = ap.parse_args()

    raw = json.loads(pathlib.Path(args.raw).read_text(encoding="utf-8"))
    print(f"原始命例 {len(raw)} 例；建索引…")
    t0 = time.time()
    hour_map = build_index()
    cases = resolve(raw, hour_map)
    if args.limit:
        cases = cases[:args.limit]
    print(f"反查完成 {len(cases)} 例（{time.time()-t0:.1f}s）")

    tr, ad, be = TimeResolver(), HeluoAdapter(), BaziEngine()
    st = collections.Counter()
    errs = collections.Counter()
    degr = collections.Counter()
    t0 = time.time()
    for i, c in enumerate(cases):
        y, m, dd = c["date"]
        gender = "male" if c.get("gender") == "男" else "female"
        want = c.get("bazi", "").split()
        hours = c["hours"] or [12]
        try:
            loc = tr.lookup(c.get("address") or "")
        except Exception:
            loc = None
        st["loc_hit" if loc else "loc_miss"] += 1

        hitA = False
        for h in hours:
            try:
                p = be.compute((y, m, dd, h), gender=gender).get_pillars_chinese()
                got = [p["year"], p["month"], p["day"], p["hour"]]
                if got == want:
                    hitA = True
                    break
            except Exception as e:
                errs[f"A:{type(e).__name__}"] += 1
        st["A_ok" if hitA else "A_miss"] += 1

        hitB = False
        for dh in (-1, 0, 1):
            for h in hours:
                for hh in (h - 1, h, h + 1):
                    if not (0 <= hh <= 23):
                        continue
                    try:
                        ctx = tr.resolve_context(
                            birth_date=datetime.date(y, m, dd) + datetime.timedelta(days=dh),
                            hour=hh, minute=0, timezone=None,
                            location=(loc.name_zh if loc else "北京"), gender=gender)
                        r = ad.compute_from_context(ctx, gender=gender)
                        bl = list(r.bazi)
                        got = ["".join(bl[0]), "".join(bl[1]),
                               "".join(bl[2]), "".join(bl[3])]
                        if got == want:
                            hitB = True
                            break
                        if getattr(r, "era_source", None) not in (None, "derived"):
                            degr[f"era_source={r.era_source}"] += 1
                        if getattr(r, "yuan_qi_error", None):
                            degr["yuan_qi_error"] += 1
                    except Exception as e:
                        errs[f"B:{type(e).__name__}"] += 1
                if hitB:
                    break
            if hitB:
                break
        st["B_ok" if hitB else "B_miss"] += 1
        if (i + 1) % 400 == 0:
            print(f"  … {i+1}/{len(cases)} ({time.time()-t0:.0f}s)")

    n = max(1, len(cases))
    print(f"\n===== 真实命例对拍（{n} 例，{time.time()-t0:.0f}s）=====")
    print(f"出生地解析：命中 {st['loc_hit']} / 未命中 {st['loc_miss']}"
          f"（{st['loc_hit']/n*100:.1f}%）")
    print(f"路径A（标准时·无真太阳时）：四柱可复现 {st['A_ok']}/{n} = {st['A_ok']/n*100:.2f}%")
    print(f"路径B（真太阳时+真实经度）：四柱可复现 {st['B_ok']}/{n} = {st['B_ok']/n*100:.2f}%")
    print(f"异常 {sum(errs.values())}：")
    for k, v in errs.most_common(8):
        print(f"   {v:>5d} × {k[:90]}")
    print(f"静默降级 {sum(degr.values())}：")
    for k, v in degr.most_common(8):
        print(f"   {v:>5d} × {k}")
    print("\n判读：路径A = 地基正确性；路径B 的差 = 真太阳时口径 vs 标准时口径（西部尤显），非缺陷。")


if __name__ == "__main__":
    main()
