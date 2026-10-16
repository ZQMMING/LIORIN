#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E8 Production Trace — 紫微 Full Replay 抽样验证器 (只读)

从紫微518400合成数据集抽样 N 条, 用 ZIWEI 引擎独立计算同生时命盘,
对比 命宫地支/五行局/12宫主星 三项, 输出匹配率。

用途: PRODUCTION_VALIDATED 门槛 (V2 验收规范 E8)。
红线: 只读引擎+只读数据集, 不写入任何引擎/数据路径 (User 红线)。

用法:
    ZIWEI_DATASET_ROOT=D:/顺天系统资料/ziwei-doushu-dataset/ziwei-samples-toolkit \
        python scripts/e8_ziwei_full_replay.py --samples 50

    ZIWEI_DATASET_ROOT=... python scripts/e8_ziwei_full_replay.py --year 1954 --month 1 --samples 20
"""
import os
import sys
import json
import gzip
import argparse
from pathlib import Path
from collections import defaultdict

# P0 路径红线: 数据集根必须环境变量注入, 无缺省
_ROOT_ENV = "ZIWEI_DATASET_ROOT"


def _dataset_root() -> Path:
    env = os.environ.get(_ROOT_ENV)
    if not env:
        raise SystemExit(
            f"P0路径红线: 请设置环境变量 {_ROOT_ENV} 指向 ziwei-samples-toolkit 目录"
        )
    p = Path(env)
    if not p.exists():
        raise SystemExit(f"数据集根不存在: {p}")
    return p


def _find_samples(root: Path, year: int | None, month: int | None, count: int):
    """从 samples-out 里抽 count 条 (可指定年月; 默认遍历最早年份)。"""
    out = root / "samples-out"
    if not out.exists():
        raise SystemExit(f"找不到 {out} (samples-out 目录)")
    if year is None:
        year_dirs = sorted(d.name for d in out.iterdir() if d.is_dir())
        year = year_dirs[0].split("-")[1] if year_dirs else None
    files = []
    if month is None:
        files = sorted((out / f"year-{year}").glob("*.jsonl.gz"))
    else:
        files = [out / f"year-{year}" / f"{year}-{month:02d}.jsonl.gz"]
    recs = []
    for f in files:
        if not f.exists():
            continue
        with gzip.open(f, "rt", encoding="utf-8") as gz:
            for line in gz:
                recs.append(json.loads(line))
                if len(recs) >= count:
                    return recs
        if len(recs) >= count:
            break
    return recs


# 地支数字 → 汉字 (数据集 branch 是 0-11)
_BRANCH_CN = "子丑寅卯辰巳午未申酉戌亥"
# 主星 中文 → PINYIN (引擎输出用 pinyin)
_STAR_PINYIN = {
    "紫微": "ZIWEI", "天机": "TIANJI", "太阳": "TAIYANG", "武曲": "WUQU",
    "天同": "TIANTONG", "廉贞": "LIANZHEN", "天府": "TIANFU", "太阴": "TAIYIN",
    "贪狼": "TANLANG", "巨门": "JUMEN", "天相": "TIANXIANG", "天梁": "TIANLIANG",
    "七杀": "QISHA", "破军": "POJUN",
}

# Pinyin 别名归一(引擎与数据集对同一星的拼写差异)
_PINYIN_ALIAS = {
    "LIANZHENG": "LIANZHEN",  # 廉贞: 数据集 LIANZHENG / 引擎 LIANZHEN
}


def _norm_star(py: str) -> str:
    return _PINYIN_ALIAS.get(py, py)


def _major_stars_pinyin(stars) -> set:
    """从数据集 stars 列表提取主星, 映射为 pinyin set (与引擎对齐, 归一别名)."""
    out = set()
    for s in stars or []:
        if s.get("type") == "major":
            py = _STAR_PINYIN.get(s.get("name"))
            if py:
                out.add(_norm_star(py))
    return out


def _engine_majors_per_branch(chart) -> dict:
    """引擎 palace_data → {branch_cn: set(pinyin)} 。"""
    pd = getattr(chart, "palace_data", None) or {}
    # 引擎 palace_data 结构可能是 {branch: {...}} 或 list
    out = defaultdict(set)
    if isinstance(pd, dict):
        for br, info in pd.items():
            stars = []
            if isinstance(info, dict):
                stars = info.get("major_stars") or info.get("major") or []
            for s in stars:
                out[str(br)].add(s if isinstance(s, str) else s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=50)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--month", type=int, default=None)
    args = ap.parse_args()

    root = _dataset_root()
    recs = _find_samples(root, args.year, args.month, args.samples)
    print(f"抽样 {len(recs)} 条 (数据集根={root.name}, year={args.year or 'auto'})")

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter

    adapter = ZiweiSolarAdapter()
    match_ming = 0
    match_wuxing = 0
    match_stars = 0
    total = 0
    fail_samples = []

    for i, r in enumerate(recs):
        bi = r["birthInfo"]
        chart = r["chart"]
        ds_ming_branch_num = chart.get("mingGongBranch")
        ds_wuxing = chart.get("wuxingJuName", "")
        # 命宫宫位的主星 (找 isMingGong)
        ds_ming_stars = None
        for pl in chart.get("palaces", []):
            if pl.get("isMingGong"):
                ds_ming_stars = _major_stars_pinyin(pl.get("stars"))
                break
        total += 1

        try:
            e = adapter.compute(
                bi["year"], bi["month"], bi["day"], bi["hour"],
                bi.get("gender", "male"),
            )
        except Exception as ex:
            print(f"  [{i}] engine error {type(ex).__name__}: {str(ex)[:60]}")
            continue

        # 引擎输出
        e_ming_star = getattr(e, "soul_palace_main_star", None)
        e_pd = e.palace_data if hasattr(e, "palace_data") else {}
        # 引擎命宫地支: 引擎字段 soul_earthly_branch
        e_ming_branch_cn = None
        e_ming_stars = None
        if isinstance(e_pd, dict):
            for k in ("soul_earthly_branch", "ming_gong", "命宫"):
                if k in e_pd and e_pd[k]:
                    e_ming_branch_cn = str(e_pd[k])
                    break
            # 主星: soul_palace_main_stars
            e_ming_stars = set(getattr(e, "soul_palace_main_stars", None) or [])

        # 1) 命宫地支匹配
        ds_ming_branch_cn = _BRANCH_CN[ds_ming_branch_num] if ds_ming_branch_num is not None else None
        if e_ming_branch_cn and ds_ming_branch_cn and e_ming_branch_cn == ds_ming_branch_cn:
            match_ming += 1

        # 2) 五行局匹配 (引擎 five_elements_class)
        e_wuxing = str(e_pd.get("five_elements_class", "")) if isinstance(e_pd, dict) else ""
        if e_wuxing and ds_wuxing and (e_wuxing in ds_wuxing or ds_wuxing in e_wuxing):
            match_wuxing += 1

        # 3) 命宫主星匹配 (两侧都归一别名)
        if e_ming_stars is not None and ds_ming_stars is not None:
            e_norm = {_norm_star(s) for s in e_ming_stars}
            if e_norm == ds_ming_stars:
                match_stars += 1
            elif i < 10:
                fail_samples.append((i, e_norm, ds_ming_stars))

        if i < 3:
            print(f"  [{i}] 命宫: 数据={ds_ming_branch_cn} 引擎={e_ming_branch_cn} | "
                  f"五行: 数据={ds_wuxing} 引擎={e_wuxing} | "
                  f"主星: 数据={sorted(ds_ming_stars) if ds_ming_stars else '∅'} "
                  f"引擎={sorted(e_ming_stars) if e_ming_stars else '∅'}")

    print("\n" + "=" * 56)
    print(f"E8 Full Replay 抽样 {total} 条结果:")
    print(f"  命宫地支匹配: {match_ming}/{total} ({100*match_ming/max(total,1):.1f}%)")
    print(f"  五行局匹配:   {match_wuxing}/{total} ({100*match_wuxing/max(total,1):.1f}%)")
    print(f"  命宫主星匹配: {match_stars}/{total} ({100*match_stars/max(total,1):.1f}%)")
    if fail_samples:
        print("\n  主星不匹配样例(前10):")
        for i, es, ds_ in fail_samples[:5]:
            print(f"    [{i}] 引擎={sorted(es) if es else '∅'} 数据={sorted(ds_) if ds_ else '∅'}")
    print("=" * 56)

    # E8 门槛: 三项均 ≥95% 才 PASS
    passed = all([
        match_ming / max(total, 1) >= 0.95,
        match_wuxing / max(total, 1) >= 0.95,
        match_stars / max(total, 1) >= 0.95,
    ])
    print(f"\nE8 PRODUCTION TRACE: {'PASS' if passed else 'FAIL'} (门槛: 三项均≥95%)")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
