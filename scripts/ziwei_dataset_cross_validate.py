#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ZIWEI E8前置 — 518400数据集抽样交叉验证 (只读)

从数据集 samples-out/ 抽样N个命盘, 用本引擎 ZiweiSolarAdapter 重排,
对比12宫主星(major stars)的一致率。这是 PRODUCTION_VALIDATED 阶段
E8 Full Replay 的前置可行性验证。

数据集为 iztro 体系; 引擎按倪海厦体系安星。若存在流派差异(安星规则差异),
一致率会反映在结果中 — 差异≠错误, 需人工裁决分类(派别隔离, V2同盘异法)。

用法:
    python scripts/ziwei_dataset_cross_validate.py [--n 50] [--seed 42]
"""
import argparse
import gzip
import json
import random
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DATASET_ROOT = Path(os.environ.get("ZIWEI_DATASET_ROOT", "")) / "samples-out" if os.environ.get("ZIWEI_DATASET_ROOT") else None


def load_samples(n: int, seed: int = 42):
    """从各年份数据集中抽样n个样本. 数据集路径必须通过 ZIWEI_DATASET_ROOT 环境变量注入 (P0路径红线)."""
    if DATASET_ROOT is None or not DATASET_ROOT.exists():
        raise SystemExit("P0路径红线: 请设置环境变量 ZIWEI_DATASET_ROOT 指向 ziwei-samples-toolkit 目录")
    rng = random.Random(seed)
    files = sorted(DATASET_ROOT.glob("year-*/[0-9]*-[0-9]*.jsonl.gz"))
    if not files:
        raise SystemExit(f"数据集不存在: {DATASET_ROOT}")
    picked = []
    # 均匀散布抽样: 从随机起点每k个文件取1个, 每文件抽1条
    step = max(1, len(files) // max(1, n))
    for f in files[rng.randrange(step)::step]:
        if len(picked) >= n:
            break
        with gzip.open(f, "rt", encoding="utf-8") as fp:
            lines = fp.readlines()
        if not lines:
            continue
        line = lines[rng.randrange(len(lines))]
        try:
            picked.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return picked


# 数据集宫名→引擎宫名映射(十二宫)
PALACE_MAP_DS2ENG = {
    "命宫": "命宫", "兄弟": "兄弟", "夫妻": "夫妻", "子女": "子女",
    "财帛": "财帛", "疾厄": "疾厄", "迁移": "迁移", "仆役": "仆役",
    "官禄": "官禄", "田宅": "田宅", "福德": "福德", "父母": "父母",
}

# 数据集中文星名→引擎拼音名 (对齐 e8_ziwei_full_replay 的 _STAR_PINYIN)
# 修正: 天同→TIANTONG(原误标TIANXIE), 廉贞两侧归一为LIANZHEN
STAR_MAP = {
    "紫微": "ZIWEI", "天机": "TIANJI", "太阳": "TAIYANG", "武曲": "WUQU",
    "天同": "TIANTONG", "廉贞": "LIANZHEN", "天府": "TIANFU", "太阴": "TAIYIN",
    "贪狼": "TANLANG", "巨门": "JUMEN", "天相": "TIANXIANG", "天梁": "TIANLIANG",
    "七杀": "QISHA", "破军": "POJUN",
}
# 引擎侧廉贞别名归一 (引擎可能输出 LIANZHENG, 统一 LIANZHEN)
_STAR_ALIAS = {"LIANZHENG": "LIANZHEN"}
def _norm_star(py): return _STAR_ALIAS.get(py, py)


def ds_palaces_to_map(chart: dict):
    """数据集palaces[] 转为 {宫名: [星名...]}"""
    out = {}
    for p in chart.get("palaces", []):
        name = p.get("name", "")
        stars = [s.get("name", "") for s in p.get("stars", []) if s.get("type") == "major"]
        out[name] = stars
    return out


def eng_chart_to_map(r) -> dict:
    """引擎ZiweiChart 转为 {宫名: [拼音星名...]} — 宫位数据在 palace_data.palaces (廉贞归一)."""
    d = r.to_dict() if hasattr(r, "to_dict") else r
    palaces = d.get("palace_data", {}).get("palaces", {})
    out = {}
    for palace, pdata in palaces.items():
        if isinstance(pdata, dict) and "major" in pdata:
            out[palace] = [_norm_star(str(x)) for x in pdata["major"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    samples = load_samples(args.n, args.seed)
    print(f"抽样: {len(samples)}盘 (seed={args.seed})")

    from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter
    adapter = ZiweiSolarAdapter()

    total_palace_cmp = match_palace = 0
    total_sample = full_match = 0
    star_only_ds = 0
    mismatches = []
    for i, s in enumerate(samples):
        bi = s["birthInfo"]
        try:
            r = adapter.compute(bi["year"], bi["month"], bi["day"], bi["hour"], bi.get("gender", "male"))
        except Exception as e:
            mismatches.append(f"sample[{i}] 引擎异常: {type(e).__name__}: {str(e)[:60]}")
            continue
        ds_map = ds_palaces_to_map(s["chart"])
        eng_map = eng_chart_to_map(r)
        if not ds_map or not eng_map:
            star_only_ds += 1
            continue
        sample_full = True
        for palace, ds_stars in ds_map.items():
            if palace not in eng_map:
                continue
            eng_stars = set(eng_map[palace])
            ds_translated = {STAR_MAP.get(x, x) for x in ds_stars}
            total_palace_cmp += 1
            if eng_stars == ds_translated:
                match_palace += 1
            else:
                sample_full = False
                if len(mismatches) < 10:
                    mismatches.append(
                        f"sample[{i}] {palace}: ds={sorted(ds_translated)} eng={sorted(eng_stars)}"
                    )
        total_sample += 1
        if sample_full:
            full_match += 1

    print("=" * 62)
    print("ZIWEI 数据集交叉验证 (iztro 518400样本 vs 引擎)")
    print("=" * 62)
    if total_palace_cmp:
        print(f"样本数(可比): {total_sample}, 全宫一致: {full_match}")
        print(f"宫位比较: {match_palace}/{total_palace_cmp} "
              f"({100.0 * match_palace / total_palace_cmp:.1f}%)")
    if star_only_ds:
        print(f"跳过(结构异常): {star_only_ds}")
    print(f"\n差异样例(前10):")
    for m in mismatches:
        print(f"  {m}")
    print("\n注: 数据集为iztro体系; 差异可能是流派安星规则差异(需人工分类), 非必然错误")


if __name__ == "__main__":
    main()
