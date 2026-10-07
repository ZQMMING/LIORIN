# -*- coding: utf-8 -*-
"""纯卦元堂「重数」改造的影响面统计（真实四柱，全链）。

用法：
    PYTHONPATH=src python tools/heluo/impact_pure_gua_chongshu.py

两步法：
  1. 只算天数地数 + 先天卦，统计「先天卦为乾/坤纯卦」在总体中的占比（快）
  2. 只对纯卦盘跑 HeluoCanonical 全链，比对先天/后天两层元堂爻位的新旧差异（准）
"""
import io
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import sxtwl  # noqa: E402

from tongshu.engines.heluo.canonical import HeluoCanonical  # noqa: E402
from tongshu.engines.heluo.numbers import compute_tian_di_shu  # noqa: E402
from tongshu.engines.heluo.prenatal import determine_prenatal_hexagram  # noqa: E402
from tongshu.engines.heluo.yuan_tang import HOUR_NAMES  # noqa: E402

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
YEAR_YANG = "甲丙戊庚壬"

# 改造前：8 处锚点 + 旧线性兜底
OLD_ANCHOR = {
    "男乾": {0: 0, 3: 0, 6: 2, 9: 2},
    "女乾": {0: 5, 3: 5, 6: 2, 9: 2},
    "女坤": {0: 0, 3: 0, 6: 3, 9: 3},
    "男坤": {0: 5, 3: 5, 6: 2, 9: 2},
}
# 改造后：重数全表
NEW_UP = (0, 1, 2, 0, 1, 2, 3, 4, 5, 3, 4, 5)
NEW_DOWN = (5, 4, 3, 5, 4, 3, 2, 1, 0, 2, 1, 0)


def old_index(cfg: str, hi: int) -> int:
    up = cfg in ("男乾", "女坤")
    return OLD_ANCHOR[cfg].get(hi, hi % 6 if up else (5 - hi) % 6)


def new_index(cfg: str, hi: int) -> int:
    return NEW_UP[hi] if cfg in ("男乾", "女坤") else NEW_DOWN[hi]


def cfg_of(gua: str, gender: str) -> str:
    if gua == "乾":
        return "男乾" if gender == "male" else "女乾"
    return "女坤" if gender == "female" else "男坤"


def pillars(y: int, m: int, d: int, h: int) -> list[tuple[str, str]]:
    day = sxtwl.fromSolar(y, m, d)
    return [(GAN[g.tg], ZHI[g.dz]) for g in
            (day.getYearGZ(), day.getMonthGZ(), day.getDayGZ(), day.getHourGZ(h))]


def is_pure_gua(obj) -> bool:
    return obj.upper_gua == obj.lower_gua and obj.upper_gua in ("乾", "坤")


def main() -> None:
    canonical = HeluoCanonical()
    total = pure = 0
    cfg_counter: Counter = Counter()
    pure_charts: list = []

    day = date(1980, 1, 1)
    end = date(1989, 12, 31)
    while day <= end:
        if day.day in (2, 9, 16, 23):
            for h24 in range(0, 24, 2):
                hi = h24 // 2
                for gender in ("male", "female"):
                    total += 1
                    bz = pillars(day.year, day.month, day.day, h24)
                    nums = compute_tian_di_shu(bz, gender)
                    pre = determine_prenatal_hexagram(
                        nums.tian_reduced, nums.di_reduced, gender,
                        bz[0][0] in YEAR_YANG, "zhong",
                    )
                    if is_pure_gua(pre):
                        pure += 1
                        cfg_counter[cfg_of(pre.upper_gua, gender)] += 1
                        pure_charts.append((day, hi, gender, bz))
        day += timedelta(days=1)

    print("=" * 72)
    print("第一步：先天卦为纯卦（乾/坤）的比例")
    print("=" * 72)
    print(f"  抽样盘数（1980-1989，每季 4 日 × 12 时 × 2 性别）: {total}")
    print(f"  先天纯卦盘数                                         : {pure}"
          f"  ({pure / total:.2%})")
    print(f"  配置分布: {dict(cfg_counter)}")

    changed = 0
    layer_changed: Counter = Counter()
    hour_counter: Counter = Counter()
    per_cfg_changed: Counter = Counter()
    per_cfg_total: Counter = Counter()
    samples: list[str] = []

    for (d, hi, gender, bz) in pure_charts:
        try:
            r = canonical.calculate(
                bazi=bz, gender=gender, birth_hour=HOUR_NAMES[hi],
                era="zhong", birth_year=d.year, birth_date=d.isoformat(),
            )
        except Exception:
            continue
        layers = []
        if is_pure_gua(r.prenatal):
            layers.append(("先天", cfg_of(r.prenatal.upper_gua, gender)))
        if is_pure_gua(r.postnatal):
            layers.append(("后天", cfg_of(r.postnatal.upper_gua, gender)))
        if not layers:
            continue
        diffs = []
        for lay, cfg in layers:
            per_cfg_total[cfg] += 1
            o, n = old_index(cfg, hi), new_index(cfg, hi)
            if o != n:
                layer_changed[lay] += 1
                per_cfg_changed[cfg] += 1
                hour_counter[HOUR_NAMES[hi]] += 1
                diffs.append(f"{lay}{cfg} {HOUR_NAMES[hi]}时 {o}->{n}")
        if diffs:
            changed += 1
            if len(samples) < 6:
                samples.append(f"{d} {HOUR_NAMES[hi]}时 {gender} | " + " ; ".join(diffs))

    n_pure = sum(per_cfg_total.values())
    print()
    print("=" * 72)
    print("第二步：纯卦盘全链比对（先天层 + 后天层）")
    print("=" * 72)
    print(f"  纯卦盘（先天层）总数 : {n_pure}")
    print(f"  任一层元堂爻位改变   : {changed}  ({changed / n_pure:.1%} of 纯卦盘)")
    print(f"  折算到全部抽样盘     : {changed / total:.2%}")
    print(f"  按层：先天 {layer_changed['先天']} / 后天 {layer_changed['后天']}")
    print()
    print("  按配置（改变数 / 出现数）:")
    for cfg in ("男乾", "女乾", "女坤", "男坤"):
        t = per_cfg_total[cfg]
        if t:
            print(f"    {cfg}: {per_cfg_changed[cfg]:>4} / {t:<4}"
                  f" ({per_cfg_changed[cfg] / t:.1%})")
    print()
    print("  改动的时辰分布：")
    for h in HOUR_NAMES:
        if hour_counter[h]:
            print(f"    {h}时: {hour_counter[h]}")
    print(f"    不变: {' '.join(h for h in HOUR_NAMES if not hour_counter[h])}")
    print()
    print("  样例：")
    for s in samples:
        print(f"    {s}")


if __name__ == "__main__":
    main()
