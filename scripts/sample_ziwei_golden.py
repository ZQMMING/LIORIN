#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
紫微 Golden Set 抽样器

来源: D:/顺天系统资料/ziwei-doushu-dataset（倪海厦《天纪》紫微斗数 518,400条）
用途: 抽取代表性样本 → 转为 Golden Case JSON
      覆盖: 60年干支循环 + 12时辰 + 2性别 + 边界（子时/闰月/节气边界）

输出: cases/golden/ziwei_golden_set.json
格式: EngineGoldenCase (V2 规范: input/canonical_state/expected_calculation/...)

用法:
  python scripts/sample_ziwei_golden.py --count 150 [--seed 42]

原则（V2）:
- 只读数据，不修改引擎
- 倪海厦体系约束：与 iztro 同做交叉验证源，不污染引擎
- Resource ID ≠ File Path（路径独立）
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import os

REPO_ROOT = Path(__file__).resolve().parents[1]
# 数据集路径必须通过环境变量 ZIWEI_DATASET_ROOT 注入（P0路径独立红线）
_env = os.environ.get("ZIWEI_DATASET_ROOT")
if not _env:
    raise SystemExit("P0路径红线: 请设置环境变量 ZIWEI_DATASET_ROOT 指向 ziwei-doushu-dataset/ziwei-samples-toolkit")
DATASET_ROOT = Path(_env)
OUT_PATH = REPO_ROOT / "cases" / "golden" / "ziwei_golden_set.json"

# 12地支数字 → 中文（数据集用 0=子 1=丑 ... 11=亥）
BRANCH_NUM_TO_CN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 主星拼音（数据集用中文名，无需转换）


def list_samples() -> list[dict]:
    """列出数据集全部可用样本（优先 sample-preview，其次 samples-out 随机采样）。"""
    samples = []
    # 1. sample-preview（20个，确定存在）
    preview_dir = DATASET_ROOT / "sample-preview"
    if preview_dir.is_dir():
        for p in sorted(preview_dir.rglob("*.json")):
            try:
                samples.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                pass

    # 2. samples-out（60年×12月 gz，随机抽到目标数）
    samples_out = DATASET_ROOT / "samples-out"
    if samples_out.is_dir():
        year_dirs = sorted(d for d in samples_out.iterdir() if d.is_dir())
        for yd in year_dirs:
            gz_files = sorted(yd.glob("*.jsonl.gz"))
            if not gz_files:
                continue
            # 每年份抽1个月文件
            pick = gz_files[random.randrange(len(gz_files))]
            try:
                with gzip.open(pick, "rt", encoding="utf-8") as f:
                    lines = f.readlines()
                if lines:
                    samples.append(json.loads(random.choice(lines)))
            except Exception:
                pass
    return samples


def to_golden_case(sample: dict) -> dict:
    """将数据集样本转为 V2 Golden Case。"""
    chart = sample["chart"]
    birth = sample["birthInfo"]
    return {
        "case_id": f"ZIWEI-GOLDEN-{birth['year']}-{birth['month']:02d}-{birth['day']:02d}-h{birth['hour']:02d}-{birth['gender']}",
        "engine": "ziwei",
        "engine_version": "1.0.0",
        "input": {
            "birth_year": birth["year"],
            "birth_month": birth["month"],
            "birth_day": birth["day"],
            "birth_hour": birth["hour"],
            "gender": birth["gender"],
            "longitude": birth.get("longitude", 120),
        },
        "canonical_state": {
            "lunar_year": chart["lunarInfo"]["lunarYear"],
            "lunar_month": chart["lunarInfo"]["lunarMonth"],
            "lunar_day": chart["lunarInfo"]["lunarDay"],
            "year_stem": chart["lunarInfo"]["yearStem"],
            "year_branch": chart["lunarInfo"]["yearBranch"],
            "is_leap_month": chart["lunarInfo"]["isLeapMonth"],
        },
        "expected_calculation": {
            "ming_gong_branch": BRANCH_NUM_TO_CN[chart["mingGongBranch"]],
            "shen_gong_branch": BRANCH_NUM_TO_CN[chart["shenGongBranch"]],
            "wuxing_ju": chart["wuxingJuName"],
            "ziwei_star_branch": BRANCH_NUM_TO_CN[chart["ziweiPos"]],
            "palaces": [
                {
                    "name": p["name"],
                    "branch": BRANCH_NUM_TO_CN[p["branch"]],
                    "major_stars": [s["name"] for s in p.get("stars", []) if s.get("type") == "major"],
                }
                for p in chart["palaces"]
            ],
        },
        "expected_evidence": [],
        "expected_signal": [],
        "expected_judgment": [],
        "human_verified_result": None,
        "source": {
            "dataset": "ziwei-doushu-dataset",
            "system": sample.get("system", ""),
            "schema_version": "v3-samples",
        },
        "provenance": {
            "source_id": "renhuai123/ziwei-doushu",
            "source_version": "v3.0-samples",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=150)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    if not DATASET_ROOT.is_dir():
        print(f"❌ 数据集目录不存在: {DATASET_ROOT}")
        print("   请确认 D:/顺天系统资料/ziwei-doushu-dataset 已复制")
        return 1

    samples = list_samples()
    print(f"收集样本: {len(samples)} 条")
    if not samples:
        print("❌ 无可用样本")
        return 1

    # 去重 + 抽样到目标数
    seen = set()
    unique = []
    for s in samples:
        key = (s["birthInfo"]["year"], s["birthInfo"]["month"], s["birthInfo"]["day"],
               s["birthInfo"]["hour"], s["birthInfo"]["gender"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    if len(unique) > args.count:
        unique = random.sample(unique, args.count)

    golden = [to_golden_case(s) for s in unique]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(golden, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ 写入 {len(golden)} 个 Golden Case → {OUT_PATH}")
    # 覆盖统计
    years = {c["input"]["birth_year"] for c in golden}
    genders = {c["input"]["gender"] for c in golden}
    hours = {c["input"]["birth_hour"] for c in golden}
    print(f"   年份覆盖: {min(years)}-{max(years)} ({len(years)}年)")
    print(f"   性别覆盖: {sorted(genders)}")
    print(f"   时辰覆盖: {len(hours)}个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
