# -*- coding: utf-8 -*-
"""核实：bazi 月柱粒度 / 我这份 solar_jq_index 是否第二份实现 / 与 jiehhou 有无漂移"""
import io
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, "src")
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from heluo_engine.engines.heluo.hua_gong import (HUAGONG_JIEQI_WINDOWS, huagong_by_birth_date,
                                            huagong_by_jieqi)
from heluo_engine.engines.heluo.jiehhou import get_current_jieqi_info
from heluo_engine.engines.heluo.yue_ling_shu_ge import solar_jq_index

out = []

# ══ 1. 八字引擎月柱 vs 节气窗口 ══
out.append("== 1. bazi 月支能否单独定出窗口？ ==")
out.append("   月支月跨两个节气（如卯月=惊蛰→清明），而窗口按节气切，")
out.append("   故月支**粒度不够**，必须落到日。这是原典窗口的固有粒度，不是实现取巧。")
out.append("")
out.append("   月支   节气区间(jq)              窗口归属")
# 节起月支：子←冬至 丑←大寒 寅←立春 卯←惊蛰 辰←清明 巳←立夏
#           午←芒种 未←小暑 申←立秋 酉←白露 戌←寒露 亥←立冬
START = {0: "子", 2: "丑", 3: "寅", 5: "卯", 7: "辰", 9: "巳",
         11: "午", 13: "未", 15: "申", 17: "酉", 19: "戌", 21: "亥"}
pts = []
cur = date(2025, 11, 1)
while cur <= date(2027, 4, 30):
    import sxtwl
    jq = sxtwl.fromSolar(cur.year, cur.month, cur.day).getJieQi()
    if jq is not None and jq != 255 and 0 <= jq < 24:
        pts.append((cur, jq))
    cur += timedelta(days=1)
pts.sort()


def jq_of(d):
    # 2026 全年：若 pts 只从 2025-11 起，c 必须**重新初始化后逐日推进**，
    # 不能跨 365 天共用一个初值（上一版共用 c=0，导致 1 月初全被判成上一年的 jq）。
    c = None
    for dd, jq in pts:
        if dd <= d:
            c = jq
        else:
            break
    if c is None:
        return None
    return c


def br_of(d):
    b = "子"
    for dd, jq in pts:
        if jq in START and dd <= d:
            b = START[jq]
    return b


for b in "子丑寅卯辰巳午未申酉戌亥":
    seg = {}
    for k in range(365):
        d = date(2026, 1, 1) + timedelta(days=k)
        if br_of(d) != b:
            continue
        g = huagong_by_jieqi(jq_of(d))
        seg[g] = seg.get(g, 0) + 1
    out.append("   %s     %-22s %s" % (b, "/".join(sorted(seg)) or "（全月空档）",
                                   "**跨窗口**" if len(seg) > 1 else "整月单一"))

# ══ 2. 我这份 solar_jq_index 是不是第二份实现 ══
out.append("")
out.append("== 2. solar_jq_index 是否与 jiehhou.get_current_jieqi_info 重复？ ==")
diff = 0
samples = []
d = date(2026, 1, 1)
for k in range(365):
    ds = (d + timedelta(days=k)).isoformat()
    a = solar_jq_index(ds)
    info = get_current_jieqi_info(d.year, d.month, d.day)
    b = info.jq_index if info else None
    if a != b:
        diff += 1
        if len(samples) < 5:
            samples.append((ds, a, b))
out.append("   2026 全年 365 日逐日比对：不一致 %d 处" % diff)
for ds, a, b in samples:
    out.append("      %s  solar_jq_index=%s  jiehhou=%s" % (ds, a, b))
out.append("   → %s" % ("两份实现目前一致，但**是两份**，将来必然漂移"
                     if diff == 0 else "已漂移！"))

# ══ 3. 现有 canonical 是否已经算过 jq ══
out.append("")
out.append("== 3. canonical 是否已经算过 jq（重复劳动？） ==")
out.append("   canonical.calculate() Step 9 _compute_seasonal_hexagram(birth_date)")
out.append("   已经用 get_current_jieqi_info 算出 jq_index 并塞进 HeluoResult。")
out.append("   → 化工若自己再调一次 solar_jq_index，**同一份 sxtwl 结果算两遍**。")

# ══ 4. _compute_huagong 与 _compute_seasonal_hexagram 的先后 ══
out.append("")
out.append("== 4. 两者在 calculate() 中的顺序 ==")
out.append("   Step 8  _compute_huagong(...)            ← 化工")
out.append("   Step 9  _compute_seasonal_hexagram(...)  ← 节候卦（已含 jq_index）")
out.append("   → 化工在 Step 8、jq 在 Step 9 才算出。**顺序上化工拿不到**，")
out.append("     但 jq 只依赖 birth_date，与盘面无关，本可提前算或直接复用。")

io.open("probe_arch.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out))