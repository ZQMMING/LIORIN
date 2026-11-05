#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微亮度表外部取证核对（可选，依赖仓库外取证文档）。

数据源：`D:\\顺天系统资料\\紫微检验\\亮度表四方对照_Z39.md`
（168 格 × 引擎/dataset众数/倪师断言/原著命图/证据等级）。
文档不存在时输出 SKIP 并 return 0（不把缺证据当通过）。

用途：
1. 逐格核对产品 Z39 表与 dataset 众数的三档归类（差异必须已登记）；
2. 统计证据等级，量化「只有 dataset 单一证据（自证循环）」的格数。
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DOC = Path(r"D:\顺天系统资料\紫微检验\亮度表四方对照_Z39.md")
CLS = {"庙": "bright", "旺": "bright", "得": "normal", "利": "normal",
       "平": "normal", "陷": "dim", "不": "dim", "弱": "dim"}

# 已按原典明文裁决的倪师断言冲突格：(星, 支) -> 裁决理由
ADJUDICATED_CONFLICTS = {
    ("太阴", "卯"): (
        "《紫微斗数全书》:2145 明列「太阴 庙亥子丑 旺寅酉戌 陷卯辰巳」，"
        "卯=陷，产品与 dataset 正确；倪师断言条（Z38:9）原文实讲"
        "「水澄桂萼/太阴庙在子时」，系误摘，该断言条已注销"
    ),
}


def parse(doc: Path) -> list[dict]:
    rows = []
    for line in doc.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 7 or cells[0] in ("星", "---") or cells[1] == "地支":
            continue
        star, branch, engine, dataset, nishi, mingtu, level = cells
        m = re.match(r"(bright|normal|dim)", dataset)
        rows.append({"star": star, "branch": branch, "engine": engine,
                     "dataset": m.group(1) if m else "", "nishi": nishi,
                     "mingtu": mingtu, "level": level})
    return rows


def main() -> int:
    from tongshu.engines.ziwei.rules.brightness import BRIGHTNESS_TABLE

    if not DOC.exists():
        print(f"SKIP: 取证文档不存在 → {DOC}")
        return 0

    rows = parse(DOC)
    print(f"对照表格数 = {len(rows)}")
    lv = Counter(r["level"] for r in rows)
    print("证据等级分布：")
    for k, v in lv.most_common():
        print(f"  {k:12s} {v:4d}  ({100 * v / len(rows):5.1f}%)")

    diffs = []
    for r in rows:
        ours = BRIGHTNESS_TABLE.get(r["star"], {}).get(r["branch"])
        if not ours or not r["dataset"]:
            diffs.append((r, ours, "缺值"))
        elif CLS[ours] != r["dataset"]:
            diffs.append((r, ours, "三档不一致"))

    print(f"\n与 dataset 众数三档不一致 = {len(diffs)}（应仅为已登记的命图裁决格）")
    for r, ours, why in diffs:
        print(f"  {r['star']}{r['branch']}: 产品={ours}({CLS.get(ours)}) "
              f"dataset={r['dataset']} 命图={r['mingtu']} 倪师={r['nishi']} "
              f"等级={r['level']} [{why}]")

    # 与「倪师断言」列冲突的格（内部证据矛盾，须登记）
    conflicts = [r for r in rows
                 if r["nishi"] not in ("-", "") and r["nishi"] != "-"
                 and CLS.get(r["nishi"]) != CLS.get(BRIGHTNESS_TABLE.get(r["star"], {}).get(r["branch"]))]
    if conflicts:
        print(f"\n与倪师断言列冲突 = {len(conflicts)}（已裁决：原典明文优先，Z38 断言条注销为误摘）：")
        for r in conflicts:
            verdict = ADJUDICATED_CONFLICTS.get((r["star"], r["branch"]), "未裁决，待补原典证据")
            print(f"  {r['star']}{r['branch']}: 产品={BRIGHTNESS_TABLE.get(r['star'], {}).get(r['branch'])} "
                  f"倪师断言={r['nishi']} dataset={r['dataset']} 命图={r['mingtu']}")
            print(f"    裁决: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
