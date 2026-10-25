# -*- coding: utf-8 -*-
"""Behaviour snapshot for the heluo engine — used to tell EQUIVALENT mutants
from REAL blind spots.

A mutation that survives the test suite is NOT automatically a blind spot:
defensive code (e.g. ``return ("", "")`` guarded by a caller's ``or ""``)
often has an equivalent mutant — the observable behaviour is unchanged.

So we compare a **behaviour snapshot** (deterministic JSON of the engine's
observable output on several fixed cases) between the baseline and the mutant:

  * output identical  ⇒ EQUIVALENT mutant (no blind spot; not a defect)
  * output differs    ⇒ REAL blind spot: behaviour changed, nobody noticed
"""
from __future__ import annotations

import json
import sys

#: 固定的若干盘（覆盖不同路径：男/女、纯卦/杂卦、不同流月流日）
CASES = [
    ((1980, 6, 22, 10), "male", "2026-10-23"),
    ((1975, 11, 22, 1), "male", "2026-09-15"),
    ((1983, 11, 3, 12), "female", "2027-05-10"),
    ((1990, 3, 15, 14), "male", "2026-10-23"),
    ((1965, 8, 8, 8), "female", "2026-01-20"),
]


def _round(obj, n=6):
    """Round floats so the snapshot is stable across runs."""
    if isinstance(obj, float):
        return round(obj, n)
    if isinstance(obj, dict):
        return {str(k): _round(v, n) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple)):
        return [_round(v, n) for v in obj]
    return obj


def snapshot() -> dict:
    """Deterministic snapshot of the engine's observable behaviour."""
    from heluo_engine.adapter import HeluoAdapter
    from heluo_engine.engines.heluo.time_layer_judgment import (
        collect_dayun_judgment, collect_time_layer_judgments,
    )

    ad = HeluoAdapter()
    out = []
    for solar, gender, target in CASES:
        rec = {"case": "%s|%s|%s" % (solar, gender, target)}
        try:
            res = ad.compute(solar, gender=gender, target_date=target)
            rec["prenatal"] = res.prenatal.hexagram_name
            rec["postnatal"] = res.postnatal.hexagram_name
            rec["yuantang"] = res.yuantang.yuantang
            rec["target_date"] = res.target_date
            rec["hua_gong"] = (res.hua_gong.state.value if res.hua_gong else None)
            tj = [_j.to_dict() for _j in
                  collect_time_layer_judgments(res) + [collect_dayun_judgment(res)]]
            rec["time_layers"] = tj
        except Exception as exc:
            rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        out.append(rec)
    return _round(out)


def main() -> int:
    data = snapshot()
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    if out_path:
        # 显式 UTF-8 写文件（避免 shell 重定向的编码问题）
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
