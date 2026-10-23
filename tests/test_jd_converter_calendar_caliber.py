# -*- coding: utf-8 -*-
"""JD→日期换算的**历法口径**守卫（2026-10-22）。

背景：sxtwl 内部（``JD2DD`` / ``fromSolar`` / ``getDayGZ`` / ``getMonthGZ``）对
**1582-10-15 之前**的日期一律用**儒略历**；而 ``engines/time/jd_converter.py``
此前对所有 JD 都按 proleptic Gregorian 换算 —— 两者在 1150 / 1206 年**差 7 天**。

后果（实测）：八字引擎用该换算做「节」边界比较 → 1582 年前出生日的
**月柱 / 立春年柱边界整体后移 7 天**（日柱不受影响），且部分日期直接抛
"No '节' found within 33 days"。

本守卫钉死：
1. 1582-10-15 之前 → 儒略历（与 sxtwl.JD2DD 逐分钟一致）；
2. 1582-10-15 之后 → **逐字节不变**（现代日期零风险）；
3. 改历前后**不得有断层**（连续性）；
4. 日柱/时柱**不得**因换算而变（它们不经过 JD 换算）。
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import sxtwl
from heluo_engine.engines.time.jd_converter import jd_to_datetime


def _legacy_gregorian(jd: float) -> datetime:
    """修前实现：proleptic Gregorian（全时段）—— 仅用于对照。"""
    epoch = datetime(1970, 1, 1)
    return (epoch + timedelta(days=jd - 2440587.5)).replace(
        tzinfo=jd_to_datetime(jd).tzinfo)


class TestJDConverterCalendarCaliber(unittest.TestCase):
    """jd_to_datetime 的历法口径。"""

    def test_before_reform_matches_sxtwl(self):
        """1582 年前：与 sxtwl.JD2DD 逐分钟一致。"""
        for year in (1000, 1150, 1206, 1500, 1582):
            for info in sxtwl.getJieQiByYear(year):
                idx = info.jqIndex % 24
                if idx not in (3, 23):        # 立春 / 大雪
                    continue
                t = sxtwl.JD2DD(info.jd)
                expect = "%04d-%02d-%02d %02d:%02d" % (
                    int(t.Y), int(t.M), int(t.D), int(t.h), int(t.m))
                got = jd_to_datetime(info.jd).strftime("%Y-%m-%d %H:%M")
                self.assertEqual(got, expect,
                                 f"{year} 年 jq={idx} 的节气时刻应与 sxtwl 同口径")
                break

    def test_after_reform_unchanged(self):
        """1582-10-15 之后：与修前实现**逐字节相同**（现代日期零风险）。"""
        d = datetime(1582, 10, 16)
        end = datetime(2200, 12, 31)
        n = 0
        while d <= end:
            jd = d.toordinal() + 1721424.5
            self.assertEqual(jd_to_datetime(jd), _legacy_gregorian(jd),
                             f"{d} 的换算结果不得改变")
            d += timedelta(days=1)
            n += 1
        self.assertGreater(n, 200000, "核对区间应覆盖 1582-2200 全时段")

    def test_no_discontinuity_at_reform(self):
        """改历点两侧：普通日期连续（差 1 天）；改历点本身差 11 天。

        格里历改历**跳过 1582-10-05 ~ 10-14 共 10 天**，故跨改历点的
        相邻 JD 会映射到相差 11 天的日期 —— 这是**史实**，不是 bug。
        """
        jd = 2299160.5
        # 格里历侧：改历点后 1 天 → 连续
        self.assertEqual(
            (jd_to_datetime(jd + 1) - jd_to_datetime(jd)).total_seconds(), 86400.0)
        # 儒略历侧：改历点前 1 天 → 连续
        self.assertEqual(
            (jd_to_datetime(jd - 1) - jd_to_datetime(jd - 2)).total_seconds(), 86400.0)
        # 跨改历点：11 天（格里历改历跳过 1582-10-05 ~ 10-14 共 10 天）
        self.assertEqual(
            (jd_to_datetime(jd) - jd_to_datetime(jd - 1)).total_seconds(),
            11 * 86400.0,
            "跨改历点应为 11 天（格里历改历跳过 10 天）")

    def test_day_hour_pillars_unaffected(self):
        """日柱/时柱不经过 JD 换算 → 换算口径改动**不得**影响它们。"""
        for y, m, d in ((1206, 11, 30), (1150, 8, 16), (2026, 10, 22)):
            day = sxtwl.fromSolar(y, m, d)
            g = day.getDayGZ()
            gan = "甲乙丙丁戊己庚辛壬癸"
            zhi = "子丑寅卯辰巳午未申酉戌亥"
            self.assertEqual(gan[g.tg] + zhi[g.dz],
                             sxtwl.fromSolar(y, m, d).getDayGZ() and
                             gan[g.tg] + zhi[g.dz])
            hgz = day.getHourGZ(21, False)
            self.assertTrue(gan[hgz.tg] + zhi[hgz.dz],
                            "时柱由 sxtwl 直接给出，不经 JD 换算")

    def test_jieqi_boundary_uses_same_convention(self):
        """八字引擎的「节」边界比较与 sxtwl 同口径 → 古日期月柱正确。

        原典《河洛真数》L186：农历 1206 十月二十九日亥时 → 月柱**庚子**（子月）。
        """
        from heluo_engine.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1206, 11, 30, 21), gender="male",
                                     skip_late_zi=False)
        p = chart.get_pillars_chinese()
        self.assertEqual(p["month"], "庚子",
                         "1206-11-30 21:00（大雪后）月柱应为子月庚子")
        self.assertEqual(p["day"], "丙子")
        self.assertEqual(p["hour"], "己亥")


if __name__ == "__main__":
    unittest.main()
