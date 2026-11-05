# -*- coding: utf-8 -*-
"""后端一致性：ZiweiEngine(backend="native") vs 默认 iztro 后端，逐字段对照。

这是"原生引擎可替代 iztro"的验收依据：同一农历日期/时辰/性别，
两条后端必须给出同一张盘（命宫/身宫/五行局/十四主星/辅煞/四组十二神/
宫干/大限区间/生年四化/命宫主星）。
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402

CASES = [
    ((1983, 9, 29), 11, "male"), ((1990, 2, 5), 5, "male"), ((1990, 2, 19), 0, "female"),
    ((1976, 6, 16), 10, "female"), ((1963, 9, 27), 7, "male"), ((1955, 1, 6), 2, "male"),
    ((1924, 10, 9), 17, "male"), ((2000, 11, 25), 0, "male"),
    ((1995, -8, 10), 10, "male"), ((1995, -8, 18), 10, "male"),   # 闰月前半月 / 后半月
    ((1990, 7, 15), 23, "female"),                                # 晚子时
]

FIELDS = ["五行局", "命宫支", "身宫支", "命宫主星", "生年四化", "宫干",
          "十四主星", "辅煞", "杂曜", "十二神", "大限"]


def _comparable(ch):
    palaces = {}
    for name, p in ch.palaces.items():
        palaces[name] = {
            "branch": p.get("branch"),
            "stem": p.get("stem"),
            "major": sorted(p.get("major") or []),
            "minor": sorted(p.get("minor") or []),
            "adjective": sorted(p.get("adjective") or []),
            "decadalRange": list(p.get("decadalRange") or []),
            "changsheng12": p.get("changsheng12"),
            "boshi12": p.get("boshi12"),
            "jiangqian12": p.get("jiangqian12"),
            "suiqian12": p.get("suiqian12"),
        }
    return {
        "ju": ch.fiveElementsClass,
        "soul": ch.soul_earthly_branch,
        "body": ch.body_earthly_branch,
        "soul_stars": sorted(ch.soul_palace_main_stars),
        "soul_sihua": sorted(ch.soul_palace_sihua),
        "palaces": palaces,
    }


def main() -> int:
    iztro_engine = ZiweiEngine()
    native_engine = ZiweiEngine(backend="native")
    if not iztro_engine._iztro_available:
        raise SystemExit("iztro 不可用，无法做后端对照（先 npm install）")

    miss = Counter()
    for lunar_date, hour, gender in CASES:
        try:
            a = _comparable(iztro_engine.full_chart(lunar_date, hour, gender))
            b = _comparable(native_engine.full_chart(lunar_date, hour, gender))
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {lunar_date} {hour}h {gender}: {type(exc).__name__}: {exc}")
            miss["异常"] += 1
            continue
        if a["ju"] != b["ju"]:
            miss["五行局"] += 1
        if a["soul"] != b["soul"]:
            miss["命宫支"] += 1
        if a["body"] != b["body"]:
            miss["身宫支"] += 1
        if a["soul_stars"] != b["soul_stars"]:
            miss["命宫主星"] += 1
            print(f"[命宫主星] {lunar_date}: iztro={a['soul_stars']} native={b['soul_stars']}")
        if a["soul_sihua"] != b["soul_sihua"]:
            miss["生年四化"] += 1
            print(f"[生年四化] {lunar_date}: iztro={a['soul_sihua']} native={b['soul_sihua']}")
        for name, pa in a["palaces"].items():
            pb = b["palaces"].get(name)
            if not pb:
                miss["宫位缺失"] += 1
                continue
            if pa["stem"] != pb["stem"] or pa["branch"] != pb["branch"]:
                miss["宫干"] += 1
                print(f"[宫干] {lunar_date} {name}: {pa['stem']}{pa['branch']} vs {pb['stem']}{pb['branch']}")
            if pa["major"] != pb["major"]:
                miss["十四主星"] += 1
                print(f"[主星] {lunar_date} {name}: {pa['major']} vs {pb['major']}")
            if pa["minor"] != pb["minor"]:
                miss["辅煞"] += 1
                print(f"[辅煞] {lunar_date} {name}: {pa['minor']} vs {pb['minor']}")
            if pa["adjective"] != pb["adjective"]:
                miss["杂曜"] += 1
                print(f"[杂曜] {lunar_date} {name}: {pa['adjective']} vs {pb['adjective']}")
            for key in ("changsheng12", "boshi12", "jiangqian12", "suiqian12"):
                if pa[key] != pb[key]:
                    miss["十二神"] += 1
                    print(f"[{key}] {lunar_date} {name}: {pa[key]} vs {pb[key]}")
            if pa["decadalRange"] != pb["decadalRange"]:
                miss["大限"] += 1
                print(f"[大限] {lunar_date} {name}: {pa['decadalRange']} vs {pb['decadalRange']}")

    print(f"\n案例数={len(CASES)}  字段不一致：{dict(miss) if miss else '全部一致'}")
    return 0 if not miss else 1


if __name__ == "__main__":
    raise SystemExit(main())
