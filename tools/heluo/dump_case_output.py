# -*- coding: utf-8 -*-
"""跑一个真实案例，**完整**展开引擎输出（递归，不省略任何字段）。

用于人工核对引擎全链路：
四柱 → 天数地数 → 先天卦 → 元堂 → 后天卦 → 时间轴（大运/流年/流月/流日）
→ 互错综 → 化工 → 元气 → 节候 → 判词 → 平台信号。

**用法**
```
python tools/heluo/dump_case_output.py                 # 默认样本（目标年在时间轴内）
python tools/heluo/dump_case_output.py --index 3       # 换一条样本
python tools/heluo/dump_case_output.py --out out.txt   # 落盘
python tools/heluo/dump_case_output.py --target-date 2026-10-23
```

⚠ 样本来自 `src/heluo_engine/data/案例回归样本.json`（真实命例，随包），
**不依赖包外数据**。
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime
import io
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from heluo_engine.adapter import HeluoAdapter
from heluo_engine.engines.bazi_engine import BaziEngine
from heluo_engine.engines.heluo.canonical_signals import build_platform_signals

SAMPLE = REPO / "src" / "heluo_engine" / "data" / "案例回归样本.json"


def dump(o, out, indent=0):
    pad = "  " * indent
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        out.write(f"{pad}{type(o).__name__}:\n")
        for f in dataclasses.fields(o):
            dump(getattr(o, f.name), out, indent + 1)
        return
    if isinstance(o, dict):
        out.write(f"{pad}dict({len(o)}):\n")
        for k, v in o.items():
            out.write(f"{pad}  [{k}]:\n")
            dump(v, out, indent + 2)
        return
    if isinstance(o, (list, tuple)):
        out.write(f"{pad}{type(o).__name__}(len={len(o)}):\n")
        for i, v in enumerate(o):
            out.write(f"{pad}  #{i}:\n")
            dump(v, out, indent + 2)
        return
    if isinstance(o, datetime.datetime):
        out.write(f"{pad}{o.isoformat()}\n")
        return
    if isinstance(o, str) and len(o) > 300:
        out.write(f"{pad}{o[:300]}\n")
        out.write(f"{pad}…（共 {len(o)} 字）\n")
        return
    out.write(f"{pad}{o!r}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=-1,
                    help="样本序号；-1 = 自动挑一条目标年在时间轴覆盖内的")
    ap.add_argument("--out", default="", help="输出文件（缺省打印到 stdout）")
    ap.add_argument("--target-date", default="2026-10-23")
    args = ap.parse_args()

    doc = json.loads(SAMPLE.read_text(encoding="utf-8"))
    if args.index >= 0:
        pick = doc["samples"][args.index]
    else:
        pick = next((c for c in doc["samples"]
                     if 2026 - c["date"][0] <= 70 and c["date"][0] <= 2005),
                    doc["samples"][0])
    y, m, d = pick["date"]
    h = pick["hour"]
    gender = pick["gender"]

    buf = io.StringIO()
    buf.write("【案例】" + json.dumps(pick, ensure_ascii=False) + "\n")
    chart = BaziEngine().compute((y, m, d, h), gender=gender)
    buf.write(f"\n【引擎算出的四柱】{chart.get_pillars_chinese()}"
              f"（期望 {pick['bazi']}）\n")

    res = HeluoAdapter().compute((y, m, d, h), gender=gender,
                                 target_date=args.target_date)
    sigs = build_platform_signals(res)

    buf.write("\n" + "=" * 78 + "\nHeluoResult 完整输出\n" + "=" * 78 + "\n")
    dump(res, buf)
    buf.write("\n" + "=" * 78 + "\n平台信号 build_platform_signals(result)\n"
              + "=" * 78 + "\n")
    dump(sigs, buf)

    text = buf.getvalue()
    if args.out:
        p = pathlib.Path(args.out)
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"已写入 {p}（{len(text.splitlines())} 行）")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
