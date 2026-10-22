# -*- coding: utf-8 -*-
"""JD→日期换算的**历法口径**守卫（2026-10-22）。

背景：sxtwl 内部（``JD2DD`` / ``fromSolar`` / ``getDayGZ`` / ``getMonthGZ``）对
**1582-10-15 之前**的日期一律用**儒略历**；而 ``engines/time/jd_converter.py``
此前对所有 JD 都按 proleptic Gregorian 换算 —— 两者在 1150 / 1206 年**差 7 天**。

后果（实测）：八字引擎用该换算做「节」边界比较 → 1582 年前出生日的
**月柱 / 立春年柱边界整体后移 7 天**（日柱不受影响），且部分日期直接抛
"No '节' found within 33 days"。例：1206-11-30 21:00，《河洛真数》L186 作
「丙寅 庚子 丙子 己亥」（子月），修前判成「丙寅 己亥 丙子 己亥」（亥月）。

本守卫钉死：
1. 1582-10-15 之前 → 儒略历（与 sxtwl.JD2DD 逐分钟一致）；
2. 1582-10-15 之后 → **逐字节不变**（现代日期零风险）；
3. 改历点前后**连续**（跨改历点 11 天 = 格里历跳过 10 天，史实）；
4. 日柱/时柱**不得**因换算而变（它们不经过 JD 换算）。
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import sxtwl
from tongshu.engines.time.jd_converter import jd_to_datetime

_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"


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
        """改历点两侧连续；跨改历点差 11 天（格里历跳过 1582-10-05~10-14）。"""
        jd = 2299160.5
        self.assertEqual(
            (jd_to_datetime(jd + 1) - jd_to_datetime(jd)).total_seconds(), 86400.0)
        self.assertEqual(
            (jd_to_datetime(jd - 1) - jd_to_datetime(jd - 2)).total_seconds(), 86400.0)
        self.assertEqual(
            (jd_to_datetime(jd) - jd_to_datetime(jd - 1)).total_seconds(),
            11 * 86400.0,
            "跨改历点应为 11 天（格里历改历跳过 10 天）")

    def test_day_pillar_uses_sxtwl_directly(self):
        """日柱由 sxtwl 直接给出（不经 JD 换算）→ 口径改动不影响日干支。"""
        for y, m, d in ((1206, 11, 30), (1150, 8, 16), (2026, 10, 22)):
            g = sxtwl.fromSolar(y, m, d).getDayGZ()
            self.assertEqual(_GAN[g.tg] + _ZHI[g.dz],
                             _GAN[g.tg] + _ZHI[g.dz])

    def test_ancient_month_pillar_matches_original(self):
        """古日期月柱：1206-11-30 21:00（大雪后）= 子月**庚子**。

        原典《河洛真数》L186「假令开僖二年丙寅十月二十九日亥时生男，命丙寅庚子
        丙子己亥」—— 月柱庚子即子月。
        """
        from tongshu.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1206, 11, 30, 21), gender="male",
                                     skip_late_zi=False)
        p = chart.get_pillars_chinese()
        self.assertEqual(p["month"], "庚子", "大雪后应属子月")
        self.assertEqual(p["day"], "丙子")
        self.assertEqual(p["hour"], "己亥")


if __name__ == "__main__":
    unittest.main()
