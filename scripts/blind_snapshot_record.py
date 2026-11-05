# -*- coding: utf-8 -*-
"""盲派「引擎签名快照」录制器。

用途：把 20 个盲派命例的**引擎当前输出签名**冻结为快照，用于检测无意漂移。
它不是真值：真值层在 `cases/truth/blind_truth_cases.json`（只收原著明文断语案例）。

用法:
    python scripts/blind_snapshot_record.py            # 重录并写回
    python scripts/blind_snapshot_record.py --check    # 只比对，不写回（CI 用）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.blind_bazi_engine import compute_blind_bazi  # noqa: E402

SNAPSHOT = ROOT / "cases" / "golden" / "blind_engine_snapshot.json"


def _signature(result) -> dict:
    strengths = [round(float(s.strength), 4) for s in (result.signals or [])]
    return {
        "signal_count": len(result.signals or []),
        "strength_range": [min(strengths) if strengths else None,
                           max(strengths) if strengths else None],
        "has_zuo_gong": bool(result.zuo_gong_type),
        "has_main_branches": bool(result.main_branches),
        "has_guest_branches": bool(result.guest_branches),
        "has_ti_yong": bool(result.ti_branches) and bool(result.yong_branches),
        "zuo_gong_methods_count": len(result.zuo_gong_methods or []),
        "zheng_fan_ju": result.zheng_fan_ju,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    drift = 0
    for case in data["cases"]:
        inp = case["input"]
        result = compute_blind_bazi(
            (inp["birth_year"], inp["birth_month"], inp["birth_day"], inp["birth_hour"]),
            inp["gender"],
        )
        sig = _signature(result)
        if args.check:
            old = case["snapshot"]
            bad = {k: (old.get(k), sig.get(k)) for k in sig if old.get(k) != sig.get(k)}
            if bad:
                drift += 1
                print(f"DRIFT {case['case_id']}: {bad}")
        else:
            case["snapshot"] = sig

    if args.check:
        print(f"快照比对: {len(data['cases']) - drift}/{len(data['cases'])} 一致")
        return 0 if drift == 0 else 1

    data["metadata"]["recorded_at"] = "recorded-by-script"
    SNAPSHOT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已重录 {len(data['cases'])} 案 -> {SNAPSHOT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
