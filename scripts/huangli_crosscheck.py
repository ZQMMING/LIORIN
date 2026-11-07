# -*- coding: utf-8 -*-
"""黄历·双库一致性核对（lunar_python vs sxtwl）。

用途：黄历的农历（含闰月）/节气名称/日柱干支，仓内没有外部历书逐日样本，
先用两个**独立实现**的历算库交叉核对（等价于「双后端 parity」），
发现不一致即打印（供人工按历书裁决），而不是静默取其一。

注意：两库同源思路（寿星天文历），一致性是必要不充分证据，不能替代原典/历书对照。

用法：
    python scripts/huangli_crosscheck.py 1900 2100 1      # 逐年逐日（慢）
    python scripts/huangli_crosscheck.py 1900 2100 7      # 每 7 天抽一天
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

import sxtwl
from lunar_python import Solar

# 节气名：sxtwl jqIndex 0-23 对应 小寒…冬至（以 15 度划分，索引顺序与常见表不同）
JIEQI = [
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
]


def check(start_year: int, end_year: int, step_days: int = 1) -> int:
    bad = 0
    cur = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    total = 0
    while cur <= end:
        total += 1
        solar = Solar.fromYmd(cur.year, cur.month, cur.day)
        lunar = solar.getLunar()

        sd = sxtwl.fromSolar(cur.year, cur.month, cur.day)
        lp = (lunar.getYear(), lunar.getMonth(), lunar.getDay())
        sx = (sd.getLunarYear(), sd.getLunarMonth(), sd.getLunarDay(), bool(sd.isLunarLeap()))

        # lunar_python: 闰月 getMonth() 为负数
        lp_norm = (lp[0], abs(lp[1]), lp[2], lp[1] < 0)
        sx_norm = (sx[0], abs(sx[1]), sx[2], sx[3])

        if lp_norm != sx_norm:
            bad += 1
            print(f"[农历] {cur} lunar={lp_norm} sxtwl={sx_norm}")

        # 日柱：lunar_python vs sxtwl（engine 另有 1900-01-01 甲戌 锚定硬校验）
        ldz = lunar.getDayInGanZhi()
        sdz = f"{sxtwl_GAN[sd.getDayGZ().tg]}{sxtwl_ZHI[sd.getDayGZ().dz]}"
        if ldz != sdz:
            bad += 1
            print(f"[日柱] {cur} lunar={ldz} sxtwl={sdz}")

        # 节气：两库同一天只应有一个节气名且一致
        ljq = lunar.getJieQi() or ""
        sjq = JIEQI[sd.getJieQi()] if sd.hasJieQi() else ""
        if ljq != sjq:
            bad += 1
            print(f"[节气] {cur} lunar={ljq or '-'} sxtwl={sjq or '-'}")

        cur += timedelta(days=step_days)

    print(f"[crosscheck] 样本 {total} 天（{start_year}-01-01 .. {end_year}-12-31 步长 {step_days}），不一致 {bad}")
    return bad


sxtwl_GAN = "甲乙丙丁戊己庚辛壬癸"
sxtwl_ZHI = "子丑寅卯辰巳午未申酉戌亥"


if __name__ == "__main__":
    y1 = int(sys.argv[1]) if len(sys.argv) > 1 else 1900
    y2 = int(sys.argv[2]) if len(sys.argv) > 2 else 2030
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    raise SystemExit(1 if check(y1, y2, step) else 0)
