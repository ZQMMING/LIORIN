# -*- coding: utf-8 -*-
"""河洛终态案例打印器。

用法：
    PYTHONPATH=src python tools/heluo/case_demo.py

打印：四柱 / 天数地数 / 先天后天卦 / 元堂 / 大运分段 / 流年流月 / 解卦 evidence，
并在纯卦盘上对照「改造前（8 锚点+线性兜底）」与「改造后（重数全表）」的大运先天段。
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import sxtwl  # noqa: E402

from tongshu.engines.heluo.canonical import HeluoCanonical  # noqa: E402
from tongshu.engines.heluo.guajie import build_guajie_from_result  # noqa: E402
from tongshu.engines.heluo.yuan_tang import HOUR_NAMES  # noqa: E402

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 改造前：8 锚点 + 旧线性兜底
OLD_ANCHOR = {
    "男乾": {0: 0, 3: 0, 6: 2, 9: 2},
    "女乾": {0: 5, 3: 5, 6: 2, 9: 2},
    "女坤": {0: 0, 3: 0, 6: 3, 9: 3},
    "男坤": {0: 5, 3: 5, 6: 2, 9: 2},
}
NEW_UP = (0, 1, 2, 0, 1, 2, 3, 4, 5, 3, 4, 5)
NEW_DOWN = (5, 4, 3, 5, 4, 3, 2, 1, 0, 2, 1, 0)


def old_index(cfg, hi):
    up = cfg in ("男乾", "女坤")
    return OLD_ANCHOR[cfg].get(hi, hi % 6 if up else (5 - hi) % 6)


def new_index(cfg, hi):
    return NEW_UP[hi] if cfg in ("男乾", "女坤") else NEW_DOWN[hi]


def cfg_of(gua, gender):
    if gua == "乾":
        return "男乾" if gender == "male" else "女乾"
    return "女坤" if gender == "female" else "男坤"


def pillars(y, m, d, h):
    day = sxtwl.fromSolar(y, m, d)
    return [(GAN[g.tg], ZHI[g.dz]) for g in
            (day.getYearGZ(), day.getMonthGZ(), day.getDayGZ(), day.getHourGZ(h))]


def dump(bz, gender, birth_hour, birth_date, target, label=""):
    hi = HOUR_NAMES.index(birth_hour)
    r = HeluoCanonical().calculate(
        bazi=bz, gender=gender, birth_hour=birth_hour, era="zhong",
        birth_year=int(birth_date[:4]), birth_date=birth_date,
    )
    pre, post = r.prenatal, r.postnatal
    n = r.numbers
    print("=" * 74)
    print(f"案例 {label}  {birth_date} {birth_hour}时 "
          f"{'男' if gender == 'male' else '女'}")
    print("=" * 74)
    print(f"  四柱       : " + " ".join(f"{g}{z}" for g, z in bz))
    print(f"  天数/地数  : {n.tian_reduced} / {n.di_reduced}"
          f"   (天 {n.tian_shu} 地 {n.di_shu})")
    print(f"  先天卦     : {pre.hexagram_name}  (上{pre.upper_gua} 下{pre.lower_gua})")
    print(f"  后天卦     : {post.hexagram_name}  (上{post.upper_gua} 下{post.lower_gua})")

    pure = pre.upper_gua == pre.lower_gua and pre.upper_gua in ("乾", "坤")
    old_yt = None
    print(f"  元堂(先天) : {r.yuantang.yuantang}  index={r.yuantang.yuantang_index}"
          f"  {r.yuantang.yao_nature}爻")
    if pure:
        cfg = cfg_of(pre.upper_gua, gender)
        o, nw = old_index(cfg, hi), new_index(cfg, hi)
        old_yt = o
        tag = "← 已变" if o != nw else "（未变）"
        print(f"     配置 {cfg}｜{birth_hour}时  改造前 index={o} → "
              f"改造后 index={nw}  {tag}")

    dy = r.timeline.qi_phase["dayun"]
    age = target - int(birth_date[:4]) + 1        # 虚岁
    print(f"  大运段数   : {len(dy)}  覆盖 {dy[0]['age_start']}-"
          f"{dy[-1]['age_end']} 虚岁")
    for e in dy:
        mark = " ★" if e["age_start"] <= age <= e["age_end"] else ""
        span = e["age_end"] - e["age_start"] + 1
        print(f"    {e['age_start']:>3}-{e['age_end']:<3} {e['hexagram']}"
              f" {e['line_nature']}爻 idx={e['line_index']} {e['phase']}"
              f" {span}年{mark}")

    for y2 in r.timeline.yearly_hexagrams:
        if y2.get("year") == target:
            print(f"  {target} 流年 (虚岁{age}) : {y2['hexagram']} 元堂 idx="
                  f"{y2['yuantang_index']} ({y2['yuantang_nature']}爻)")
            for m in y2.get("months", [])[:3]:
                up, lo = m.get("upper"), m.get("lower")
                print(f"      流月 {m.get('month')}月: {up}{lo} 上{up} 下{lo}")
            break

    if old_yt is not None and old_yt != r.yuantang.yuantang_index:
        print(f"  ── 大运先天段对照（元堂 {old_yt} vs "
              f"{r.yuantang.yuantang_index}，自下而上各走六爻）──")
        new_order = [k for e in dy if e["phase"] == "先天" for k in [e["line_index"]]]
        old_order = [(old_yt + k) % 6 for k in range(6)]
        print(f"     改造前爻位序列: {old_order}")
        print(f"     改造后爻位序列: {new_order}")
        if new_order == old_order:
            print("     → 序列相同，仅段起止年龄平移")
        else:
            print(f"     → 整段前移/后移，段界年龄全部改变")
    g = build_guajie_from_result(r, bazi=bz, target_year=target,
                                 target_month=7, target_day=5)
    ev = g.get("evidence", [])
    print(f"  解卦 evidence 条数: {len(ev)}")
    for e in ev[:6]:
        print(f"    · {e}")
    if len(ev) > 6:
        print(f"    …（其余 {len(ev) - 6} 条）")
    return r


def main():
    # 案例 A：上轮基线案例，非纯卦，应完全无变化
    dump(pillars(1983, 11, 3, 12), "male", "午", "1983-11-03", 2026, "A 回归确认")
    print()
    # 案例 B：纯卦，男乾，辰时 —— 改造后元堂 4 -> 1
    dump(pillars(1980, 3, 16, 8), "male", "辰", "1980-03-16", 2026, "B 纯卦男乾")
    print()
    # 案例 C：纯卦，女坤，申时 —— 改造后元堂 2 -> 5
    dump(pillars(1980, 5, 2, 16), "female", "申", "1980-05-02", 2026, "C 纯卦女坤")


if __name__ == "__main__":
    main()
