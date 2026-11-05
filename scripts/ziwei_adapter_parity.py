# -*- coding: utf-8 -*-
"""生产适配器双后端对照：ZiweiSolarAdapter(backend="iztro") vs backend="native"。

同一阳历/时辰/性别，两条后端应给出同一张 ZiweiChart（命宫/身宫/五行局/主星/
辅煞/杂曜/生年四化/亮度/十二神/大限）。
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter  # noqa: E402

CASES = [
    (1983, 11, 3, 11, "male"), (1990, 3, 1, 5, "female"), (1990, 3, 15, 0, "male"),
    (1976, 7, 14, 9, "female"), (1963, 11, 12, 7, "male"), (1955, 1, 29, 3, "female"),
    (1924, 11, 5, 17, "male"), (2000, 1, 1, 0, "male"), (1995, 10, 12, 10, "male"),
    (1984, 12, 10, 0, "male"), (1990, 8, 15, 23, "female"), (1970, 6, 1, 23, "male"),
]


def _norm(ch):
    return {
        "ju": ch.fiveElementsClass,
        "soul": ch.soul_earthly_branch,
        "body": ch.body_earthly_branch,
        "soul_stars": sorted(ch.soul_palace_main_stars),
        "sihua": sorted(ch.soul_palace_sihua),
        "doujun": ch.doujun_palace,
        "palaces": {
            n: {
                "branch": p.get("branch"),
                "stem": p.get("stem"),
                "major": sorted(p.get("major") or []),
                "minor": sorted(p.get("minor") or []),
                "brightness": dict(p.get("brightness") or {}),
                "changsheng12": p.get("changsheng12"),
                "boshi12": p.get("boshi12"),
                "jiangqian12": p.get("jiangqian12"),
                "suiqian12": p.get("suiqian12"),
                "decadalRange": list(p.get("decadal_range") or []),
            }
            for n, p in ch.palaces.items()
        },
    }


def main() -> int:
    a_eng = ZiweiSolarAdapter(backend="iztro")
    b_eng = ZiweiSolarAdapter(backend="native")
    miss = Counter()
    for y, m, d, h, g in CASES:
        try:
            a = _norm(a_eng.compute(y, m, d, h, g))
            b = _norm(b_eng.compute(y, m, d, h, g))
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {y}-{m}-{d} {h}h {g}: {type(exc).__name__}: {exc}")
            miss["异常"] += 1
            continue
        for k in ("ju", "soul", "body", "soul_stars", "sihua", "doujun"):
            if a[k] != b[k]:
                miss[k] += 1
                print(f"[{k}] {y}-{m}-{d} {h}h {g}: iztro={a[k]} native={b[k]}")
        for name, pa in a["palaces"].items():
            pb = b["palaces"].get(name) or {}
            for key in ("branch", "stem", "major", "minor", "brightness",
                        "changsheng12", "boshi12", "jiangqian12", "suiqian12", "decadalRange"):
                if pa.get(key) != pb.get(key):
                    miss[f"宫:{key}"] += 1
                    if miss[f"宫:{key}"] <= 2:
                        print(f"[{key}] {y}-{m}-{d} {name}: {pa.get(key)} vs {pb.get(key)}")
    print(f"\n案例数={len(CASES)}  不一致：{dict(miss) if miss else '全部一致'}")
    return 0 if not miss else 1


if __name__ == "__main__":
    raise SystemExit(main())
